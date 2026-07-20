from datetime import UTC, datetime, timedelta

from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.prompt_builder import build_prompt
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
        signals={"flow_potencia_produccion_w": 5000.0},
    )


def _fired() -> RuleExecution:
    return RuleExecution(
        rule_id="PV-001",
        rule_version="1.0.0",
        period_start=TS0,
        period_end=TS0 + timedelta(minutes=30),
        parameters_used={},
        fired=True,
        evidence=("PV power dropped.",),
        input_checksum="abc",
    )


class TestBuildPrompt:
    def test_contains_plant_id(self) -> None:
        inp = LLMEpisodeInput(plant_id="casabero", episode=_episode())
        prompt = build_prompt(inp)
        assert "casabero" in prompt

    def test_contains_episode_type(self) -> None:
        inp = LLMEpisodeInput(plant_id="x", episode=_episode())
        prompt = build_prompt(inp)
        assert "pv_production" in prompt

    def test_contains_signals(self) -> None:
        inp = LLMEpisodeInput(plant_id="x", episode=_episode())
        prompt = build_prompt(inp)
        assert "flow_potencia_produccion_w" in prompt
        assert "5000.0" in prompt

    def test_contains_fired_rules(self) -> None:
        inp = LLMEpisodeInput(
            plant_id="x",
            episode=_episode(),
            fired_rules=(_fired(),),
        )
        prompt = build_prompt(inp)
        assert "PV-001" in prompt
        assert "E1:" in prompt

    def test_contains_instructions(self) -> None:
        inp = LLMEpisodeInput(plant_id="x", episode=_episode())
        prompt = build_prompt(inp)
        assert "NEVER declare a cause as 'confirmed'" in prompt
        assert "evidence_refs" in prompt
        assert "Max tokens" in prompt

    def test_contains_manual_excerpts(self) -> None:
        inp = LLMEpisodeInput(
            plant_id="x",
            episode=_episode(),
            manual_excerpts=("Manual p.42: max PV voltage 600V.",),
        )
        prompt = build_prompt(inp)
        assert "Manual p.42" in prompt

    def test_contains_data_quality(self) -> None:
        inp = LLMEpisodeInput(
            plant_id="x",
            episode=_episode(),
            data_quality_summary="98% coverage, 2 gaps.",
        )
        prompt = build_prompt(inp)
        assert "98% coverage" in prompt
