from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from solgreen.energy.sign_profiles import CanonicalPowerField

API_KEY_TO_CANONICAL_SIGNAL: dict[str, str] = {
    "B_P1": "potencia_de_bateria_w",
    "T_A_P_O_G": "total_active_power_of_the_grid_w",
    "C_P_PVT": "pv_total_charging_power_w",
}

API_KEY_TO_CANONICAL_FIELD: dict[str, CanonicalPowerField] = {
    "B_P1": CanonicalPowerField.TELEMETRY_BATTERY,
    "T_A_P_O_G": CanonicalPowerField.TELEMETRY_GRID,
    "C_P_PVT": CanonicalPowerField.TELEMETRY_PV,
}

SYNC_AUTHORIZED_KEYS: frozenset[str] = frozenset(API_KEY_TO_CANONICAL_FIELD)


@dataclass(frozen=True, slots=True)
class SnapshotSignal:
    api_key: str
    value: float | None
    unit: str


@dataclass(frozen=True, slots=True)
class SolarmanSnapshot:
    device_sn: str
    device_type: str | None
    device_state: int | None
    collection_time: datetime
    station_id: str
    plant_id: str
    signals: dict[str, SnapshotSignal]


class SnapshotsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshots: list[SnapshotResult]
    snapshots_inserted: int
    snapshots_skipped: int
    normalized_signals: list[NormalizedSignalEntry]
    normalized_inserted: int


class SnapshotResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    device_sn: str
    collection_time: datetime
    inserted: bool
    signal_count: int


class NormalizedSignalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    device_sn: str
    signal_key: str
    canonical_field: str
    raw_power_w: float | None
    status: str


def parse_current_data_to_snapshot(
    data_list: list[dict[str, Any]],
    device_sn: str,
    device_type: str | None,
    device_state: int | None,
    collection_time_unix: int,
    station_id: str,
    plant_id: str,
) -> SolarmanSnapshot:
    collection_time = datetime.fromtimestamp(collection_time_unix, tz=UTC)

    signals: dict[str, SnapshotSignal] = {}
    for item in data_list:
        key = str(item.get("key", ""))
        if not key:
            continue
        raw = item.get("value")
        unit = str(item.get("unit", ""))
        try:
            value = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            value = None
        signals[key] = SnapshotSignal(api_key=key, value=value, unit=unit)

    return SolarmanSnapshot(
        device_sn=device_sn,
        device_type=device_type,
        device_state=device_state,
        collection_time=collection_time,
        station_id=station_id,
        plant_id=plant_id,
        signals=signals,
    )
