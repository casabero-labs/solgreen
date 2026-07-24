from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.energy.integration import (
    DirectionalPowerObservation,
    EnergySeriesIdentity,
    IntegrationMethod,
    IntegrationProfile,
    IntegrationResult,
    SampleSemantics,
    integrate_energy,
)
from solgreen.energy.normalization import NormalizationStatus
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerDirection,
    SourceSystem,
    is_timezone_aware,
)

logger = logging.getLogger(__name__)


class EnergyIntegrationMode(StrEnum):
    OFF = "off"
    INSTANTANEOUS = "instantaneous"


_DIRECTIONAL_POWER_FIELD_MAP: dict[PowerDirection, str] = {
    PowerDirection.GRID_IMPORT: "grid_import_w",
    PowerDirection.GRID_EXPORT: "grid_export_w",
    PowerDirection.BATTERY_CHARGE: "battery_charge_w",
    PowerDirection.BATTERY_DISCHARGE: "battery_discharge_w",
    PowerDirection.PV_GENERATION: "pv_generation_w",
}


SUPPORTED_SERIES: tuple[tuple[CanonicalPowerField, PowerDirection], ...] = (
    (CanonicalPowerField.TELEMETRY_GRID, PowerDirection.GRID_IMPORT),
    (CanonicalPowerField.TELEMETRY_GRID, PowerDirection.GRID_EXPORT),
    (CanonicalPowerField.TELEMETRY_BATTERY, PowerDirection.BATTERY_CHARGE),
    (CanonicalPowerField.TELEMETRY_BATTERY, PowerDirection.BATTERY_DISCHARGE),
    (CanonicalPowerField.TELEMETRY_PV, PowerDirection.PV_GENERATION),
)


class SolarmanPersistedSignalRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    collection_time: datetime
    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    normalized_status: NormalizationStatus
    sign_profile_version: str | None = None
    grid_import_w: float | None = None
    grid_export_w: float | None = None
    battery_charge_w: float | None = None
    battery_discharge_w: float | None = None
    pv_generation_w: float | None = None
    load_consumption_w: float | None = None

    @pydantic.model_validator(mode="after")
    def _validate_timestamp_aware(self) -> SolarmanPersistedSignalRow:
        if not is_timezone_aware(self.collection_time):
            raise ValueError("collection_time must be timezone-aware.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_magnitudes(self) -> SolarmanPersistedSignalRow:
        for field_name in (
            "grid_import_w",
            "grid_export_w",
            "battery_charge_w",
            "battery_discharge_w",
            "pv_generation_w",
            "load_consumption_w",
        ):
            val = getattr(self, field_name)
            if val is not None:
                if not math.isfinite(val):
                    raise ValueError(f"{field_name} must be finite when populated; got {val}.")
                if val < 0:
                    raise ValueError(
                        f"{field_name} must be non-negative when populated; got {val}."
                    )
        return self


def _map_row_to_directional_power(
    row: SolarmanPersistedSignalRow,
) -> tuple[PowerDirection, float | None]:
    if row.grid_import_w is not None:
        return PowerDirection.GRID_IMPORT, row.grid_import_w
    if row.grid_export_w is not None:
        return PowerDirection.GRID_EXPORT, row.grid_export_w
    if row.battery_charge_w is not None:
        return PowerDirection.BATTERY_CHARGE, row.battery_charge_w
    if row.battery_discharge_w is not None:
        return PowerDirection.BATTERY_DISCHARGE, row.battery_discharge_w
    if row.pv_generation_w is not None:
        return PowerDirection.PV_GENERATION, row.pv_generation_w
    return PowerDirection.UNKNOWN, None


def adapt_persisted_row_to_observation(
    row: SolarmanPersistedSignalRow,
    series_direction: PowerDirection,
) -> DirectionalPowerObservation:
    status = row.normalized_status
    profile_version = row.sign_profile_version

    if status is NormalizationStatus.NORMALIZED:
        if profile_version is None:
            return DirectionalPowerObservation(
                timestamp=row.collection_time,
                canonical_source=row.canonical_field,
                source_system=row.source_system,
                direction=series_direction,
                power_w=None,
                status=NormalizationStatus.PROFILE_NOT_FOUND,
                profile_version=None,
                lineage=("solarman_db_row",),
            )

        direction, magnitude = _map_row_to_directional_power(row)

        if direction is not series_direction:
            raise ValueError(
                f"Row direction {direction.value} does not match series direction "
                f"{series_direction.value}."
            )

        if magnitude is None:
            raise ValueError(
                f"Normalized row has no directional magnitude for direction "
                f"{series_direction.value}. Data integrity error."
            )

        if not math.isfinite(magnitude):
            raise ValueError(
                f"Normalized row has non-finite magnitude {magnitude} for "
                f"{series_direction.value}. Data integrity error."
            )

        if magnitude < 0:
            raise ValueError(
                f"Normalized row has negative magnitude {magnitude} for "
                f"{series_direction.value}. Data integrity error."
            )

        return DirectionalPowerObservation(
            timestamp=row.collection_time,
            canonical_source=row.canonical_field,
            source_system=row.source_system,
            direction=series_direction,
            power_w=magnitude,
            status=status,
            profile_version=profile_version,
            lineage=("solarman_db_row",),
        )

    return DirectionalPowerObservation(
        timestamp=row.collection_time,
        canonical_source=row.canonical_field,
        source_system=row.source_system,
        direction=series_direction,
        power_w=None,
        status=status,
        profile_version=None,
        lineage=("solarman_db_row",),
    )


class SolarmanEnergyRuntimeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    profile_version: str | None = None
    series_attempted: int = 0
    series_succeeded: int = 0
    series_failed: int = 0
    per_series_results: tuple[tuple[str, IntegrationResult], ...] = Field(default=())
    per_series_errors: tuple[tuple[str, str], ...] = Field(default=())
    results_persisted: bool = False
    warnings: tuple[str, ...] = Field(default=())


class SolarmanEnergyIntegrationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: EnergyIntegrationMode
    profile_version: str | None = None
    expected_interval: timedelta | None = None
    maximum_authorized_interval: timedelta | None = None
    lookback: timedelta | None = None
    profile: IntegrationProfile | None = None

    @pydantic.model_validator(mode="after")
    def _validate_off_rejects_energy_params(self) -> SolarmanEnergyIntegrationContext:
        if self.mode is EnergyIntegrationMode.OFF:
            for field_name, value in (
                ("profile_version", self.profile_version),
                ("expected_interval", self.expected_interval),
                ("maximum_authorized_interval", self.maximum_authorized_interval),
                ("lookback", self.lookback),
            ):
                if value is not None:
                    raise ValueError(f"EnergyIntegrationMode.OFF does not accept {field_name}.")
            if self.profile is not None:
                raise ValueError("EnergyIntegrationMode.OFF does not accept a profile.")
            return self

        if self.mode is EnergyIntegrationMode.INSTANTANEOUS:
            if not self.profile_version:
                raise ValueError("EnergyIntegrationMode.INSTANTANEOUS requires profile_version.")
            if self.expected_interval is None:
                raise ValueError("EnergyIntegrationMode.INSTANTANEOUS requires expected_interval.")
            if self.maximum_authorized_interval is None:
                raise ValueError(
                    "EnergyIntegrationMode.INSTANTANEOUS requires maximum_authorized_interval."
                )
            if self.lookback is None:
                raise ValueError("EnergyIntegrationMode.INSTANTANEOUS requires lookback.")
            if self.expected_interval <= timedelta(0):
                raise ValueError(
                    f"expected_interval must be strictly positive; got {self.expected_interval}."
                )
            if self.maximum_authorized_interval <= timedelta(0):
                raise ValueError(
                    f"maximum_authorized_interval must be strictly positive; "
                    f"got {self.maximum_authorized_interval}."
                )
            if self.lookback <= timedelta(0):
                raise ValueError(f"lookback must be strictly positive; got {self.lookback}.")
            if self.maximum_authorized_interval < self.expected_interval:
                raise ValueError(
                    f"maximum_authorized_interval ({self.maximum_authorized_interval}) "
                    f"must be >= expected_interval ({self.expected_interval})."
                )
            if self.lookback < self.maximum_authorized_interval:
                raise ValueError(
                    f"lookback ({self.lookback}) must be >= "
                    f"maximum_authorized_interval ({self.maximum_authorized_interval})."
                )
            profile = IntegrationProfile(
                profile_version=self.profile_version,
                sample_semantics=SampleSemantics.INSTANTANEOUS,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=self.expected_interval,
                maximum_authorized_interval=self.maximum_authorized_interval,
            )
            object.__setattr__(self, "profile", profile)
            return self

        raise ValueError(f"Unknown EnergyIntegrationMode: {self.mode}")


def build_energy_context(
    *,
    cli_mode: str | None = None,
    env_mode: str | None = None,
    cli_profile_version: str | None = None,
    env_profile_version: str | None = None,
    cli_expected_interval: str | None = None,
    env_expected_interval: str | None = None,
    cli_max_interval: str | None = None,
    env_max_interval: str | None = None,
    cli_lookback: str | None = None,
    env_lookback: str | None = None,
) -> SolarmanEnergyIntegrationContext:
    from solgreen.timeline.duration import parse_iso_duration

    raw_mode: str | None = cli_mode if cli_mode is not None else env_mode
    mode = EnergyIntegrationMode.OFF
    if raw_mode is not None:
        try:
            mode = EnergyIntegrationMode(raw_mode)
        except ValueError as err:
            raise ValueError(
                f"Unknown energy integration mode: {raw_mode!r}. "
                f"Valid modes: {[m.value for m in EnergyIntegrationMode]}"
            ) from err

    profile_version: str | None = (
        cli_profile_version if cli_profile_version is not None else env_profile_version
    )

    def _parse(raw: str | None) -> timedelta | None:
        if raw is None:
            return None
        return parse_iso_duration(raw)

    expected_interval: timedelta | None = None
    if cli_expected_interval is not None:
        expected_interval = _parse(cli_expected_interval)
    elif env_expected_interval is not None:
        expected_interval = _parse(env_expected_interval)

    maximum_authorized_interval: timedelta | None = None
    if cli_max_interval is not None:
        maximum_authorized_interval = _parse(cli_max_interval)
    elif env_max_interval is not None:
        maximum_authorized_interval = _parse(env_max_interval)

    lookback: timedelta | None = None
    if cli_lookback is not None:
        lookback = _parse(cli_lookback)
    elif env_lookback is not None:
        lookback = _parse(env_lookback)

    return SolarmanEnergyIntegrationContext(
        mode=mode,
        profile_version=profile_version,
        expected_interval=expected_interval,
        maximum_authorized_interval=maximum_authorized_interval,
        lookback=lookback,
    )


def load_persisted_signal_rows(
    conn: Any,
    plant_id: str,
    station_id: str,
    canonical_field: CanonicalPowerField,
    period_start: datetime,
    period_end: datetime,
) -> list[SolarmanPersistedSignalRow]:
    if not is_timezone_aware(period_start):
        raise ValueError("period_start must be timezone-aware.")
    if not is_timezone_aware(period_end):
        raise ValueError("period_end must be timezone-aware.")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ss.collection_time,
                ns.canonical_field,
                ns.source_system,
                ns.normalized_status,
                ns.sign_profile_version,
                ns.grid_import_w,
                ns.grid_export_w,
                ns.battery_charge_w,
                ns.battery_discharge_w,
                ns.pv_generation_w,
                ns.load_consumption_w
            FROM solarman_normalized_signals ns
            JOIN solarman_snapshots ss ON ss.id = ns.snapshot_id
            WHERE ss.plant_id = %s
              AND ss.station_id = %s
              AND ns.canonical_field = %s
              AND ss.collection_time >= %s
              AND ss.collection_time <= %s
            ORDER BY ss.collection_time ASC
            """,
            (plant_id, station_id, canonical_field.value, period_start, period_end),
        )
        rows = cur.fetchall()

    observations: list[SolarmanPersistedSignalRow] = []
    for row in rows:
        (
            collection_time,
            cf_val,
            source_val,
            norm_status_val,
            profile_version,
            grid_import_w,
            grid_export_w,
            battery_charge_w,
            battery_discharge_w,
            pv_generation_w,
            load_consumption_w,
        ) = row

        try:
            status = NormalizationStatus(norm_status_val)
        except ValueError:
            logger.warning(
                "Unknown normalization status %r for row at %s, treating as error",
                norm_status_val,
                collection_time,
            )
            status = NormalizationStatus.NORMALIZED

        observations.append(
            SolarmanPersistedSignalRow(
                collection_time=collection_time,
                canonical_field=CanonicalPowerField(cf_val),
                source_system=SourceSystem(source_val),
                normalized_status=status,
                sign_profile_version=profile_version,
                grid_import_w=grid_import_w,
                grid_export_w=grid_export_w,
                battery_charge_w=battery_charge_w,
                battery_discharge_w=battery_discharge_w,
                pv_generation_w=pv_generation_w,
                load_consumption_w=load_consumption_w,
            )
        )

    return observations


def run_energy_integration(
    conn: Any,
    plant_id: str,
    station_id: str,
    context: SolarmanEnergyIntegrationContext,
    period_start: datetime,
    period_end: datetime,
) -> SolarmanEnergyRuntimeResult:
    if context.mode is EnergyIntegrationMode.OFF:
        return SolarmanEnergyRuntimeResult(enabled=False)

    if context.profile is None:
        raise ValueError("EnergyIntegrationContext must have profile when mode is INSTANTANEOUS.")

    series_results: list[tuple[str, IntegrationResult]] = []
    series_errors: list[tuple[str, str]] = []
    succeeded = 0
    failed = 0

    for canonical_field, direction in SUPPORTED_SERIES:
        series_key = f"{canonical_field.value}/{direction.value}"
        try:
            rows = load_persisted_signal_rows(
                conn=conn,
                plant_id=plant_id,
                station_id=station_id,
                canonical_field=canonical_field,
                period_start=period_start,
                period_end=period_end,
            )

            if not rows:
                series = EnergySeriesIdentity(
                    source_field=canonical_field,
                    source_system=SourceSystem.INVERTER_TELEMETRY,
                    direction=direction,
                )
                empty_result = integrate_energy(
                    series=series,
                    observations=[],
                    profile=context.profile,
                    period_start=period_start,
                    period_end=period_end,
                )
                series_results.append((series_key, empty_result))
                succeeded += 1
                continue

            observations: list[DirectionalPowerObservation] = []
            for row in rows:
                obs = adapt_persisted_row_to_observation(row, direction)
                observations.append(obs)

            series = EnergySeriesIdentity(
                source_field=canonical_field,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                direction=direction,
            )

            result = integrate_energy(
                series=series,
                observations=observations,
                profile=context.profile,
                period_start=period_start,
                period_end=period_end,
            )
            series_results.append((series_key, result))
            succeeded += 1

        except Exception as exc:  # pragma: no cover - series isolation
            logger.warning("Series %s failed: %s", series_key, exc)
            series_errors.append((series_key, str(exc)))
            failed += 1

    warnings: list[str] = []
    if failed > 0:
        warnings.append("some_series_failed")

    return SolarmanEnergyRuntimeResult(
        enabled=True,
        profile_version=context.profile_version,
        series_attempted=len(SUPPORTED_SERIES),
        series_succeeded=succeeded,
        series_failed=failed,
        per_series_results=tuple(series_results),
        per_series_errors=tuple(series_errors),
        results_persisted=False,
        warnings=tuple(warnings),
    )
