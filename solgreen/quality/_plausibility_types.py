from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.contracts.enums import SourceType


class PlausibilityStatus(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    PENDING_CONFIRMATION = "pending_confirmation"


class PlausibilityReasonCode(StrEnum):
    NAN = "nan"
    POSITIVE_INFINITY = "positive_infinity"
    NEGATIVE_INFINITY = "negative_infinity"
    SOC_OUT_OF_RANGE = "soc_out_of_range"
    BELOW_ABSOLUTE_ZERO = "below_absolute_zero"
    BELOW_MINIMUM = "below_minimum"
    ABOVE_MAXIMUM = "above_maximum"


class MeasurementRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_name: str = Field(description="Nombre canonico de la senal validada.")
    unit: str = Field(description="Unidad fisica de la senal.")
    minimum: float = Field(description="Limite inferior de plausibilidad.")
    maximum: float = Field(description="Limite superior de plausibilidad.")
    source: str = Field(description="Procedencia documentada del rango.")
    status: PlausibilityStatus = Field(description="Estado de confirmacion del rango.")
    profile_version: str = Field(description="Version del perfil al que pertenece.")

    @pydantic.model_validator(mode="after")
    def _minimum_not_above_maximum(self) -> MeasurementRange:
        if self.minimum > self.maximum:
            raise ValueError(
                f"MeasurementRange.minimum ({self.minimum}) cannot exceed maximum ({self.maximum})."
            )
        return self


class MeasurementPlausibilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_version: str = Field(description="Version del perfil de plausibilidad.")
    ranges: dict[str, MeasurementRange] = Field(
        default_factory=dict,
        description="Rangos por nombre canonico de senal.",
    )


class PlausibilityFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check_id: str = Field(description="Identificador del chequeo de plausibilidad.")
    check_version: str = Field(description="Version del chequeo.")
    source_type: SourceType = Field(description="Origen del sample evaluado.")
    signal_name: str = Field(description="Nombre canonico de la senal.")
    timestamp_utc: datetime = Field(description="Timestamp UTC del sample.")
    observed_value: float = Field(
        allow_inf_nan=True,
        description="Valor observado. Puede ser NaN o Infinity si el chequeo lo detecto.",
    )
    minimum: float | None = Field(
        default=None,
        description="Limite inferior del rango (None para chequeos universales).",
    )
    maximum: float | None = Field(
        default=None,
        description="Limite superior del rango (None para chequeos universales).",
    )
    unit: str | None = Field(
        default=None,
        description="Unidad fisica (None para chequeos universales).",
    )
    profile_version: str | None = Field(
        default=None,
        description="Version del perfil cuando el chequeo proviene de rango configurado.",
    )
    profile_status: PlausibilityStatus | None = Field(
        default=None,
        description="Estado de confirmacion del rango configurado.",
    )
    profile_source: str | None = Field(
        default=None,
        description="Procedencia documentada del rango configurado.",
    )
    reason_code: PlausibilityReasonCode = Field(description="Codigo del motivo del hallazgo.")


class PlausibilityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluated_count: int = Field(
        default=0,
        ge=0,
        description="Numero de (sample, signal) evaluados bajo un rango explicito.",
    )
    passed_count: int = Field(default=0, ge=0, description="Numero de evaluaciones aprobadas.")
    failed_count: int = Field(
        default=0,
        ge=0,
        description="Numero de evaluaciones que produjeron al menos un hallazgo.",
    )
    not_configured_count: int = Field(
        default=0,
        ge=0,
        description="Numero de senales sin rango de plausibilidad explicito.",
    )
    findings: tuple[PlausibilityFinding, ...] = Field(
        default_factory=tuple,
        description="Hallazgos estructurados producidos por la evaluacion.",
    )
    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="passed_count / evaluated_count. None si evaluated_count == 0.",
    )
