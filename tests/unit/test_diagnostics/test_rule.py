from datetime import UTC, datetime

from solgreen.diagnostics.rule import Rule, RuleExecution


class TestRule:
    def test_minimal_rule(self) -> None:
        rule = Rule(
            rule_id="TEST-001",
            name="Test rule",
            category="data",
            question="Is it working?",
            signals_required=("timestamp_axis",),
            base_severity="low",
        )
        assert rule.rule_id == "TEST-001"
        assert rule.version == "1.0.0"
        assert rule.parameters == {}
        assert rule.known_false_positives == ()
        assert rule.signals_optional == ()

    def test_full_rule(self) -> None:
        rule = Rule(
            rule_id="BAT-001",
            version="2.0.0",
            name="SOC bajo",
            category="battery",
            question="¿SOC bajo?",
            signals_required=("flow_soc_pct",),
            signals_optional=("telemetry_soc_pct",),
            base_severity="medium",
            parameters={"threshold": 20},
            known_false_positives=("Maintenance mode.",),
        )
        assert rule.version == "2.0.0"
        assert rule.parameters == {"threshold": 20}
        assert rule.known_false_positives == ("Maintenance mode.",)


class TestRuleExecution:
    def test_creation(self) -> None:
        ts = datetime(2026, 7, 17, tzinfo=UTC)
        exec_ = RuleExecution(
            rule_id="DATA-001",
            rule_version="1.0.0",
            period_start=ts,
            period_end=ts,
            parameters_used={"max_gap_minutes": 30},
            fired=True,
            evidence=("Gap of 45 minutes detected.",),
            input_checksum="abc123",
        )
        assert exec_.fired is True
        assert len(exec_.evidence) == 1

    def test_not_fired(self) -> None:
        ts = datetime(2026, 7, 17, tzinfo=UTC)
        exec_ = RuleExecution(
            rule_id="DATA-001",
            rule_version="1.0.0",
            period_start=ts,
            period_end=ts,
            parameters_used={},
            fired=False,
            input_checksum="def456",
        )
        assert exec_.fired is False
        assert exec_.evidence == ()
