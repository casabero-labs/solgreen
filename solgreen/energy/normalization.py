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
    is_power_field_source_compatible,
    is_timezone_aware,
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
        self._validate_authority_for_current_fields()
        self._validate_field_source_internal()
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
            self._validate_zero_explicit_magnitudes()
            self._validate_magnitude_conservation()
        else:
            self._validate_non_normalized_status_metadata()
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

    def _validate_authority_for_current_fields(self) -> None:
        if self.authority_class is not AuthorityClass.OPERATIONAL:
            raise ValueError(
                f"DirectionalPowerResult for operational field "
                f"'{self.canonical_field}' must use authority_class=operational, "
                f"got '{self.authority_class}'. AuthorityClass.FISCAL is "
                f"reserved for future fiscal-specific fields."
            )

    def _validate_field_source_internal(self) -> None:
        compatible = is_power_field_source_compatible(self.canonical_field, self.source_system)
        if self.status is NormalizationStatus.FIELD_MISMATCH:
            if compatible:
                raise ValueError(
                    f"FIELD_MISMATCH status requires incompatible "
                    f"field/source pair: got "
                    f"field='{self.canonical_field}', "
                    f"source='{self.source_system}' which are compatible."
                )
        elif compatible is False:
            raise ValueError(
                f"canonical_field '{self.canonical_field}' and source_system "
                f"'{self.source_system}' are incompatible; status must be "
                f"field_mismatch."
            )

    def _validate_zero_explicit_magnitudes(self) -> None:
        if self.raw_power_w != 0.0:
            return
        raw = self.raw_power_w
        assert raw is not None
        field = self.canonical_field
        grid_fields = {CanonicalPowerField.FLOW_GRID, CanonicalPowerField.TELEMETRY_GRID}
        battery_fields = {CanonicalPowerField.FLOW_BATTERY, CanonicalPowerField.TELEMETRY_BATTERY}
        pv_fields = {CanonicalPowerField.FLOW_PRODUCCION, CanonicalPowerField.TELEMETRY_PV}
        load_fields = {CanonicalPowerField.FLOW_CONSUMO}

        if field in grid_fields:
            if self.grid_import_w != 0.0:
                raise ValueError("zero grid result requires grid_import_w=0.0.")
            if self.grid_export_w != 0.0:
                raise ValueError("zero grid result requires grid_export_w=0.0.")
            if self.battery_charge_w is not None:
                raise ValueError("zero grid result must not populate battery_charge_w.")
            if self.battery_discharge_w is not None:
                raise ValueError("zero grid result must not populate battery_discharge_w.")
            if self.pv_generation_w is not None:
                raise ValueError("zero grid result must not populate pv_generation_w.")
            if self.load_consumption_w is not None:
                raise ValueError("zero grid result must not populate load_consumption_w.")
        elif field in battery_fields:
            if self.battery_charge_w != 0.0:
                raise ValueError("zero battery result requires battery_charge_w=0.0.")
            if self.battery_discharge_w != 0.0:
                raise ValueError("zero battery result requires battery_discharge_w=0.0.")
            if self.grid_import_w is not None:
                raise ValueError("zero battery result must not populate grid_import_w.")
            if self.grid_export_w is not None:
                raise ValueError("zero battery result must not populate grid_export_w.")
            if self.pv_generation_w is not None:
                raise ValueError("zero battery result must not populate pv_generation_w.")
            if self.load_consumption_w is not None:
                raise ValueError("zero battery result must not populate load_consumption_w.")
        elif field in pv_fields:
            if self.pv_generation_w != 0.0:
                raise ValueError("zero pv result requires pv_generation_w=0.0.")
            if self.grid_import_w is not None:
                raise ValueError("zero pv result must not populate grid_import_w.")
            if self.grid_export_w is not None:
                raise ValueError("zero pv result must not populate grid_export_w.")
            if self.battery_charge_w is not None:
                raise ValueError("zero pv result must not populate battery_charge_w.")
            if self.battery_discharge_w is not None:
                raise ValueError("zero pv result must not populate battery_discharge_w.")
            if self.load_consumption_w is not None:
                raise ValueError("zero pv result must not populate load_consumption_w.")
        elif field in load_fields:
            if self.load_consumption_w != 0.0:
                raise ValueError("zero load result requires load_consumption_w=0.0.")
            if self.grid_import_w is not None:
                raise ValueError("zero load result must not populate grid_import_w.")
            if self.grid_export_w is not None:
                raise ValueError("zero load result must not populate grid_export_w.")
            if self.battery_charge_w is not None:
                raise ValueError("zero load result must not populate battery_charge_w.")
            if self.battery_discharge_w is not None:
                raise ValueError("zero load result must not populate battery_discharge_w.")
            if self.pv_generation_w is not None:
                raise ValueError("zero load result must not populate pv_generation_w.")

    def _validate_magnitude_conservation(self) -> None:
        raw = self.raw_power_w
        if raw is None or raw == 0.0:
            return
        expected = abs(raw)
        field = self.canonical_field
        grid_fields = {CanonicalPowerField.FLOW_GRID, CanonicalPowerField.TELEMETRY_GRID}
        battery_fields = {CanonicalPowerField.FLOW_BATTERY, CanonicalPowerField.TELEMETRY_BATTERY}
        pv_fields = {CanonicalPowerField.FLOW_PRODUCCION, CanonicalPowerField.TELEMETRY_PV}
        load_fields = {CanonicalPowerField.FLOW_CONSUMO}

        if field in grid_fields:
            self._validate_signed_pair(
                primary=self.grid_import_w,
                other=self.grid_export_w,
                expected=expected,
                primary_label="grid_import_w",
                other_label="grid_export_w",
            )
            self._assert_other_fields_none(
                "grid",
                (
                    "battery_charge_w",
                    "battery_discharge_w",
                    "pv_generation_w",
                    "load_consumption_w",
                ),
            )
        elif field in battery_fields:
            self._validate_signed_pair(
                primary=self.battery_charge_w,
                other=self.battery_discharge_w,
                expected=expected,
                primary_label="battery_charge_w",
                other_label="battery_discharge_w",
            )
            self._assert_other_fields_none(
                "battery",
                (
                    "grid_import_w",
                    "grid_export_w",
                    "pv_generation_w",
                    "load_consumption_w",
                ),
            )
        elif field in pv_fields:
            if raw <= 0:
                raise ValueError(f"normalized pv result must have raw_power_w > 0, got {raw}.")
            if self.pv_generation_w != raw:
                raise ValueError(
                    f"pv_generation_w ({self.pv_generation_w}) must equal raw_power_w ({raw})."
                )
            self._assert_other_fields_none(
                "pv_generation_w",
                (
                    "grid_import_w",
                    "grid_export_w",
                    "battery_charge_w",
                    "battery_discharge_w",
                    "load_consumption_w",
                ),
            )
        elif field in load_fields:
            if raw <= 0:
                raise ValueError(f"normalized load result must have raw_power_w > 0, got {raw}.")
            if self.load_consumption_w != raw:
                raise ValueError(
                    f"load_consumption_w ({self.load_consumption_w}) must equal "
                    f"raw_power_w ({raw})."
                )
            self._assert_other_fields_none(
                "load_consumption_w",
                (
                    "grid_import_w",
                    "grid_export_w",
                    "battery_charge_w",
                    "battery_discharge_w",
                    "pv_generation_w",
                ),
            )

    def _validate_signed_pair(
        self,
        *,
        primary: float | None,
        other: float | None,
        expected: float,
        primary_label: str,
        other_label: str,
    ) -> None:
        if primary is not None and other is not None:
            raise ValueError(f"{primary_label} and {other_label} cannot both be populated.")
        if primary is not None:
            if primary != expected:
                raise ValueError(
                    f"{primary_label} ({primary}) must equal abs(raw_power_w) ({expected})."
                )
        elif other is not None:
            if other != expected:
                raise ValueError(
                    f"{other_label} ({other}) must equal abs(raw_power_w) ({expected})."
                )
        else:
            raise ValueError(
                f"normalized signed result must populate either "
                f"{primary_label} or {other_label} for non-zero value."
            )

    def _assert_other_fields_none(self, populated: str, others: tuple[str, ...]) -> None:
        for field_name in others:
            if getattr(self, field_name) is not None:
                raise ValueError(f"{populated} populated; {field_name} must be None.")

    def _validate_non_normalized_status_metadata(self) -> None:
        status = self.status
        if status is NormalizationStatus.PROFILE_NOT_FOUND:
            if self.profile_version is not None:
                raise ValueError("profile_not_found result must have profile_version=None.")
            if self.profile_status is not None:
                raise ValueError("profile_not_found result must have profile_status=None.")
        elif status is NormalizationStatus.MISSING_VALUE:
            if self.raw_power_w is not None:
                raise ValueError("missing_value result must have raw_power_w=None.")
        elif status is NormalizationStatus.NONFINITE_VALUE:
            if self.raw_power_w is None or math.isfinite(self.raw_power_w):
                raise ValueError("nonfinite_value result must have non-finite raw_power_w.")
        elif status is NormalizationStatus.INVALID_UNSIGNED_NEGATIVE:
            if self.raw_power_w is None or self.raw_power_w >= 0:
                raise ValueError("invalid_unsigned_negative result must have raw_power_w < 0.")
        elif status is NormalizationStatus.PROFILE_NOT_CONFIRMED:
            if self.profile_version is None:
                raise ValueError("profile_not_confirmed result must have profile_version set.")
            if self.profile_status not in (
                ProfileStatus.PROVISIONAL,
                ProfileStatus.UNKNOWN,
            ):
                raise ValueError(
                    "profile_not_confirmed result must have profile_status=provisional or unknown."
                )
            if self.raw_power_w is None:
                raise ValueError("profile_not_confirmed result must have raw_power_w set.")


def normalize_power_value(
    *,
    plant_id: str,
    canonical_field: CanonicalPowerField,
    source_system: SourceSystem,
    timestamp: datetime,
    raw_power_w: float | None,
    registry: PowerSignProfileRegistry,
) -> DirectionalPowerResult:
    if not is_power_field_source_compatible(canonical_field, source_system):
        return DirectionalPowerResult(
            canonical_field=canonical_field,
            source_system=source_system,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=raw_power_w,
            status=NormalizationStatus.FIELD_MISMATCH,
        )

    if not is_timezone_aware(timestamp):
        raise ValueError(
            f"normalize_power_value() requires timezone-aware timestamp, got naive: {timestamp}"
        )

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
    if profile.canonical_field != canonical_field:
        raise ValueError(
            f"Internal error: profile field mismatch. "
            f"Expected {canonical_field}, got {profile.canonical_field}."
        )
    if profile.source_system != source_system:
        raise ValueError(
            f"Internal error: profile source mismatch. "
            f"Expected {source_system}, got {profile.source_system}."
        )
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
