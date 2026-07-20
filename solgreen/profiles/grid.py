from __future__ import annotations

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

ProfileName = Annotated[str, StringConstraints(min_length=1, max_length=128)]
ProfileStatus = Annotated[str, StringConstraints(min_length=1, max_length=64)]


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=AliasGenerator(alias=to_camel),
        populate_by_name=True,
    )


class GridNominal(_CamelModel):
    line_to_neutral_v: int = Field(ge=0)
    frequency_hz: float = Field(gt=0)


class GridThresholds(_CamelModel):
    overvoltage_v: float | None = None
    undervoltage_v: float | None = None
    frequency_high_hz: float | None = None
    frequency_low_hz: float | None = None


class GridProfile(_CamelModel):
    profile_version: str
    name: ProfileName
    status: ProfileStatus
    nominal: GridNominal
    thresholds: GridThresholds
    notes: tuple[str, ...] = Field(default_factory=tuple)


def load_grid_profile(path: Path) -> GridProfile:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Grid profile must be a YAML mapping, got {type(data).__name__}")
    return GridProfile.model_validate(data)
