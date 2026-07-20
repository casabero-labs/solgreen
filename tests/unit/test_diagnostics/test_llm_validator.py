from datetime import UTC, datetime, timedelta

from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.llm_output import Hypothesis, LLMInterpretation
from solgreen.diagnostics.llm_validator import validate_interpretation
from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline import CanonicalEpisode

TS0 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _episode() -> CanonicalEpisode:
    return CanonicalEpisode(
        episode_type="pv_production",
        start=TS0,
        end=TS0 + timedelta(minutes=30),
        duration=timedelta(minutes=30),
        sample_count=7,
        coverage_pct=100.0,
        source_summary="merged",
    )


def _input_with_one_fired() -> LLMEpisodeInput:
    return LLMEpisodeInput(
        plant_id="casabero",
        episode=_episode(),
        fired_rules=(
            RuleExecution(
                rule_id="PV-001",
                rule_version="1.0.0",
                period_start=TS0,
                period_end=TS0 + timedelta(minutes=30),
                parameters_used={},
                fired=True,
                evidence=("PV power dropped.",),
                input_checksum="abc",
            ),
        ),
    )


def _valid_interp() -> LLMInterpretation:
    return LLMInterpretation(
        summary="PV dropout detected.",
        hypotheses=(
            Hypothesis(description="MPPT fault", support_level="moderate", evidence_refs=(0,)),
        ),
        provider="openai",
        model="gpt-4",
        prompt_version="1.0.0",
        input_hash="abc123",
    )


class TestValidateInterpretation:
    def test_valid_returns_empty(self) -> None:
        errors = validate_interpretation(_valid_interp(), _input_with_one_fired())
        assert errors == []

    def test_empty_summary_fails(self) -> None:
        interp = _valid_interp().model_copy(update={"summary": "  "})
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert any("summary" in e for e in errors)

    def test_invalid_evidence_ref_fails(self) -> None:
        interp = _valid_interp().model_copy(
            update={"hypotheses": (Hypothesis(description="x", support_level="weak", evidence_refs=(99,)),)}
        )
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert any("evidence_refs" in e for e in errors)

    def test_valid_evidence_ref_passes(self) -> None:
        interp = _valid_interp().model_copy(
            update={"hypotheses": (Hypothesis(description="x", support_level="weak", evidence_refs=(0,)),)}
        )
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert errors == []

    def test_empty_provider_fails(self) -> None:
        interp = _valid_interp().model_copy(update={"provider": ""})
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert any("provider" in e for e in errors)

    def test_empty_model_fails(self) -> None:
        interp = _valid_interp().model_copy(update={"model": ""})
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert any("model" in e for e in errors)

    def test_empty_input_hash_fails(self) -> None:
        interp = _valid_interp().model_copy(update={"input_hash": ""})
        errors = validate_interpretation(interp, _input_with_one_fired())
        assert any("input_hash" in e for e in errors)
