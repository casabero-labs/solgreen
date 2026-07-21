from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    PowerDirection,
    PowerSignProfile,
    PowerSignProfileRegistry,
    ProfileStatus,
    SourceSystem,
)


class NormalizationStatus(StrEnum):
    NORMALIZED = "normalized"
    PROFILE_NOT_CONFIRMED = "profile_not_confirmed"
    PROFILE_NOT_FOUND = "profile_not_found"
    MISSING_VALUE = "missing_value"
    NONFINITE_VALUE = "nonfinite_value"
    INVALID_UNSIGNED_NEGATIVE = "invalid_unsigned_negative"
    FIELD_MISMATCH = "field_mismatch"


class DirectionalPowerResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    authority_class: AuthorityClass
    raw_power_w: float | None
    status: NormalizationStatus
    profile_version: str | None = None
    profile_status: ProfileStatus | None = None
    grid_import_w: float | None = None
    grid_export_w: float | None = None
    battery_charge_w: float | None = None
    battery_discharge_w: float | None = None
    pv_generation_w: float | None = None
    load_consumption_w: float | None = None
    warnings: tuple[str, ...] = Field(default=())

    @pydantic.model_validator(mode="after")
    def _validate_normalized_invariants(self) -> DirectionalPowerResult:
        if self.status is NormalizationStatus.NORMALIZED:
            if self.raw_power_w is None:
                raise ValueError("normalized result must have raw_power_w.")
            if not math.isfinite(self.raw_power_w):
                raise ValueError("normalized result raw_power_w must be finite.")
            if self.profile_version is None:
                raise ValueError("normalized result must have profile_version.")
            if self.profile_status is not ProfileStatus.CONFIRMED:
                raise ValueError("normalized result must have profile_status=confirmed.")
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
                        raise ValueError(f"{field_name} must be finite when populated.")
                    if val < 0:
                        raise ValueError(f"{field_name} must be non-negative when populated.")
            if (
                self.grid_import_w is not None
                and self.grid_export_w is not None
                and self.grid_import_w > 0
                and self.grid_export_w > 0
            ):
                raise ValueError("grid_import_w and grid_export_w cannot both be > 0.")
            if (
                self.battery_charge_w is not None
                and self.battery_discharge_w is not None
                and self.battery_charge_w > 0
                and self.battery_discharge_w > 0
            ):
                raise ValueError("battery_charge_w and battery_discharge_w cannot both be > 0.")
        else:
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
                    raise ValueError(
                        f"Non-normalized result must not populate directional fields. "
                        f"{field_name} is set."
                    )
        return self


def normalize_power_value(
    *,
    plant_id: str,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    timestamp: datetime,
    raw_power_w: float | None,
    registry: PowerSignProfileRegistry,
) -> DirectionalPowerResult:
    if raw_power_w is None:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=None,
            status=NormalizationStatus.MISSING_VALUE,
        )

    if not math.isfinite(raw_power_w):
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=raw_power_w,
            status=NormalizationStatus.NONFINITE_VALUE,
        )

    profile = registry.resolve(
        plant_id=plant_id,
        canonical_field=canonical_field,
        source_system=source_system,
        timestamp=timestamp,
    )

    if profile is None:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=raw_power_w,
            status=NormalizationStatus.PROFILE_NOT_FOUND,
        )

    if profile.status is not ProfileStatus.CONFIRMED:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=profile.authority_class,
            raw_power_w=raw_power_w,
            status=NormalizationStatus.PROFILE_NOT_CONFIRMED,
            profile_version=profile.profile_version,
            profile_status=profile.status,
        )

    return _apply_profile(
        canonical_field=canonical_field,
        source_system=source_system,
        profile=profile,
        raw_power_w=raw_power_w,
    )


