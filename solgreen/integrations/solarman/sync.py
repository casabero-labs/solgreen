from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from solgreen.energy.normalization import (
    NormalizationStatus,
    normalize_power_value,
)
from solgreen.energy.sign_profiles import SourceSystem
from solgreen.importer.normalize import ImportNormalizationContext, SignNormalizationMode
from solgreen.integrations.solarman.client import SolarmanClient
from solgreen.integrations.solarman.models import CurrentDataRecord
from solgreen.integrations.solarman.snapshot import (
    API_KEY_TO_CANONICAL_FIELD,
    SYNC_AUTHORIZED_KEYS,
    SolarmanSnapshot,
    parse_current_data_to_snapshot,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@dataclass
class DeviceSyncResult:
    device_sn: str = ""
    snapshot_inserted: bool = False
    snapshot_skipped: bool = False
    signal_count: int = 0
    authorized_eligible: int = 0
    authorized_normalized: int = 0
    authorized_not_confirmed: int = 0
    authorized_not_found: int = 0
    authorized_errors: int = 0
    error: str | None = None


@dataclass
class SyncResult:
    station_id: str
    plant_id: str
    devices_queried: int
    snapshots_inserted: int = 0
    snapshots_skipped: int = 0
    normalized_count: int = 0
    not_confirmed_count: int = 0
    not_found_count: int = 0
    error_count: int = 0
    device_results: list[DeviceSyncResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.snapshots_inserted > 0 or self.snapshots_skipped > 0

    @property
    def total_normalized(self) -> int:
        return (
            self.normalized_count
            + self.not_confirmed_count
            + self.not_found_count
            + self.error_count
        )


def sync_solarman_station(
    client: SolarmanClient,
    station_id: str,
    plant_id: str,
    norm_ctx: ImportNormalizationContext | None = None,
    conn: Any | None = None,
) -> SyncResult:
    devices = client.list_station_devices(station_id)
    result = SyncResult(
        station_id=station_id,
        plant_id=plant_id,
        devices_queried=len(devices),
    )

    for device in devices:
        device_result = _sync_device(
            client=client,
            device_info=device,
            station_id=station_id,
            plant_id=plant_id,
            norm_ctx=norm_ctx,
            conn=conn,
        )
        result.device_results.append(device_result)
        if device_result.snapshot_inserted:
            result.snapshots_inserted += 1
        elif device_result.snapshot_skipped:
            result.snapshots_skipped += 1
        result.normalized_count += device_result.authorized_normalized
        result.not_confirmed_count += device_result.authorized_not_confirmed
        result.not_found_count += device_result.authorized_not_found
        result.error_count += device_result.authorized_errors
        if device_result.error:
            result.errors.append(f"{device_result.device_sn}: {device_result.error}")
        if device_result.authorized_eligible > 0:
            result.error_count += device_result.authorized_errors

    return result


def _sync_device(
    client: SolarmanClient,
    device_info: object,
    station_id: str,
    plant_id: str,
    norm_ctx: ImportNormalizationContext | None,
    conn: Any | None,
) -> DeviceSyncResult:
    device_id = getattr(device_info, "device_id", None)
    device_sn = getattr(device_info, "device_sn", "unknown")

    if not device_id:
        return DeviceSyncResult(device_sn=device_sn, error="missing device_id")

    try:
        current_data: CurrentDataRecord = client.get_device_current_data(device_id)
    except Exception as exc:
        return DeviceSyncResult(device_sn=device_sn, error=str(exc))

    data_sn = current_data.device_sn or device_sn
    result = DeviceSyncResult(device_sn=data_sn)

    data_list = current_data.data_list or []

    try:
        snapshot = parse_current_data_to_snapshot(
            data_list=data_list,
            device_sn=data_sn,
            device_type=current_data.device_type,
            device_state=current_data.device_state,
            collection_time_unix=current_data.collection_time or 0,
            station_id=station_id,
            plant_id=plant_id,
        )
    except Exception as exc:
        result.error = f"snapshot parse: {exc}"
        return result

    result.signal_count = len(snapshot.signals)

    normalized_entries: list[dict[str, object]] = []
    if norm_ctx is not None and norm_ctx.registry_mode != SignNormalizationMode.OFF:
        normalized_entries = _normalize_snapshot(snapshot, norm_ctx, result)

    if conn is not None:
        try:
            saved = _persist_snapshot(conn, snapshot, normalized_entries)
            result.snapshot_inserted = saved.get("inserted", False)
            result.snapshot_skipped = saved.get("skipped", False)
        except Exception as exc:
            result.error = f"persist: {exc}"
            return result

    return result


def _normalize_snapshot(
    snapshot: SolarmanSnapshot,
    norm_ctx: ImportNormalizationContext,
    result: DeviceSyncResult,
) -> list[dict[str, object]]:
    registry = norm_ctx.sign_registry
    if registry is None:
        return []

    entries: list[dict[str, object]] = []
    for api_key in SYNC_AUTHORIZED_KEYS:
        sig = snapshot.signals.get(api_key)
        if sig is None or sig.value is None:
            continue

        canonical_field = API_KEY_TO_CANONICAL_FIELD[api_key]
        result.authorized_eligible += 1

        direction = normalize_power_value(
            plant_id=norm_ctx.plant_id,
            canonical_field=canonical_field,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=snapshot.collection_time,
            raw_power_w=sig.value,
            registry=registry,
        )

        status = direction.status
        if status is NormalizationStatus.MISSING_VALUE:
            continue

        entries.append(
            {
                "signal_key": api_key,
                "canonical_field": canonical_field.value,
                "source_system": direction.source_system.value,
                "raw_power_w": direction.raw_power_w,
                "normalized_status": direction.status.value,
                "grid_import_w": direction.grid_import_w,
                "grid_export_w": direction.grid_export_w,
                "battery_charge_w": direction.battery_charge_w,
                "battery_discharge_w": direction.battery_discharge_w,
                "pv_generation_w": direction.pv_generation_w,
                "load_consumption_w": direction.load_consumption_w,
                "warnings": json.dumps(list(direction.warnings)) if direction.warnings else None,
                "within_zero_deadband": direction.within_zero_deadband,
            }
        )

        if status is NormalizationStatus.NORMALIZED:
            result.authorized_normalized += 1
        elif status is NormalizationStatus.PROFILE_NOT_CONFIRMED:
            result.authorized_not_confirmed += 1
        elif status is NormalizationStatus.PROFILE_NOT_FOUND:
            result.authorized_not_found += 1
        else:
            result.authorized_errors += 1

    return entries


def _persist_snapshot(
    conn: Any,
    snapshot: SolarmanSnapshot,
    normalized_entries: list[dict[str, object]],
) -> dict[str, bool]:
    raw_json = json.dumps(
        {k: {"value": sig.value, "unit": sig.unit} for k, sig in snapshot.signals.items()}
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO solarman_snapshots
                (device_sn, device_type, device_state, collection_time,
                 station_id, plant_id, raw_signals, signal_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (device_sn, collection_time) DO NOTHING
            RETURNING id
            """,
            (
                snapshot.device_sn,
                snapshot.device_type,
                snapshot.device_state,
                snapshot.collection_time,
                snapshot.station_id,
                snapshot.plant_id,
                raw_json,
                len(snapshot.signals),
            ),
        )
        row = cur.fetchone()

    if row is None:
        return {"inserted": False, "skipped": True}

    snapshot_id = row[0]

    for entry in normalized_entries:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO solarman_normalized_signals
                    (snapshot_id, signal_key, canonical_field, source_system,
                     raw_power_w, normalized_status,
                     grid_import_w, grid_export_w,
                     battery_charge_w, battery_discharge_w,
                     pv_generation_w, load_consumption_w,
                     warnings, within_zero_deadband)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (snapshot_id, signal_key) DO NOTHING
                """,
                (
                    snapshot_id,
                    entry["signal_key"],
                    entry["canonical_field"],
                    entry["source_system"],
                    entry["raw_power_w"],
                    entry["normalized_status"],
                    entry["grid_import_w"],
                    entry["grid_export_w"],
                    entry["battery_charge_w"],
                    entry["battery_discharge_w"],
                    entry["pv_generation_w"],
                    entry["load_consumption_w"],
                    entry["warnings"],
                    entry["within_zero_deadband"],
                ),
            )
    conn.commit()
    return {"inserted": True, "skipped": False}
