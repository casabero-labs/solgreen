from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.energy.normalization import (
    DirectionalPowerResult,
    NormalizationStatus,
    normalize_power_value,
)
from solgreen.energy.registry_seeds import (
    build_production_sign_profile_registry,
    build_telemetry_sign_profile_registry,
)
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerSignProfileRegistry,
    SourceSystem,
)

MAX_INLINE_NORMALIZATION_RESULTS = 10_000
MAX_MD_WARNING_DETAILS = 20


class SignNormalizationMode(StrEnum):
    OFF = "off"
    LEGACY = "legacy"
    D10 = "d10"


@dataclass(frozen=True)
class SignalBinding:
    raw_signal_name: str
    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    expected_unit: Literal["W"]


TELEMETRY_SIGNAL_BINDINGS: tuple[SignalBinding, ...] = (
    SignalBinding(
        raw_signal_name="potencia_de_bateria_w",
        canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
    SignalBinding(
        raw_signal_name="total_active_power_of_the_grid_w",
        canonical_field=CanonicalPowerField.TELEMETRY_GRID,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
    SignalBinding(
        raw_signal_name="pv_total_charging_power_w",
        canonical_field=CanonicalPowerField.TELEMETRY_PV,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
)


@dataclass(frozen=True)
class ImportNormalizationContext:
    sign_registry: PowerSignProfileRegistry | None
    registry_mode: SignNormalizationMode
    effective_from: datetime | None
    plant_id: str


class NormalizedSignalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    timestamp_utc: datetime
    raw_signal_name: str
    normalization: DirectionalPowerResult


class NormalizationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    eligible_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    result_count: int = Field(ge=0)
    normalized_count: int = Field(ge=0)
    not_confirmed_count: int = Field(ge=0)
    not_found_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)

    @pydantic.model_validator(mode="after")
    def _validate_invariants(self) -> NormalizationSummary:
        if self.eligible_count != (
            self.missing_count
            + self.normalized_count
            + self.not_confirmed_count
            + self.not_found_count
            + self.error_count
        ):
            raise ValueError(
                f"eligible_count ({self.eligible_count}) must equal "
                f"missing ({self.missing_count}) + "
                f"normalized ({self.normalized_count}) + "
                f"not_confirmed ({self.not_confirmed_count}) + "
                f"not_found ({self.not_found_count}) + "
                f"error ({self.error_count})"
            )
        if self.result_count != self.eligible_count - self.missing_count:
            raise ValueError(
                f"result_count ({self.result_count}) must equal "
                f"eligible_count ({self.eligible_count}) - "
                f"missing_count ({self.missing_count})"
            )
        if self.warning_count > self.result_count:
            raise ValueError(
                f"warning_count ({self.warning_count}) must not exceed "
                f"result_count ({self.result_count})"
            )
        return self


def _resolve_mode(
    cli_mode: str | None,
    env_mode: str | None,
) -> SignNormalizationMode:
    raw: str | None = cli_mode
    if raw is None:
        raw = env_mode
    if raw is None:
        return SignNormalizationMode.OFF
    try:
        return SignNormalizationMode(raw)
    except ValueError as exc:
        raise ValueError(
            f"Unknown sign normalization mode: {raw!r}. "
            f"Valid modes: {[m.value for m in SignNormalizationMode]}"
        ) from exc


def _parse_effective_from(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    try:
        from dateutil.parser import isoparse

        dt = isoparse(raw)
    except Exception as exc:
        raise ValueError(f"Invalid ISO 8601 datetime: {raw!r}") from exc
    if dt.utcoffset() is None:
        raise ValueError(
            f"effective_from must be timezone-aware (include Z or offset). Got: {raw!r}"
        )
    return dt


def build_normalization_context(
    *,
    cli_mode: str | None = None,
    env_mode: str | None = None,
    cli_effective_from: str | None = None,
    env_effective_from: str | None = None,
    plant_id: str,
) -> ImportNormalizationContext:
    mode = _resolve_mode(cli_mode, env_mode)

    raw_effective_from: str | None = cli_effective_from
    if raw_effective_from is None:
        raw_effective_from = env_effective_from

    effective_from = _parse_effective_from(raw_effective_from)

    if mode is SignNormalizationMode.OFF:
        if effective_from is not None:
            raise ValueError("SignNormalizationMode.OFF does not accept effective_from.")
        return ImportNormalizationContext(
            sign_registry=None,
            registry_mode=mode,
            effective_from=None,
            plant_id=plant_id,
        )

    if mode is SignNormalizationMode.LEGACY:
        if effective_from is not None:
            raise ValueError("SignNormalizationMode.LEGACY does not accept effective_from.")
        registry = build_telemetry_sign_profile_registry()
        return ImportNormalizationContext(
            sign_registry=registry,
            registry_mode=mode,
            effective_from=None,
            plant_id=plant_id,
        )

    if mode is SignNormalizationMode.D10:
        if effective_from is None:
            raise ValueError("SignNormalizationMode.D10 requires effective_from.")
        registry = build_production_sign_profile_registry(
            effective_from=effective_from,
        )
        return ImportNormalizationContext(
            sign_registry=registry,
            registry_mode=mode,
            effective_from=effective_from,
            plant_id=plant_id,
        )

    raise ValueError(f"Unhandled mode: {mode}")


def normalize_telemetry_signals(
    samples: list[InverterTelemetrySample],
    context: ImportNormalizationContext,
) -> tuple[tuple[NormalizedSignalResult, ...], NormalizationSummary]:
    if context.registry_mode is SignNormalizationMode.OFF:
        return (), NormalizationSummary(
            eligible_count=0,
            missing_count=0,
            result_count=0,
            normalized_count=0,
            not_confirmed_count=0,
            not_found_count=0,
            error_count=0,
            warning_count=0,
        )

    assert context.sign_registry is not None

    bindings = TELEMETRY_SIGNAL_BINDINGS
    eligible_count = len(samples) * len(bindings)

    results: list[NormalizedSignalResult] = []
    missing_count = 0
    normalized_count = 0
    not_confirmed_count = 0
    not_found_count = 0
    error_count = 0
    warning_count = 0

    for sample in samples:
        for binding in bindings:
            raw_power_w = sample.get_float(binding.raw_signal_name)

            direction = normalize_power_value(
                plant_id=context.plant_id,
                canonical_field=binding.canonical_field,
                source_system=binding.source_system,
                timestamp=sample.timestamp_utc,
                raw_power_w=raw_power_w,
                registry=context.sign_registry,
            )

            if direction.status is NormalizationStatus.MISSING_VALUE:
                missing_count += 1
                continue

            result = NormalizedSignalResult(
                canonical_field=binding.canonical_field,
                source_system=binding.source_system,
                timestamp_utc=sample.timestamp_utc,
                raw_signal_name=binding.raw_signal_name,
                normalization=direction,
            )
            results.append(result)

            if direction.status is NormalizationStatus.NORMALIZED:
                normalized_count += 1
                if direction.warnings:
                    warning_count += 1
            elif direction.status is NormalizationStatus.PROFILE_NOT_CONFIRMED:
                not_confirmed_count += 1
                warning_count += 1
            elif direction.status is NormalizationStatus.PROFILE_NOT_FOUND:
                not_found_count += 1
                warning_count += 1
            else:
                error_count += 1
                warning_count += 1

    summary = NormalizationSummary(
        eligible_count=eligible_count,
        missing_count=missing_count,
        result_count=len(results),
        normalized_count=normalized_count,
        not_confirmed_count=not_confirmed_count,
        not_found_count=not_found_count,
        error_count=error_count,
        warning_count=warning_count,
    )

    return tuple(results), summary
