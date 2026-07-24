from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Protocol

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.diagnostics.rule import Rule, RuleExecution
from solgreen.diagnostics.rule_catalog import RuleCatalog
from solgreen.timeline.episode import CanonicalEpisode


class RuleEvaluationStatus(StrEnum):
    NOT_EVALUABLE = "not_evaluable"
    EVALUATED_NOT_FIRED = "evaluated_not_fired"
    FIRED = "fired"


class RuleEvaluationReason(StrEnum):
    RULE_NOT_IMPLEMENTED = "rule_not_implemented"
    MISSING_REQUIRED_SIGNALS = "missing_required_signals"
    EVALUATOR_NOT_REGISTERED = "evaluator_not_registered"


class RuleEvaluationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    rule_version: str
    status: RuleEvaluationStatus
    reason: RuleEvaluationReason | None
    missing_signals: tuple[str, ...] = Field(
        default=(),
        description=(
            "Señales requeridas ausentes (solo poblado cuando reason == MISSING_REQUIRED_SIGNALS)."
        ),
    )
    execution: RuleExecution | None = Field(
        default=None,
        description=(
            "Ejecucion real producida por un evaluador registrado. None para estados not_evaluable."
        ),
    )

    @pydantic.model_validator(mode="after")
    def _check_invariants(self) -> RuleEvaluationOutcome:
        if self.status == RuleEvaluationStatus.NOT_EVALUABLE:
            if self.execution is not None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "not_evaluable outcomes must not carry an execution."
                )
            if self.reason is None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "not_evaluable outcomes must declare a reason."
                )
        elif self.status == RuleEvaluationStatus.EVALUATED_NOT_FIRED:
            if self.execution is None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "evaluated_not_fired must carry an execution."
                )
            if self.execution.fired:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "evaluated_not_fired must have fired=False."
                )
            if self.reason is not None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "evaluated_not_fired must not carry a reason."
                )
        else:
            if self.execution is None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "fired outcomes must carry an execution."
                )
            if not self.execution.fired:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "fired outcomes must have fired=True."
                )
            if not self.execution.evidence:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "fired outcomes must carry non-empty evidence."
                )
            if self.reason is not None:
                raise ValueError(
                    f"RuleEvaluationOutcome invariant violated for {self.rule_id}: "
                    "fired outcomes must not carry a reason."
                )
        return self


class RuleEvaluator(Protocol):
    rule_id: str
    rule_version: str

    def evaluate(self, rule: Rule, episode: CanonicalEpisode) -> RuleExecution: ...


class RuleEvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[tuple[str, str], RuleEvaluator] = {}

    def register(self, evaluator: RuleEvaluator) -> None:
        key = (evaluator.rule_id, evaluator.rule_version)
        if key in self._evaluators:
            raise ValueError(
                f"Evaluator for ({evaluator.rule_id}, {evaluator.rule_version}) "
                "is already registered."
            )
        self._evaluators[key] = evaluator

    def get(self, rule_id: str, rule_version: str) -> RuleEvaluator | None:
        return self._evaluators.get((rule_id, rule_version))

    def has(self, rule_id: str, rule_version: str) -> bool:
        return (rule_id, rule_version) in self._evaluators


def _episode_checksum(episode: CanonicalEpisode) -> str:
    payload = (
        f"{episode.start.isoformat()}|{episode.end.isoformat()}|"
        f"{episode.sample_count}|{episode.episode_type}"
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _validate_evaluator_output(
    rule: Rule, episode: CanonicalEpisode, execution: RuleExecution
) -> RuleExecution:
    if execution.rule_id != rule.rule_id:
        raise ValueError(
            f"Evaluator for {rule.rule_id} produced an execution with "
            f"rule_id={execution.rule_id!r}."
        )
    if execution.rule_version != rule.version:
        raise ValueError(
            f"Evaluator for {rule.rule_id} produced an execution with "
            f"rule_version={execution.rule_version!r}; expected "
            f"{rule.version!r}."
        )
    if execution.period_start != episode.start or execution.period_end != episode.end:
        raise ValueError(
            f"Evaluator for {rule.rule_id} produced an execution with a "
            "period that does not match the episode."
        )
    return execution


def evaluate_rule_catalog(
    catalog: RuleCatalog,
    episode: CanonicalEpisode,
    registry: RuleEvaluatorRegistry,
) -> tuple[RuleEvaluationOutcome, ...]:
    outcomes: list[RuleEvaluationOutcome] = []

    for rule in catalog.list_rules():
        if rule.implementation_status.value == "planned":
            outcomes.append(
                RuleEvaluationOutcome(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    status=RuleEvaluationStatus.NOT_EVALUABLE,
                    reason=RuleEvaluationReason.RULE_NOT_IMPLEMENTED,
                )
            )
            continue

        missing = tuple(
            signal for signal in rule.signals_required if episode.signals.get(signal) is None
        )
        if missing:
            outcomes.append(
                RuleEvaluationOutcome(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    status=RuleEvaluationStatus.NOT_EVALUABLE,
                    reason=RuleEvaluationReason.MISSING_REQUIRED_SIGNALS,
                    missing_signals=missing,
                )
            )
            continue

        evaluator = registry.get(rule.rule_id, rule.version)
        if evaluator is None:
            outcomes.append(
                RuleEvaluationOutcome(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    status=RuleEvaluationStatus.NOT_EVALUABLE,
                    reason=RuleEvaluationReason.EVALUATOR_NOT_REGISTERED,
                )
            )
            continue

        execution = _validate_evaluator_output(rule, episode, evaluator.evaluate(rule, episode))
        if execution.fired:
            outcomes.append(
                RuleEvaluationOutcome(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    status=RuleEvaluationStatus.FIRED,
                    reason=None,
                    execution=execution,
                )
            )
        else:
            outcomes.append(
                RuleEvaluationOutcome(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    status=RuleEvaluationStatus.EVALUATED_NOT_FIRED,
                    reason=None,
                    execution=execution,
                )
            )

    return tuple(outcomes)


def eligible_fired_rules(
    executions: tuple[RuleExecution, ...],
) -> tuple[RuleExecution, ...]:
    return tuple(e for e in executions if e.fired and e.evidence)
