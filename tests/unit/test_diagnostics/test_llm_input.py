from datetime import UTC, datetime, timedelta

from solgreen.diagnostics.llm_input import LLMEpisodeInput
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


def _fired_rule_execution() -> RuleExecution:
    return RuleExecution(
        rule_id="PV-001",
        rule_version="1.0.0",
        period_start=TS0,
        period_end=TS0 + timedelta(minutes=30),
        parameters_used={"min_voltage_v": 100},
        fired=True,
        evidence=("PV power dropped to 0W while voltage remained at 320V.",),
        input_checksum="abc123",
    )


class TestLLMEpisodeInput:
    def test_creation(self) -> None:
        inp = LLMEpisodeInput(
            plant_id="casabero",
            episode=_episode(),
            fired_rules=(_fired_rule_execution(),),
            data_quality_summary="All rows valid.",
        )
        assert inp.plant_id == "casabero"
        assert inp.episode.episode_type == "pv_production"
        assert len(inp.fired_rules) == 1
        assert inp.max_tokens == 2000

    def test_defaults(self) -> None:
        inp = LLMEpisodeInput(plant_id="test", episode=_episode())
        assert inp.fired_rules == ()
        assert inp.manual_excerpts == ()
        assert inp.data_quality_summary == ""
