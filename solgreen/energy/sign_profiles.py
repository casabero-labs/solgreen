from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

import pydantic
from pydantic import BaseModel, ConfigDict, Field


class CanonicalPowerField(StrEnum):
    FLOW_PRODUCCION = "flow_potencia_produccion_w"
    FLOW_CONSUMO = "flow_potencia_consumo_w"
    FLOW_GRID = "flow_grid_w"
    FLOW_BATTERY = "flow_battery_w"
    TELEMETRY_PV = "telemetry_pv_power_w"
    TELEMETRY_GRID = "telemetry_grid_power_w"
    TELEMETRY_BATTERY = "telemetry_battery_power_w"


class SourceSystem(StrEnum):
    SOLARMAN_PLANT_FLOW = "solarman_plant_flow"
    INVERTER_TELEMETRY = "inverter_telemetry"
    FISCAL_METER = "fiscal_meter"


class AuthorityClass(StrEnum):
    OPERATIONAL = "operational"
    FISCAL = "fiscal"


class ProfileStatus(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    UNKNOWN = "unknown"


class PowerDirection(StrEnum):
    GRID_IMPORT = "grid_import"
    GRID_EXPORT = "grid_export"
    BATTERY_CHARGE = "battery_charge"
    BATTERY_DISCHARGE = "battery_discharge"
    PV_GENERATION = "pv_generation"
    LOAD_CONSUMPTION = "load_consumption"
    UNSIGNED_MAGNITUDE = "unsigned_magnitude"
    UNKNOWN = "unknown"
    NO_FLOW = "no_flow"


_FLOW_FIELDS: frozenset[CanonicalPowerField] = frozenset(
    {
        CanonicalPowerField.FLOW_PRODUCCION,
        CanonicalPowerField.FLOW_CONSUMO,
        CanonicalPowerField.FLOW_GRID,
        CanonicalPowerField.FLOW_BATTERY,
    }
)

_TELEMETRY_FIELDS: frozenset[CanonicalPowerField] = frozenset(
    {
        CanonicalPowerField.TELEMETRY_PV,
        CanonicalPowerField.TELEMETRY_GRID,
        CanonicalPowerField.TELEMETRY_BATTERY,
    }
)

_GRID_FIELDS: frozenset[CanonicalPowerField] = frozenset(
    {
        CanonicalPowerField.FLOW_GRID,
        CanonicalPowerField.TELEMETRY_GRID,
    }
)

_BATTERY_FIELDS: frozenset[CanonicalPowerField] = frozenset(
    {
        CanonicalPowerField.FLOW_BATTERY,
        CanonicalPowerField.TELEMETRY_BATTERY,
    }
)

_PV_FIELDS: frozenset[CanonicalPowerField] = frozenset(
    {
        CanonicalPowerField.FLOW_PRODUCCION,
        CanonicalPowerField.TELEMETRY_PV,
    }
)

_LOAD_FIELDS: frozenset[CanonicalPowerField] = frozenset({CanonicalPowerField.FLOW_CONSUMO})

_GRID_DIRECTIONS: frozenset[PowerDirection] = frozenset(
    {PowerDirection.GRID_IMPORT, PowerDirection.GRID_EXPORT, PowerDirection.UNKNOWN}
)

_BATTERY_DIRECTIONS: frozenset[PowerDirection] = frozenset(
    {
        PowerDirection.BATTERY_CHARGE,
        PowerDirection.BATTERY_DISCHARGE,
        PowerDirection.UNKNOWN,
    }
)

_UNSIGNED_DIRECTIONS: frozenset[PowerDirection] = frozenset(
    {PowerDirection.PV_GENERATION, PowerDirection.UNSIGNED_MAGNITUDE, PowerDirection.UNKNOWN}
)

_LOAD_DIRECTIONS: frozenset[PowerDirection] = frozenset(
    {PowerDirection.LOAD_CONSUMPTION, PowerDirection.UNSIGNED_MAGNITUDE, PowerDirection.UNKNOWN}
)


def _field_source_compatible(field: CanonicalPowerField, source: SourceSystem) -> bool:
    if source is SourceSystem.SOLARMAN_PLANT_FLOW:
        return field in _FLOW_FIELDS
    if source is SourceSystem.INVERTER_TELEMETRY:
        return field in _TELEMETRY_FIELDS
    if source is SourceSystem.FISCAL_METER:
        return False
    return False


def _field_domain(field: CanonicalPowerField) -> str:
    if field in _GRID_FIELDS:
        return "grid"
    if field in _BATTERY_FIELDS:
        return "battery"
    if field in _PV_FIELDS:
        return "pv"
    if field in _LOAD_FIELDS:
        return "load"
    return "unknown"


def _allowed_directions(field: CanonicalPowerField) -> frozenset[PowerDirection]:
    if field in _GRID_FIELDS:
        return _GRID_DIRECTIONS
    if field in _BATTERY_FIELDS:
        return _BATTERY_DIRECTIONS
    if field in _PV_FIELDS:
        return _UNSIGNED_DIRECTIONS
    if field in _LOAD_FIELDS:
        return _LOAD_DIRECTIONS
    return frozenset()


class PowerSignProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plant_id: str = Field(min_length=1)
    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    authority_class: AuthorityClass
    measurement_point: str = Field(min_length=1)
    unit: Literal["W"]
    positive_means: PowerDirection
    negative_means: PowerDirection
    zero_means: PowerDirection = PowerDirection.NO_FLOW
    status: ProfileStatus
    evidence_refs: tuple[str, ...] = Field(default=())
    profile_version: str = Field(min_length=1)
    valid_from: datetime
    valid_to: datetime | None = None
    notes: str | None = None

    @pydantic.model_validator(mode="after")
    def _validate_datetime_aware(self) -> PowerSignProfile:
        if self.valid_from.tzinfo is None:
            raise ValueError("valid_from must be timezone-aware")
        if self.valid_to is not None and self.valid_to.tzinfo is None:
            raise ValueError("valid_to must be timezone-aware")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_valid_to_after_valid_from(self) -> PowerSignProfile:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError(
                f"valid_to ({self.valid_to}) must be after valid_from ({self.valid_from})."
            )
        return self

    @pydantic.field_validator("evidence_refs")
    @classmethod
    def _no_empty_evidence_refs(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(ref == "" for ref in v):
            raise ValueError("evidence_refs must not contain empty strings.")
        return v

    @pydantic.model_validator(mode="after")
    def _validate_field_source_compatibility(self) -> PowerSignProfile:
        if not _field_source_compatible(self.canonical_field, self.source_system):
            raise ValueError(
                f"Source system '{self.source_system}' is not compatible "
                f"with field '{self.canonical_field}'."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_fiscal_meter_restriction(self) -> PowerSignProfile:
        if self.source_system is SourceSystem.FISCAL_METER:
            raise ValueError(
                "fiscal_meter source system cannot claim authority over "
                "any operational power field. Fiscal profiles must target "
                "fiscal-specific fields, not the seven operational fields."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_confirmed_requires_evidence(self) -> PowerSignProfile:
        if self.status is ProfileStatus.CONFIRMED and len(self.evidence_refs) == 0:
            raise ValueError("A confirmed profile must have at least one evidence_ref.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_confirmed_directions_not_unknown(self) -> PowerSignProfile:
        if self.status is ProfileStatus.CONFIRMED:
            if self.positive_means is PowerDirection.UNKNOWN:
                raise ValueError("A confirmed profile must have a known positive_means.")
            if (
                self.negative_means is PowerDirection.UNKNOWN
                and self.canonical_field not in _PV_FIELDS
                and self.canonical_field not in _LOAD_FIELDS
            ):
                raise ValueError("A confirmed profile must have a known negative_means.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_unknown_status_directions(self) -> PowerSignProfile:
        if self.status is ProfileStatus.UNKNOWN:
            if self.positive_means is not PowerDirection.UNKNOWN:
                raise ValueError("An unknown profile must use positive_means=unknown.")
            if self.negative_means is not PowerDirection.UNKNOWN:
                raise ValueError("An unknown profile must use negative_means=unknown.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_directions_in_domain(self) -> PowerSignProfile:
        allowed = _allowed_directions(self.canonical_field)
        if self.status is ProfileStatus.UNKNOWN:
            pass
        else:
            if self.positive_means not in allowed:
                raise ValueError(
                    f"positive_means '{self.positive_means}' is not valid for "
                    f"field '{self.canonical_field}'. Allowed: {sorted(d.value for d in allowed)}"
                )
            if self.negative_means not in allowed:
                raise ValueError(
                    f"negative_means '{self.negative_means}' is not valid for "
                    f"field '{self.canonical_field}'. Allowed: {sorted(d.value for d in allowed)}"
                )
            if self.zero_means not in allowed and self.zero_means is not PowerDirection.NO_FLOW:
                raise ValueError(
                    f"zero_means '{self.zero_means}' is not valid for field '{self.canonical_field}'."
                )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_confirmed_directions_are_distinct(self) -> PowerSignProfile:
        if self.status is ProfileStatus.CONFIRMED and self.positive_means == self.negative_means:
            raise ValueError(
                "A confirmed profile must have distinct positive_means and negative_means."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_unsigned_field_negative_means(self) -> PowerSignProfile:
        if (
            (self.canonical_field in _PV_FIELDS or self.canonical_field in _LOAD_FIELDS)
            and self.status is ProfileStatus.CONFIRMED
            and self.negative_means
            not in (
                PowerDirection.UNKNOWN,
                PowerDirection.NO_FLOW,
            )
        ):
            raise ValueError(
                f"Unsigned field '{self.canonical_field}' cannot have "
                f"a confirmed negative_means of '{self.negative_means}'."
            )
        return self


class PowerSignProfileRegistry:
    def __init__(self) -> None:
        self._profiles: list[PowerSignProfile] = []

    @property
    def profiles(self) -> tuple[PowerSignProfile, ...]:
        return tuple(self._profiles)

    @property
    def count(self) -> int:
        return len(self._profiles)

    def register(self, profile: PowerSignProfile) -> None:
        for existing in self._profiles:
            if (
                existing.plant_id == profile.plant_id
                and existing.canonical_field == profile.canonical_field
                and existing.source_system == profile.source_system
                and existing.profile_version == profile.profile_version
                and existing.valid_from == profile.valid_from
                and existing.valid_to == profile.valid_to
            ):
                raise ValueError(
                    f"Duplicate profile: plant_id='{profile.plant_id}', "
                    f"field='{profile.canonical_field}', "
                    f"source='{profile.source_system}', "
                    f"version='{profile.profile_version}'."
                )
        for existing in self._profiles:
            if (
                existing.plant_id == profile.plant_id
                and existing.canonical_field == profile.canonical_field
                and existing.source_system == profile.source_system
                and existing.valid_to is not None
                and profile.valid_to is not None
                and not (
                    profile.valid_to <= existing.valid_from
                    or profile.valid_from >= existing.valid_to
                )
            ):
                raise ValueError(
                    f"Overlapping validity intervals for "
                    f"plant_id='{profile.plant_id}', "
                    f"field='{profile.canonical_field}', "
                    f"source='{profile.source_system}'. "
                    f"Existing: [{existing.valid_from}, {existing.valid_to}]."
                )
            if (
                existing.plant_id == profile.plant_id
                and existing.canonical_field == profile.canonical_field
                and existing.source_system == profile.source_system
                and existing.valid_to is None
            ):
                raise ValueError(
                    f"Cannot register a new profile with finite valid_to "
                    f"when an open-ended profile already exists for "
                    f"plant_id='{profile.plant_id}', "
                    f"field='{profile.canonical_field}', "
                    f"source='{profile.source_system}'."
                )
        self._profiles.append(profile)

    def resolve(
        self,
        plant_id: str,
        canonical_field: CanonicalPowerField,
        source_system: SourceSystem,
        timestamp: datetime,
    ) -> PowerSignProfile | None:
        candidates: list[PowerSignProfile] = []
        for profile in self._profiles:
            if (
                profile.plant_id == plant_id
                and profile.canonical_field == canonical_field
                and profile.source_system == source_system
                and timestamp >= profile.valid_from
                and (profile.valid_to is None or timestamp < profile.valid_to)
            ):
                candidates.append(profile)
        if len(candidates) == 0:
            return None
        if len(candidates) > 1:
            raise ValueError(
                f"Ambiguous profile resolution: {len(candidates)} profiles "
                f"match plant_id='{plant_id}', "
                f"field='{canonical_field}', "
                f"source='{source_system}', "
                f"timestamp='{timestamp}'."
            )
        return candidates[0]


def build_production_sign_profile_registry() -> PowerSignProfileRegistry:
    return PowerSignProfileRegistry()
