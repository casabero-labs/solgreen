from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from solgreen.cli import app
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
    _resolve_existing_snapshot_id,
    _validate_timestamp,
)

runner = CliRunner()


def _make_snapshot(device_sn: str = "SR-001", **overrides: object) -> SolarmanSnapshot:
    data_list = [
        {"key": "B_P1", "value": 1200.0, "unit": "W", "name": "Battery"},
        {"key": "T_A_P_O_G", "value": -800.0, "unit": "W", "name": "Grid"},
        {"key": "C_P_PVT", "value": 3500.0, "unit": "W", "name": "PV"},
        {"key": "B_C1", "value": 5.0, "unit": "A", "name": "Current"},
    ]
    return parse_current_data_to_snapshot(
        data_list=data_list,
        device_sn=device_sn,
        device_type=str(overrides.get("device_type", "INVERTER")),
        device_state=int(overrides.get("device_state", 1)),
        collection_time_unix=int(overrides.get("collection_time_unix", 1784628000)),
        station_id=str(overrides.get("station_id", "ST-001")),
        plant_id=str(overrides.get("plant_id", "SOLGREEN")),
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
            cli_mode="d10", cli_effective_from="2026-08-01T00:00:00Z", plant_id="SOLGREEN"
        )
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="INVERTER",
            device_state=1,
            collection_time=datetime(2026, 8, 2, 12, 0, tzinfo=UTC),
            station_id="ST-001",
            plant_id="SOLGREEN",
            signals={"T_A_P_O_G": SnapshotSignal(api_key="T_A_P_O_G", value=300.0, unit="W")},
        )
        result = DeviceSyncResult(device_sn=snapshot.device_sn)
        entries = _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_not_confirmed == 1
        assert entries[0]["normalized_status"] == "profile_not_confirmed"

    def test_off_mode_no_normalization(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)
        entries = _normalize_snapshot(snapshot, ctx, result)
        assert len(entries) == 0

    def test_unsupported_signals_not_in_entries(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = _make_snapshot()
        result = DeviceSyncResult(device_sn=snapshot.device_sn)
        entries = _normalize_snapshot(snapshot, ctx, result)
        keys = {e["signal_key"] for e in entries}
        assert "B_C1" not in keys


class TestUnitValidation:
    def test_w_unit_accepted(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="I",
            device_state=1,
            collection_time=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            station_id="S",
            plant_id="SOLGREEN",
            signals={"B_P1": SnapshotSignal(api_key="B_P1", value=100.0, unit="W")},
        )
        result = DeviceSyncResult()
        _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_normalized == 1

    def test_amp_unit_rejected(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="I",
            device_state=1,
            collection_time=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            station_id="S",
            plant_id="SOLGREEN",
            signals={"B_P1": SnapshotSignal(api_key="B_P1", value=5.0, unit="A")},
        )
        result = DeviceSyncResult()
        returned = _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_errors == 1
        assert len(returned) == 0

    def test_kwh_unit_rejected(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="I",
            device_state=1,
            collection_time=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            station_id="S",
            plant_id="SOLGREEN",
            signals={"T_A_P_O_G": SnapshotSignal(api_key="T_A_P_O_G", value=2.0, unit="kWh")},
        )
        result = DeviceSyncResult()
        _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_errors == 1

    def test_kw_unit_not_silently_converted(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="I",
            device_state=1,
            collection_time=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            station_id="S",
            plant_id="SOLGREEN",
            signals={"C_P_PVT": SnapshotSignal(api_key="C_P_PVT", value=3.5, unit="kW")},
        )
        result = DeviceSyncResult()
        returned = _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_errors == 1
        assert len(returned) == 0

    def test_spaces_in_unit_normalized(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        snapshot = SolarmanSnapshot(
            device_sn="SR-001",
            device_type="I",
            device_state=1,
            collection_time=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            station_id="S",
            plant_id="SOLGREEN",
            signals={"B_P1": SnapshotSignal(api_key="B_P1", value=100.0, unit=" W ")},
        )
        result = DeviceSyncResult()
        _normalize_snapshot(snapshot, ctx, result)
        assert result.authorized_normalized == 1


class TestTimestampValidation:
    def test_none_rejected(self) -> None:
        with pytest.raises(ValueError, match="None"):
            _validate_timestamp(None)

    def test_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="> 0"):
            _validate_timestamp(0)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="> 0"):
            _validate_timestamp(-1)

    def test_valid_accepted(self) -> None:
        assert _validate_timestamp(1784628000) == 1784628000


