from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.llm_output import LLMInterpretation
from solgreen.diagnostics.llm_provider import (
    DeepSeekProvider,
    FallbackProvider,
    LLMProvider,
    MiniMaxProvider,
    _parse_response,
    interpret_episode,
)
from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline.episode import CanonicalEpisode


class MockProvider(LLMProvider):
    def __init__(self, response: str = "") -> None:
        self._response = response
        self.last_prompt: str | None = None
        self.last_max_tokens: int | None = None

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
        self.last_prompt = prompt
        self.last_max_tokens = max_tokens
        return self._response


def _make_episode() -> CanonicalEpisode:
    return CanonicalEpisode(
        episode_type="pv_production",
        start=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        end=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        duration=timedelta(hours=1),
        sample_count=12,
        coverage_pct=95.0,
        source_summary="merged",
        signals={"flow_soc_pct": 75.0, "telemetry_pv_power_w": 3500.0},
    )


def _make_fired_execution() -> RuleExecution:
    return RuleExecution(
        rule_id="BAT-001",
        rule_version="1.0.0",
        period_start=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        period_end=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        parameters_used={"soc_threshold_pct": 20},
        fired=True,
        evidence=("All required signals present: flow_soc_pct",),
        input_checksum="abc123",
    )


def _make_input_data() -> LLMEpisodeInput:
    return LLMEpisodeInput(
        plant_id="casabero",
        episode=_make_episode(),
        fired_rules=(_make_fired_execution(),),
        data_quality_summary="Good quality data.",
    )


VALID_RESPONSE = json.dumps({
    "summary": "The inverter showed low SOC during the episode.",
    "hypotheses": [
        {
            "description": "Battery was depleted due to high consumption.",
            "support_level": "moderate",
            "evidence_refs": [0],
        }
    ],
    "alternatives": ["Grid outage caused battery drain."],
    "missing_info": ["Historical SOC trend."],
    "suggested_actions": ["Check battery health."],
    "warnings": [],
})


def test_provider_abc_cannot_instantiate() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_mock_provider_returns_response() -> None:
    provider = MockProvider(response="hello")
    result = provider.complete("test prompt")
    assert result == "hello"
    assert provider.last_prompt == "test prompt"


def test_deepseek_provider_properties() -> None:
    provider = DeepSeekProvider(api_key="test-key", model="custom-model")
    assert provider.provider_name == "deepseek"
    assert provider.default_model == "deepseek-chat"


def test_interpret_episode_returns_interpretation() -> None:
    provider = MockProvider(response=VALID_RESPONSE)
    input_data = _make_input_data()
    result = interpret_episode(provider, input_data)
    assert isinstance(result, LLMInterpretation)
    assert result.summary == "The inverter showed low SOC during the episode."
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].support_level == "moderate"
    assert result.provider == "mock"
    assert result.model == "mock-model"


def test_interpret_episode_passes_max_tokens() -> None:
    provider = MockProvider(response=VALID_RESPONSE)
    input_data = _make_input_data()
    input_data = input_data.model_copy(update={"max_tokens": 500})
    interpret_episode(provider, input_data)
    assert provider.last_max_tokens == 500


def test_interpret_episode_fails_validation() -> None:
    bad_response = json.dumps({
        "summary": "",
        "hypotheses": [],
        "alternatives": [],
        "missing_info": [],
        "suggested_actions": [],
        "warnings": [],
    })
    provider = MockProvider(response=bad_response)
    input_data = _make_input_data()
    with pytest.raises(ValueError, match="validation failed"):
        interpret_episode(provider, input_data)


def test_parse_response_strips_markdown_fences() -> None:
    fenced = "```json\n" + VALID_RESPONSE + "\n```"
    result = _parse_response(fenced, MockProvider(), "1.0.0", "hash123")
    assert isinstance(result, LLMInterpretation)
    assert result.summary == "The inverter showed low SOC during the episode."


def test_parse_response_handles_plain_json() -> None:
    result = _parse_response(VALID_RESPONSE, MockProvider(), "1.0.0", "hash123")
    assert isinstance(result, LLMInterpretation)
    assert result.prompt_version == "1.0.0"
    assert result.input_hash == "hash123"


def test_parse_response_invalid_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        _parse_response("not json at all", MockProvider(), "1.0.0", "hash")


def test_interpret_episode_llm_error_propagates() -> None:
    class FailingProvider(MockProvider):
        def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
            raise RuntimeError("API timeout")

    provider = FailingProvider()
    input_data = _make_input_data()
    with pytest.raises(RuntimeError, match="API timeout"):
        interpret_episode(provider, input_data)


def test_minimax_provider_properties() -> None:
    provider = MiniMaxProvider(api_key="test-key", model="custom-model")
    assert provider.provider_name == "minimax"
    assert provider.default_model == "MiniMax-Text-01"


def test_fallback_uses_primary_when_successful() -> None:
    primary = MockProvider(response=VALID_RESPONSE)
    fallback = MockProvider(response="should not be used")
    fb = FallbackProvider(primary=primary, fallback=fallback)
    result = fb.complete("prompt")
    assert fb.provider_name == "mock"
    assert fb.used_fallback is False
    input_data = _make_input_data()
    result = interpret_episode(fb, input_data)
    assert result.provider == "mock"


def test_fallback_uses_fallback_when_primary_fails() -> None:
    class FailingPrimary(MockProvider):
        def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
            raise RuntimeError("primary timeout")

    primary = FailingPrimary(response="fail")
    fallback = MockProvider(response=VALID_RESPONSE)
    fb = FallbackProvider(primary=primary, fallback=fallback)
    result = fb.complete("prompt")
    assert result == VALID_RESPONSE
    assert fb.used_fallback is True
    assert fb.provider_name == "mock"


def test_fallback_propagates_fallback_failure() -> None:
    class AlwaysFails(MockProvider):
        def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
            raise RuntimeError("api error")

    primary = AlwaysFails()
    fallback = AlwaysFails()
    fb = FallbackProvider(primary=primary, fallback=fallback)
    with pytest.raises(RuntimeError, match="api error"):
        fb.complete("prompt")
    assert fb.used_fallback is True
