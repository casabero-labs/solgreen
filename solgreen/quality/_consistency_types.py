from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.timeline.canonical import CanonicalSample


class ConsistencyStatus(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    PENDING_CONFIRMATION = "pending_confirmation"


_FlowPrefix = "flow_"
_TelemetryPrefix = "telemetry_"


class ConsistencyPair(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_id: str = Field(min_length=1, description="Identificador unico del par.")
    pair_version: str = Field(min_length=1, description="Version semantica del par.")
    flow_field: str = Field(description="Nombre del campo CanonicalSample del lado flow.")
    telemetry_field: str = Field(description="Nombre del campo CanonicalSample del lado telemetry.")
    unit: str = Field(min_length=1, description="Unidad fisica compartida.")
    absolute_tolerance: float | None = Field(
        default=None,
        ge=0.0,
        description="Tolerancia absoluta en la unidad declarada.",
    )
    relative_tolerance: float | None = Field(
        default=None,
        ge=0.0,
        description="Tolerancia relativa como fraccion (ej. 0.01 = 1%).",
    )
    max_alignment_delta: timedelta = Field(
        default=timedelta(0),
        description="Limite de time_delta para evaluar el par.",
    )
    source: str = Field(min_length=1, description="Procedencia documentada del par.")
    status: ConsistencyStatus = Field(description="Estado de confirmacion del par.")
    profile_version: str = Field(min_length=1, description="Version del perfil al que pertenece.")

    @pydantic.model_validator(mode="after")
    def _validate_pair(self) -> ConsistencyPair:
        if not self.flow_field.startswith(_FlowPrefix):
            raise ValueError(f"flow_field must start with '{_FlowPrefix}': '{self.flow_field}'")
        if not self.telemetry_field.startswith(_TelemetryPrefix):
            raise ValueError(
                f"telemetry_field must start with '{_TelemetryPrefix}': '{self.telemetry_field}'"
            )
        if self.flow_field == self.telemetry_field:
            raise ValueError(f"flow_field and telemetry_field must differ: '{self.flow_field}'")
        if self.absolute_tolerance is None and self.relative_tolerance is None:
            raise ValueError(
                "At least one of absolute_tolerance or relative_tolerance "
                f"must be set for pair '{self.pair_id}'."
            )

        canonical_fields = set(CanonicalSample.model_fields)
        if self.flow_field not in canonical_fields:
            raise ValueError(f"flow_field '{self.flow_field}' does not exist in CanonicalSample.")
        if self.telemetry_field not in canonical_fields:
            raise ValueError(
                f"telemetry_field '{self.telemetry_field}' does not exist in CanonicalSample."
            )
        return self


class MeasurementConsistencyProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_version: str = Field(min_length=1, description="Version del perfil de consistencia.")
    pairs: tuple[ConsistencyPair, ...] = Field(
        default_factory=tuple,
        description="Pares flow-telemetry a evaluar.",
    )

    @pydantic.model_validator(mode="after")
    def _no_duplicate_pairs(self) -> MeasurementConsistencyProfile:
        seen: set[tuple[str, str]] = set()
        for pair in self.pairs:
            key = (pair.flow_field, pair.telemetry_field)
            if key in seen:
                raise ValueError(
                    f"Duplicate consistency pair: ({pair.flow_field}, {pair.telemetry_field})."
                )
            seen.add(key)
        return self


class ConsistencyReasonCode(StrEnum):
    OUTSIDE_TOLERANCE = "outside_tolerance"
    NONFINITE_VALUE = "nonfinite_value"


class ConsistencyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_id: str
    pair_version: str
    timestamp_utc: datetime
    flow_field: str
    telemetry_field: str
    flow_value: float | None
    telemetry_value: float | None
    absolute_difference: float | None
    allowed_difference: float | None
    unit: str
    time_delta: timedelta | None
    profile_version: str
    profile_status: ConsistencyStatus
    profile_source: str
    reason_code: ConsistencyReasonCode


class ConsistencyResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluated_count: int = Field(default=0, ge=0)
    passed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    skipped_missing_count: int = Field(default=0, ge=0)
    skipped_alignment_count: int = Field(default=0, ge=0)
    skipped_nonfinite_count: int = Field(default=0, ge=0)
    findings: tuple[ConsistencyFinding, ...] = Field(default_factory=tuple)
    score: float | None = Field(default=None, ge=0.0, le=1.0)

    @pydantic.model_validator(mode="after")
    def _check_invariants(self) -> ConsistencyResult:
        if self.evaluated_count != self.passed_count + self.failed_count:
            raise ValueError(
                "ConsistencyResult invariant violated: evaluated_count "
                f"({self.evaluated_count}) != passed_count ({self.passed_count}) "
                f"+ failed_count ({self.failed_count})."
            )
        if (self.evaluated_count == 0) != (self.score is None):
            raise ValueError(
                "ConsistencyResult invariant violated: evaluated_count == 0 "
                f"({self.evaluated_count == 0}) but score is {self.score} "
                "(must be None iff evaluated_count == 0)."
            )
        if self.evaluated_count > 0 and self.score is not None:
            expected = self.passed_count / self.evaluated_count
            if abs(self.score - expected) > 1e-9:
                raise ValueError(
                    f"ConsistencyResult invariant violated: score ({self.score}) "
                    f"!= passed_count / evaluated_count ({expected})."
                )
        return self
