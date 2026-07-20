from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

PlantAlias = Annotated[str, StringConstraints(min_length=1, max_length=64)]


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
    )


class SystemTopology(_CamelModel):
    topology: str
    inverter_rated_power_w: int = Field(ge=0)
    battery_nominal_energy_wh: int = Field(ge=0)
    battery_nominal_voltage_v: float = Field(gt=0)
    pv_mppt_count: int = Field(ge=0, le=8)


class BatteryLimits(_CamelModel):
    normal_min_soc_pct: float = Field(ge=0.0, le=100.0)
    temporary_emergency_min_soc_pct: float = Field(ge=0.0, le=100.0)
    max_charge_power_w: int | None = None
    max_discharge_power_w: int | None = None
    source: str


class GridLimits(_CamelModel):
    profile_ref: str


class PrivacyConfig(_CamelModel):
    store_serial_encrypted: bool
    redact_serial_in_shared_reports: bool


class PlantProfile(_CamelModel):
    profile_version: str
    plant_alias: PlantAlias
    site_timezone: str
    system: SystemTopology
    limits: dict[str, object]
    privacy: PrivacyConfig

    def battery_limits(self) -> BatteryLimits | None:
        raw = self.limits.get("battery")
        if isinstance(raw, dict):
            return BatteryLimits.model_validate(raw)
        return None

    def grid_limits(self) -> GridLimits | None:
        raw = self.limits.get("grid")
        if isinstance(raw, dict):
            return GridLimits.model_validate(raw)
        return None


def load_plant_profile(path: Path) -> PlantProfile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Plant profile must be a YAML mapping, got {type(data).__name__}")
    return PlantProfile.model_validate(data)
