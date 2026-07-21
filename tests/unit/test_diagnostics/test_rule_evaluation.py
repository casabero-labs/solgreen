from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from solgreen.diagnostics.rule import Rule, RuleExecution, RuleImplementationStatus
from solgreen.diagnostics.rule_catalog import SEED_RULES, RuleCatalog
from solgreen.diagnostics.rule_evaluation import (
    RuleEvaluationOutcome,
    RuleEvaluationReason,
    RuleEvaluationStatus,
    RuleEvaluatorRegistry,
    _episode_checksum,
    eligible_fired_rules,
    evaluate_rule_catalog,
)
from solgreen.timeline.episode import CanonicalEpisode

TS0 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _episode(
    signals: dict[str, float] | None = None,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> CanonicalEpisode:
    if start is None:
        start = TS0
    if end is None:
        end = start + timedelta(minutes=30)
    return CanonicalEpisode(
        episode_type="pv_production",
        start=start,
        end=end,
        duration=end - start,
        sample_count=12,
        coverage_pct=95.0,
        source_summary="merged",
        signals=signals
        if signals is not None
        else {"flow_soc_pct": 75.0, "telemetry_pv_power_w": 3500.0},
    )


# ---------------------------------------------------------------------------
# Contract tests for Rule / RuleEvaluationOutcome
# ---------------------------------------------------------------------------


class TestRuleImplementationStatus:
    def test_default_status_is_planned(self) -> None:
        rule = Rule(
            rule_id="X-001",
            name="X",
            category="data",
            question="?",
            signals_required=("timestamp_axis",),
            base_severity="low",
            parameters={},
        )
        assert rule.implementation_status == RuleImplementationStatus.PLANNED

    def test_all_seed_rules_are_planned(self) -> None:
        for rule in SEED_RULES:
            assert rule.implementation_status == RuleImplementationStatus.PLANNED, (
                f"{rule.rule_id} should be planned, got {rule.implementation_status}"
            )

    def test_seed_rule_ids_unchanged(self) -> None:
        ids = {r.rule_id for r in SEED_RULES}
        assert ids == {"DATA-001", "BAT-001", "PV-001", "GRID-003", "INV-002"}


class TestRuleEvaluationOutcomeInvariants:
    def test_not_evaluable_with_execution_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.NOT_EVALUABLE,
                reason=RuleEvaluationReason.RULE_NOT_IMPLEMENTED,
                execution=RuleExecution(
                    rule_id="X",
                    rule_version="1.0.0",
                    period_start=TS0,
                    period_end=TS0 + timedelta(minutes=30),
                    parameters_used={},
                    fired=False,
                    evidence=(),
                    input_checksum="abc",
                ),
            )

    def test_not_evaluable_without_reason_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.NOT_EVALUABLE,
                reason=None,
            )

    def test_evaluated_not_fired_without_execution_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.EVALUATED_NOT_FIRED,
                reason=None,
                execution=None,
            )

    def test_evaluated_not_fired_with_fired_true_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.EVALUATED_NOT_FIRED,
                reason=None,
                execution=RuleExecution(
                    rule_id="X",
                    rule_version="1.0.0",
                    period_start=TS0,
                    period_end=TS0 + timedelta(minutes=30),
                    parameters_used={},
                    fired=True,
                    evidence=("ok",),
                    input_checksum="abc",
                ),
            )

    def test_fired_without_execution_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.FIRED,
                reason=None,
                execution=None,
            )

    def test_fired_with_fired_false_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.FIRED,
                reason=None,
                execution=RuleExecution(
                    rule_id="X",
                    rule_version="1.0.0",
                    period_start=TS0,
                    period_end=TS0 + timedelta(minutes=30),
                    parameters_used={},
                    fired=False,
                    evidence=("no fire",),
                    input_checksum="abc",
                ),
            )

    def test_fired_without_evidence_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            RuleEvaluationOutcome(
                rule_id="X",
                rule_version="1.0.0",
                status=RuleEvaluationStatus.FIRED,
                reason=None,
                execution=RuleExecution(
                    rule_id="X",
                    rule_version="1.0.0",
                    period_start=TS0,
                    period_end=TS0 + timedelta(minutes=30),
                    parameters_used={},
                    fired=True,
                    evidence=(),
                    input_checksum="abc",
                ),
            )

    def test_serialization_model_dump(self) -> None:
        outcome = RuleEvaluationOutcome(
            rule_id="X",
            rule_version="1.0.0",
            status=RuleEvaluationStatus.NOT_EVALUABLE,
            reason=RuleEvaluationReason.RULE_NOT_IMPLEMENTED,
        )
        dumped = outcome.model_dump()
        assert dumped["rule_id"] == "X"
        assert dumped["status"] == "not_evaluable"
        assert dumped["reason"] == "rule_not_implemented"

    def test_serialization_model_dump_json(self) -> None:
        outcome = RuleEvaluationOutcome(
            rule_id="X",
            rule_version="1.0.0",
            status=RuleEvaluationStatus.NOT_EVALUABLE,
            reason=RuleEvaluationReason.RULE_NOT_IMPLEMENTED,
        )
        assert "not_evaluable" in outcome.model_dump_json()

    def test_outcomes_are_frozen(self) -> None:
        outcome = RuleEvaluationOutcome(
            rule_id="X",
            rule_version="1.0.0",
            status=RuleEvaluationStatus.NOT_EVALUABLE,
            reason=RuleEvaluationReason.RULE_NOT_IMPLEMENTED,
        )
        with pytest.raises(ValidationError, match="frozen"):
            outcome.rule_id = "Y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Seed catalog behaviour