def _apply_profile(
    *,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    profile: PowerSignProfile,
    raw_power_w: float,
) -> DirectionalPowerResult:
    if canonical_field in (
        CanonicalPowerField.FLOW_GRID,
        CanonicalPowerField.TELEMETRY_GRID,
    ):
        return _normalize_grid(
            canonical_field=canonical_field,
            source_system=source_system,
            profile=profile,
            raw_power_w=raw_power_w,
        )
    if canonical_field in (
        CanonicalPowerField.FLOW_BATTERY,
        CanonicalPowerField.TELEMETRY_BATTERY,
    ):
        return _normalize_battery(
            canonical_field=canonical_field,
            source_system=source_system,
            profile=profile,
            raw_power_w=raw_power_w,
        )
    if canonical_field in (
        CanonicalPowerField.FLOW_PRODUCCION,
        CanonicalPowerField.TELEMETRY_PV,
    ):
        return _normalize_unsigned(
            canonical_field=canonical_field,
            source_system=source_system,
            profile=profile,
            raw_power_w=raw_power_w,
            positive_field="pv_generation_w",
        )
    if canonical_field is CanonicalPowerField.FLOW_CONSUMO:
        return _normalize_unsigned(
            canonical_field=canonical_field,
            source_system=source_system,
            profile=profile,
            raw_power_w=raw_power_w,
            positive_field="load_consumption_w",
        )
    return DirectionalPowerResult(
        canonical_field=canonical_field,
        source_system=source_system,
        authority_class=profile.authority_class,
        raw_power_w=raw_power_w,
        status=NormalizationStatus.FIELD_MISMATCH,
        profile_version=profile.profile_version,
        profile_status=profile.status,
    )


def _normalize_grid(
    *,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    profile: PowerSignProfile,
    raw_power_w: float,
) -> DirectionalPowerResult:
    if raw_power_w == 0.0:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=profile.authority_class,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version=profile.profile_version,
            profile_status=profile.status,
            grid_import_w=0.0,
            grid_export_w=0.0,
        )

    positive_dir = profile.positive_means if raw_power_w > 0 else profile.negative_means

    magnitude = abs(raw_power_w)

    grid_import: float | None = None
    grid_export: float | None = None

    if positive_dir is PowerDirection.GRID_IMPORT:
        grid_import = magnitude
    elif positive_dir is PowerDirection.GRID_EXPORT:
        grid_export = magnitude

    return DirectionalPowerResult(
        canonical_field=canonical_field,
        source_system=source_system,
        authority_class=profile.authority_class,
        raw_power_w=raw_power_w,
        status=NormalizationStatus.NORMALIZED,
        profile_version=profile.profile_version,
        profile_status=profile.status,
        grid_import_w=grid_import,
        grid_export_w=grid_export,
    )


def _normalize_battery(
    *,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    profile: PowerSignProfile,
    raw_power_w: float,
) -> DirectionalPowerResult:
    if raw_power_w == 0.0:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=profile.authority_class,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version=profile.profile_version,
            profile_status=profile.status,
            battery_charge_w=0.0,
            battery_discharge_w=0.0,
        )

    positive_dir = profile.positive_means if raw_power_w > 0 else profile.negative_means

    magnitude = abs(raw_power_w)

    battery_charge: float | None = None
    battery_discharge: float | None = None

    if positive_dir is PowerDirection.BATTERY_CHARGE:
        battery_charge = magnitude
    elif positive_dir is PowerDirection.BATTERY_DISCHARGE:
        battery_discharge = magnitude

    return DirectionalPowerResult(
        canonical_field=canonical_field,
        source_system=source_system,
        authority_class=profile.authority_class,
        raw_power_w=raw_power_w,
        status=NormalizationStatus.NORMALIZED,
        profile_version=profile.profile_version,
        profile_status=profile.status,
        battery_charge_w=battery_charge,
        battery_discharge_w=battery_discharge,
    )


def _normalize_unsigned(
    *,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    profile: PowerSignProfile,
    raw_power_w: float,
    positive_field: str,
) -> DirectionalPowerResult:
    if raw_power_w < 0:
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=profile.authority_class,
            raw_power_w=raw_power_w,
            status=NormalizationStatus.INVALID_UNSIGNED_NEGATIVE,
            profile_version=profile.profile_version,
            profile_status=profile.status,
        )

    magnitude = raw_power_w

    kwargs: dict[str, float | None] = {
        "grid_import_w": None,
        "grid_export_w": None,
        "battery_charge_w": None,
        "battery_discharge_w": None,
        "pv_generation_w": None,
        "load_consumption_w": None,
    }
    kwargs[positive_field] = magnitude

    return DirectionalPowerResult(
        canonical_field=canonical_field,
        source_system=source_system,
        authority_class=profile.authority_class,
        raw_power_w=raw_power_w,
        status=NormalizationStatus.NORMALIZED,
        profile_version=profile.profile_version,
        profile_status=profile.status,
        **kwargs,
    )