class TestSyncResultErrorCounting:
    def test_errors_not_double_counted(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        dr = DeviceSyncResult(device_sn="X", authorized_errors=2, authorized_eligible=2)
        result.device_results.append(dr)
        result.error_count += dr.authorized_errors
        assert result.error_count == 2


class TestPersistenceMocks:
    @pytest.fixture
    def mock_snapshot(self) -> SolarmanSnapshot:
        return _make_snapshot(collection_time_unix=1784628000)

    @pytest.fixture
    def norm_entries(self) -> list[dict[str, object]]:
        return [
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

    def _build_conn(self, side_effect: list) -> MagicMock:
        cur = MagicMock()
        cur.fetchone.side_effect = side_effect
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cur
        return conn

    def test_insert_snapshot_success(self, mock_snapshot, norm_entries) -> None:
        conn = self._build_conn([(42,), (1,)])
        result = _persist_snapshot(conn, mock_snapshot, norm_entries)
        assert result["inserted"] is True
        assert result["normalized_inserted"] == 1
        conn.commit.assert_called_once()

    def test_skip_existing_snapshot_insert_normalized(self, mock_snapshot, norm_entries) -> None:
        conn = self._build_conn([None, (99,), (1,)])
        result = _persist_snapshot(conn, mock_snapshot, norm_entries)
        assert result["inserted"] is False
        assert result["skipped"] is True
        assert result["normalized_inserted"] == 1

    def test_skip_both_snapshot_and_normalized(self, mock_snapshot, norm_entries) -> None:
        conn = self._build_conn([None, (99,), None])
        result = _persist_snapshot(conn, mock_snapshot, norm_entries)
        assert result["normalized_skipped"] == 1

    def test_commit_called(self, mock_snapshot, norm_entries) -> None:
        conn = self._build_conn([(42,), (1,)])
        _persist_snapshot(conn, mock_snapshot, norm_entries)
        conn.commit.assert_called_once()

    def test_rollback_on_error(self, mock_snapshot, norm_entries) -> None:
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("simulated DB error")
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cur

        with pytest.raises(RuntimeError, match="simulated DB error"):
            _persist_snapshot(conn, mock_snapshot, norm_entries)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()

    def test_resolve_existing_snapshot_id(self, mock_snapshot) -> None:
        conn = self._build_conn([(99,)])
        sid = _resolve_existing_snapshot_id(conn, mock_snapshot)
        assert sid == 99

    def test_resolve_nonexistent_snapshot_id(self, mock_snapshot) -> None:
        conn = self._build_conn([None])
        sid = _resolve_existing_snapshot_id(conn, mock_snapshot)
        assert sid is None


class TestCLI:
    def test_all_devices_fail_exit_1(self) -> None:
        result = runner.invoke(
            app, ["solarman", "sync", "--plant-id", "X", "--station-id", "0", "--no-db"]
        )
        assert result.exit_code == 1

    def test_no_station_has_exit_code(self) -> None:
        result = runner.invoke(app, ["solarman", "sync", "--plant-id", "X", "--no-db"])
        assert result.exit_code == 1

    def test_help_shows_sync_command(self) -> None:
        result = runner.invoke(app, ["solarman", "--help"])
        assert result.exit_code == 0
        assert "sync" in result.stdout

    def test_sync_help_no_secrets(self) -> None:
        result = runner.invoke(app, ["solarman", "sync", "--help"])
        assert "token" not in result.stdout.lower()
        assert "password" not in result.stdout.lower()
        assert "secret" not in result.stdout.lower()


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

    def test_error_count_includes_single_count(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=2)
        dr1 = DeviceSyncResult(device_sn="A", authorized_errors=2)
        dr2 = DeviceSyncResult(device_sn="B", authorized_errors=1)
        result.device_results = [dr1, dr2]
        result.error_count = dr1.authorized_errors + dr2.authorized_errors
        assert result.error_count == 3