# ---------------------------------------------------------------------------


class TestSeedCatalogNotFirable:
    def test_signals_present_do_not_fire_bat(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({"flow_soc_pct": 75.0, "telemetry_pv_power_w": 3500.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        by_id = {o.rule_id: o for o in outcomes}
        assert by_id["BAT-001"].status == RuleEvaluationStatus.NOT_EVALUABLE

    def test_signals_present_do_not_fire_pv(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({"flow_soc_pct": 75.0, "telemetry_pv_power_w": 3500.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        by_id = {o.rule_id: o for o in outcomes}
        assert by_id["PV-001"].status == RuleEvaluationStatus.NOT_EVALUABLE

    def test_signals_present_do_not_fire_grid(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({"telemetry_grid_power_w": 1000.0, "flow_soc_pct": 75.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        by_id = {o.rule_id: o for o in outcomes}
        assert by_id["GRID-003"].status == RuleEvaluationStatus.NOT_EVALUABLE

    def test_waiting_present_does_not_fire_inv(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({"telemetry_inverter_state": 1000.0, "flow_soc_pct": 75.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        by_id = {o.rule_id: o for o in outcomes}
        assert by_id["INV-002"].status == RuleEvaluationStatus.NOT_EVALUABLE

    def test_timestamp_present_does_not_fire_data(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({"timestamp_axis": 1.0, "flow_soc_pct": 75.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        by_id = {o.rule_id: o for o in outcomes}
        assert by_id["DATA-001"].status == RuleEvaluationStatus.NOT_EVALUABLE

    def test_seed_catalog_produces_five_not_evaluable(self) -> None:
        catalog = RuleCatalog()
        episode = _episode(
            {
                "timestamp_axis": 1.0,
                "flow_soc_pct": 75.0,
                "telemetry_pv_power_w": 3500.0,
                "telemetry_grid_power_w": 1000.0,
                "telemetry_inverter_state": 1000.0,
            }
        )
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        assert len(outcomes) == 5
        assert all(o.status == RuleEvaluationStatus.NOT_EVALUABLE for o in outcomes)

    def test_seed_catalog_reasons_are_rule_not_implemented(self) -> None:
        catalog = RuleCatalog()
        episode = _episode({})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        assert all(o.reason == RuleEvaluationReason.RULE_NOT_IMPLEMENTED for o in outcomes)

    def test_seed_catalog_produces_no_execution(self) -> None:
        catalog = RuleCatalog()
        episode = _episode(
            {
                "timestamp_axis": 1.0,
                "flow_soc_pct": 75.0,
                "telemetry_pv_power_w": 3500.0,
                "telemetry_grid_power_w": 1000.0,
                "telemetry_inverter_state": 1000.0,
            }
        )
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        assert all(o.execution is None for o in outcomes)

    def test_repeated_evaluation_is_deterministic(self) -> None:
        catalog = RuleCatalog()
        episode = _episode(
            {
                "timestamp_axis": 1.0,
                "flow_soc_pct": 75.0,
                "telemetry_pv_power_w": 3500.0,
                "telemetry_grid_power_w": 1000.0,
                "telemetry_inverter_state": 1000.0,
            }
        )
        first = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        second = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        assert first == second


# ---------------------------------------------------------------------------
# Synthetic evaluator contract (tests only — never registered in production)
# ---------------------------------------------------------------------------


class _SyntheticEvaluator:
    def __init__(
        self,
        rule_id: str,
        rule_version: str,
        *,
        fired: bool,
        evidence: tuple[str, ...] = (),
        wrong_id: str | None = None,
        wrong_version: str | None = None,
        wrong_period: bool = False,
    ) -> None:
        self.rule_id = rule_id
        self.rule_version = rule_version
        self._fired = fired
        self._evidence = evidence
        self._wrong_id = wrong_id
        self._wrong_version = wrong_version
        self._wrong_period = wrong_period

    def evaluate(self, rule: Rule, episode: CanonicalEpisode) -> RuleExecution:
        return RuleExecution(
            rule_id=self._wrong_id or rule.rule_id,
            rule_version=self._wrong_version or rule.version,
            period_start=(
                episode.start + timedelta(minutes=1) if self._wrong_period else episode.start
            ),
            period_end=(episode.end - timedelta(minutes=1) if self._wrong_period else episode.end),
            parameters_used=rule.parameters,
            fired=self._fired,
            evidence=self._evidence,
            input_checksum=_episode_checksum(episode),
        )


def _implemented_rule(
    rule_id: str = "X-001",
    signals: tuple[str, ...] = ("timestamp_axis",),
    parameters: dict[str, Any] | None = None,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        name="X",
        category="data",
        question="?",
        signals_required=signals,
        base_severity="low",
        parameters=parameters if parameters is not None else {},
        implementation_status=RuleImplementationStatus.IMPLEMENTED,
    )


class TestSyntheticEvaluatorContract:
    def test_implemented_without_signals(self) -> None:
        rule = _implemented_rule()
        catalog = RuleCatalog([rule])
        episode = _episode({})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        outcome = outcomes[0]
        assert outcome.status == RuleEvaluationStatus.NOT_EVALUABLE
        assert outcome.reason == RuleEvaluationReason.MISSING_REQUIRED_SIGNALS
        assert outcome.missing_signals == ("timestamp_axis",)
        assert outcome.execution is None

    def test_implemented_without_evaluator(self) -> None:
        rule = _implemented_rule()
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        outcomes = evaluate_rule_catalog(catalog, episode, RuleEvaluatorRegistry())
        outcome = outcomes[0]
        assert outcome.status == RuleEvaluationStatus.NOT_EVALUABLE
        assert outcome.reason == RuleEvaluationReason.EVALUATOR_NOT_REGISTERED

    def test_evaluator_fired_false_yields_evaluated_not_fired(self) -> None:
        rule = _implemented_rule()
        registry = RuleEvaluatorRegistry()
        registry.register(
            _SyntheticEvaluator(
                "X-001",
                "1.0.0",
                fired=False,
                evidence=("conditions not met",),
            )
        )
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        outcomes = evaluate_rule_catalog(catalog, episode, registry)
        outcome = outcomes[0]
        assert outcome.status == RuleEvaluationStatus.EVALUATED_NOT_FIRED
        assert outcome.execution is not None
        assert outcome.execution.fired is False

    def test_evaluator_fired_true_with_evidence_yields_fired(self) -> None:
        rule = _implemented_rule()
        registry = RuleEvaluatorRegistry()
        registry.register(
            _SyntheticEvaluator(
                "X-001",
                "1.0.0",
                fired=True,
                evidence=("specific threshold exceeded",),
            )
        )
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        outcomes = evaluate_rule_catalog(catalog, episode, registry)
        outcome = outcomes[0]
        assert outcome.status == RuleEvaluationStatus.FIRED
        assert outcome.execution is not None
        assert outcome.execution.fired is True
        assert outcome.execution.evidence

    def test_evaluator_with_wrong_rule_id_rejected(self) -> None:
        rule = _implemented_rule()
        registry = RuleEvaluatorRegistry()
        registry.register(
            _SyntheticEvaluator("X-001", "1.0.0", fired=True, evidence=("x",), wrong_id="OTHER")
        )
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        with pytest.raises(ValueError, match="rule_id"):
            evaluate_rule_catalog(catalog, episode, registry)

    def test_evaluator_with_wrong_rule_version_rejected(self) -> None:
        rule = _implemented_rule()
        registry = RuleEvaluatorRegistry()
        registry.register(
            _SyntheticEvaluator(
                "X-001", "1.0.0", fired=True, evidence=("x",), wrong_version="9.9.9"
            )
        )
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        with pytest.raises(ValueError, match="rule_version"):
            evaluate_rule_catalog(catalog, episode, registry)

    def test_registry_rejects_duplicate_evaluator(self) -> None:
        registry = RuleEvaluatorRegistry()
        registry.register(_SyntheticEvaluator("X-001", "1.0.0", fired=True, evidence=("x",)))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(_SyntheticEvaluator("X-001", "1.0.0", fired=False, evidence=("y",)))

    def test_synthetic_evaluator_deterministic(self) -> None:
        registry = RuleEvaluatorRegistry()
        registry.register(_SyntheticEvaluator("X-001", "1.0.0", fired=True, evidence=("same",)))
        rule = _implemented_rule()
        catalog = RuleCatalog([rule])
        episode = _episode({"timestamp_axis": 1.0})
        first = evaluate_rule_catalog(catalog, episode, registry)
        second = evaluate_rule_catalog(catalog, episode, registry)
        assert first == second
        assert first[0].execution is not None
        assert first[0].execution.input_checksum == second[0].execution.input_checksum  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# eligible_fired_rules
# ---------------------------------------------------------------------------


class TestEligibleFiredRules:
    def test_fired_false_excluded(self) -> None:
        execution = RuleExecution(
            rule_id="X",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=False,
            evidence=("ignored",),
            input_checksum="abc",
        )
        assert eligible_fired_rules((execution,)) == ()

    def test_fired_true_empty_evidence_excluded(self) -> None:
        execution = RuleExecution(
            rule_id="X",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=True,
            evidence=(),
            input_checksum="abc",
        )
        assert eligible_fired_rules((execution,)) == ()

    def test_fired_true_with_evidence_included(self) -> None:
        execution = RuleExecution(
            rule_id="X",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=True,
            evidence=("real evidence",),
            input_checksum="abc",
        )
        assert eligible_fired_rules((execution,)) == (execution,)

    def test_mixed_executions_filters_correctly(self) -> None:
        good = RuleExecution(
            rule_id="X",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=True,
            evidence=("real",),
            input_checksum="abc",
        )
        no_evidence = RuleExecution(
            rule_id="Y",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=True,
            evidence=(),
            input_checksum="abc",
        )
        not_fired = RuleExecution(
            rule_id="Z",
            rule_version="1.0.0",
            period_start=TS0,
            period_end=TS0 + timedelta(minutes=30),
            parameters_used={},
            fired=False,
            evidence=("ignored",),
            input_checksum="abc",
        )
        eligible = eligible_fired_rules((good, no_evidence, not_fired))
        assert eligible == (good,)
