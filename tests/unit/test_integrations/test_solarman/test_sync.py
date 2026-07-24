from __future__ import annotations

from datetime import UTC, datetime

import pytest

from solgreen.importer.normalize import build_normalization_context
from solgreen.integrations.solarman.snapshot import (
    SnapshotSignal,
    SolarmanSnapshot,
    parse_current_data_to_snapshot,
)
from solgreen.integrations.solarman.sync import (
    DeviceSyncResult,
    SyncResult,
    _normalize_snapshot,
    _persist_snapshot,
)


def _make_snapshot(device_sn: str = "SR-001") -> SolarmanSnapshot:
    data_list = [
        {"key": "B_P1", "value": 1200.0, "unit": "W", "name": "Battery"},
        {"key": "T_A_P_O_G", "value": -800.0, "unit": "W", "name": "Grid"},
        {"key": "C_P_PVT", "value": 3500.0, "unit": "W", "name": "PV"},
        {"key": "B_C1", "value": 5.0, "unit": "A", "name": "Current"},
    ]
    return parse_current_data_to_snapshot(
        data_list=data_list,
        device_sn=device_sn,
        device_type="INVERTER",
        device_state=1,
        collection_time_unix=1784628000,
        station_id="ST-001",
        plant_id="SOLGREEN",
    )


class TestNormalizeSnapshot:
    def test_legacy_normalizes_all_authorized(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)

        assert result.authorized_eligible == 3
        assert result.authorized_normalized == 3
        assert len(entries) == 3

    def test_battery_positive_discharge(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        battery = next(e for e in entries if e["signal_key"] == "B_P1")
        assert battery["normalized_status"] == "normalized"
        assert battery["battery_discharge_w"] == 1200.0

    def test_grid_negative_import(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        grid = next(e for e in entries if e["signal_key"] == "T_A_P_O_G")
        assert grid["normalized_status"] == "normalized"
        assert grid["grid_import_w"] == 800.0

    def test_pv_positive_generation(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        pv = next(e for e in entries if e["signal_key"] == "C_P_PVT")
        assert pv["normalized_status"] == "normalized"
        assert pv["pv_generation_w"] == 3500.0

    def test_d10_grid_positive_not_confirmed(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )

        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="INVERTER",
            device_state=1,
            collection_time=datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
            station_id="ST-001",
            plant_id="SOLGREEN",
            signals={
                "T_A_P_O_G": SnapshotSignal(api_key="T_A_P_O_G", value=300.0, unit="W"),
            },
        )
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_not_confirmed == 1
        assert entries[0]["normalized_status"] == "profile_not_confirmed"

    def test_d10_grid_negative_import(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )

        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="INVERTER",
            device_state=1,
            collection_time=datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
            station_id="ST-001",
            plant_id="SOLGREEN",
            signals={
                "T_A_P_O_G": SnapshotSignal(api_key="T_A_P_O_G", value=-500.0, unit="W"),
            },
        )
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_normalized == 1
        assert entries[0]["grid_import_w"] == 500.0

    def test_off_mode_no_normalization(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        assert len(entries) == 0
        assert result.authorized_eligible == 0

    def test_raw_power_preserved(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        battery = next(e for e in entries if e["signal_key"] == "B_P1")
        assert battery["raw_power_w"] == 1200.0

    def test_unsupported_signals_not_in_entries(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)

        entries = _normalize_snapshot(snapshot, ctx, result)
        keys = {e["signal_key"] for e in entries}
        assert "B_C1" not in keys


class TestPersistenceIdempotency:
    def test_insert_then_skip_on_conflict(self) -> None:
        import psycopg2

        try:
            conn = psycopg2.connect("dbname=test_solgreen user=test host=localhost")
        except Exception:
            pytest.skip("test database not available")
            return
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS solarman_snapshots (
                        id BIGSERIAL PRIMARY KEY,
                        device_sn TEXT NOT NULL,
                        device_type TEXT,
                        device_state INTEGER,
                        collection_time TIMESTAMPTZ NOT NULL,
                        station_id TEXT NOT NULL,
                        plant_id TEXT NOT NULL,
                        raw_signals JSONB NOT NULL,
                        signal_count INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        UNIQUE(device_sn, collection_time)
                    )
                """)
                cur.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS solarman_normalized_signals (
                        id BIGSERIAL PRIMARY KEY,
                        snapshot_id BIGINT NOT NULL REFERENCES solarman_snapshots(id) ON DELETE CASCADE,
                        signal_key TEXT NOT NULL,
                        canonical_field TEXT NOT NULL,
                        source_system TEXT NOT NULL DEFAULT 'inverter_telemetry',
                        raw_power_w DOUBLE PRECISION,
                        normalized_status TEXT NOT NULL,
                        grid_import_w DOUBLE PRECISION,
                        grid_export_w DOUBLE PRECISION,
                        battery_charge_w DOUBLE PRECISION,
                        battery_discharge_w DOUBLE PRECISION,
                        pv_generation_w DOUBLE PRECISION,
                        load_consumption_w DOUBLE PRECISION,
                        warnings JSONB,
                        within_zero_deadband BOOLEAN DEFAULT FALSE,
                        UNIQUE(snapshot_id, signal_key)
                    )
                """)
        except Exception:
            pytest.skip("test database not available")

        snapshot = _make_snapshot()

        saved1 = _persist_snapshot(conn, snapshot, [])
        assert saved1["inserted"] is True

        saved2 = _persist_snapshot(conn, snapshot, [])
        assert saved2["inserted"] is False
        assert saved2["skipped"] is True

        conn.close()

    def test_persist_with_normalized_signals(self) -> None:
        import psycopg2

        try:
            conn = psycopg2.connect("dbname=test_solgreen user=test host=localhost")
        except Exception:
            pytest.skip("test database not available")
            return
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS solarman_snapshots (
                        id BIGSERIAL PRIMARY KEY, device_sn TEXT NOT NULL,
                        device_type TEXT, device_state INTEGER,
                        collection_time TIMESTAMPTZ NOT NULL,
                        station_id TEXT NOT NULL, plant_id TEXT NOT NULL,
                        raw_signals JSONB NOT NULL, signal_count INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        UNIQUE(device_sn, collection_time)
                    )
                """)
                cur.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS solarman_normalized_signals (
                        id BIGSERIAL PRIMARY KEY,
                        snapshot_id BIGINT NOT NULL REFERENCES solarman_snapshots(id),
                        signal_key TEXT NOT NULL, canonical_field TEXT NOT NULL,
                        source_system TEXT NOT NULL DEFAULT 'inverter_telemetry',
                        raw_power_w DOUBLE PRECISION,
                        normalized_status TEXT NOT NULL,
                        grid_import_w DOUBLE PRECISION, grid_export_w DOUBLE PRECISION,
                        battery_charge_w DOUBLE PRECISION, battery_discharge_w DOUBLE PRECISION,
                        pv_generation_w DOUBLE PRECISION, load_consumption_w DOUBLE PRECISION,
                        warnings JSONB, within_zero_deadband BOOLEAN DEFAULT FALSE,
                        UNIQUE(snapshot_id, signal_key)
                    )
                """)
        except Exception:
            pytest.skip("test database not available")

        snapshot = _make_snapshot()
        entries = [
            {
                "signal_key": "B_P1",
                "canonical_field": "telemetry_battery_power_w",
                "source_system": "inverter_telemetry",
                "raw_power_w": 1200.0,
                "normalized_status": "normalized",
                "grid_import_w": None,
                "grid_export_w": None,
                "battery_charge_w": None,
                "battery_discharge_w": 1200.0,
                "pv_generation_w": None,
                "load_consumption_w": None,
                "warnings": None,
                "within_zero_deadband": False,
            }
        ]

        saved = _persist_snapshot(conn, snapshot, entries)
        assert saved["inserted"] is True

        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM solarman_normalized_signals")
            count = cur.fetchone()[0]
            assert count == 1

        conn.close()


class TestSyncResult:
    def test_success_when_inserted(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        result.snapshots_inserted = 1
        assert result.success is True

    def test_success_when_skipped(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        result.snapshots_skipped = 1
        assert result.success is True

    def test_not_success_when_nothing(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        assert result.success is False

    def test_total_normalized(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        result.normalized_count = 5
        result.not_confirmed_count = 2
        assert result.total_normalized == 7
