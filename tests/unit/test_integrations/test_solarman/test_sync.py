from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from click import unstyle
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


def _plain_help(args: list[str]) -> str:
    result = runner.invoke(app, [*args, "--help"], color=False)
    assert result.exit_code == 0, result.output
    return unstyle(result.stdout)


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

    def test_conflict_without_row_raises_and_rollbacks(self, mock_snapshot, norm_entries) -> None:
        conn = self._build_conn([None, None])
        with pytest.raises(RuntimeError, match="conflict but not found"):
            _persist_snapshot(conn, mock_snapshot, norm_entries)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()


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
    def test_success_when_devices_succeeded(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        result.devices_succeeded = 1
        assert result.success is True

    def test_success_when_no_db_but_device_ok(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        result.devices_succeeded = 1
        assert result.snapshots_inserted == 0
        assert result.snapshots_skipped == 0
        assert result.success is True

    def test_not_success_when_nothing(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=1)
        assert result.devices_succeeded == 0
        assert result.success is False

    def test_partial_success_still_true(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=2)
        result.devices_succeeded = 1
        result.errors.append("device_2: failed")
        assert result.success is True

    def test_all_failed_success_false(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=2)
        result.devices_succeeded = 0
        result.errors.append("A: fail")
        result.errors.append("B: fail")
        assert result.success is False

    def test_error_count_includes_single_count(self) -> None:
        result = SyncResult(station_id="S1", plant_id="P1", devices_queried=2)
        dr1 = DeviceSyncResult(device_sn="A", authorized_errors=2)
        dr2 = DeviceSyncResult(device_sn="B", authorized_errors=1)
        result.device_results = [dr1, dr2]
        result.error_count = dr1.authorized_errors + dr2.authorized_errors
        assert result.error_count == 3


class TestSyncCliFlags:
    def test_sync_help_shows_json_flag(self) -> None:
        output = _plain_help(["solarman", "sync"])
        assert "--json" in output

    def test_sync_help_shows_dry_run_flag(self) -> None:
        output = _plain_help(["solarman", "sync"])
        assert "--dry-run" in output

    def test_sync_help_shows_no_db_flag(self) -> None:
        output = _plain_help(["solarman", "sync"])
        assert "--no-db" in output

    def test_dry_run_exit_0(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
        ):
            result = runner.invoke(
                app,
                ["solarman", "sync", "--dry-run", "--plant-id", "X", "--station-id", "ST001"],
            )
            assert result.exit_code == 0

    def test_dry_run_shows_dry_run_message(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
        ):
            result = runner.invoke(
                app,
                ["solarman", "sync", "--dry-run", "--plant-id", "X", "--station-id", "ST001"],
            )
            assert "dry-run" in result.stdout.lower() or "dry_run" in result.stdout.lower()

    def test_no_db_exit_1_when_station_resolved_but_sync_fails(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
        ):
            result = runner.invoke(
                app, ["solarman", "sync", "--no-db", "--plant-id", "X", "--station-id", "ST001"]
            )
            assert result.exit_code == 1

    def test_dry_run_does_not_acquire_lock(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch("solgreen.db.advisory_lock.acquire_sync_lock") as mock_lock,
        ):
            mock_lock.return_value = (MagicMock(), MagicMock())
            runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--dry-run",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                    "--db-url",
                    "postgresql://x",
                ],
            )
            assert mock_lock.call_count == 0

    def test_dry_run_does_not_open_db_connection(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch("solgreen.db.connection.get_connection") as mock_conn,
        ):
            mock_conn.return_value = MagicMock()
            runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--dry-run",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                    "--db-url",
                    "postgresql://x",
                ],
            )
            assert mock_conn.call_count == 0

    def test_client_close_called_on_resolution_failure(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_settings = MagicMock()
        mock_client = MagicMock()
        from solgreen.integrations.solarman.station_resolver import (
            StationResolutionError,
        )

        mock_client.close.side_effect = None

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch("solgreen.integrations.solarman.client.SolarmanClient", return_value=mock_client),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                side_effect=StationResolutionError("fail"),
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                ],
            )
            assert result.exit_code == 1
            mock_client.close.assert_called_once()

    def test_sync_exception_release_success_exits_1(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        mock_lock = MagicMock()
        mock_lock.release.return_value = MagicMock(value="released")

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch("solgreen.db.connection.get_connection") as mock_get_conn,
        ):
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            with (
                patch(
                    "solgreen.db.advisory_lock.acquire_sync_lock",
                    return_value=(mock_lock, MagicMock(value="acquired")),
                ),
                patch(
                    "solgreen.integrations.solarman.sync.sync_solarman_station",
                    side_effect=RuntimeError("sync fail"),
                ),
            ):
                result = runner.invoke(
                    app,
                    [
                        "solarman",
                        "sync",
                        "--plant-id",
                        "X",
                        "--station-id",
                        "ST001",
                        "--db-url",
                        "postgresql://x",
                    ],
                )
                assert result.exit_code == 1

    def test_sync_exception_release_error_exits_1(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        mock_lock = MagicMock()
        from solgreen.db.advisory_lock import LockStatus

        mock_lock.release.return_value = LockStatus.ERROR

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch("solgreen.db.connection.get_connection") as mock_get_conn,
        ):
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            with (
                patch(
                    "solgreen.db.advisory_lock.acquire_sync_lock",
                    return_value=(mock_lock, LockStatus.ACQUIRED),
                ),
                patch(
                    "solgreen.integrations.solarman.sync.sync_solarman_station",
                    side_effect=RuntimeError("sync fail"),
                ),
            ):
                result = runner.invoke(
                    app,
                    [
                        "solarman",
                        "sync",
                        "--plant-id",
                        "X",
                        "--station-id",
                        "ST001",
                        "--db-url",
                        "postgresql://x",
                    ],
                )
                assert result.exit_code == 1

    def test_success_release_error_exits_1(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()
        mock_lock = MagicMock()
        from solgreen.db.advisory_lock import LockStatus

        mock_lock.release.return_value = LockStatus.ERROR

        mock_result = MagicMock()
        mock_result.devices_queried = 1
        mock_result.devices_succeeded = 1
        mock_result.errors = []
        mock_result.not_confirmed_count = 0
        mock_result.snapshots_inserted = 0
        mock_result.snapshots_skipped = 0
        mock_result.normalized_count = 0
        mock_result.not_found_count = 0
        mock_result.error_count = 0

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch("solgreen.db.connection.get_connection") as mock_get_conn,
        ):
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            with (
                patch(
                    "solgreen.db.advisory_lock.acquire_sync_lock",
                    return_value=(mock_lock, LockStatus.ACQUIRED),
                ),
                patch(
                    "solgreen.integrations.solarman.sync.sync_solarman_station",
                    return_value=mock_result,
                ),
            ):
                result = runner.invoke(
                    app,
                    [
                        "solarman",
                        "sync",
                        "--plant-id",
                        "X",
                        "--station-id",
                        "ST001",
                        "--db-url",
                        "postgresql://x",
                    ],
                )
                assert result.exit_code == 1

    def test_json_format_no_secrets(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()

        mock_result = MagicMock()
        mock_result.devices_queried = 0
        mock_result.devices_succeeded = 0
        mock_result.errors = ["list_devices: no stations"]
        mock_result.not_confirmed_count = 0
        mock_result.snapshots_inserted = 0
        mock_result.snapshots_skipped = 0
        mock_result.normalized_count = 0
        mock_result.not_found_count = 0
        mock_result.error_count = 1

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch(
                "solgreen.integrations.solarman.sync.sync_solarman_station",
                return_value=mock_result,
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--dry-run",
                    "--json",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                ],
            )
            output = result.stdout.lower()
            assert "token" not in output
            assert "password" not in output
            assert "secret" not in output

    def test_client_close_after_sync_not_during(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()

        mock_result = MagicMock()
        mock_result.devices_queried = 1
        mock_result.devices_succeeded = 1
        mock_result.errors = []
        mock_result.not_confirmed_count = 0
        mock_result.snapshots_inserted = 5
        mock_result.snapshots_skipped = 0
        mock_result.normalized_count = 5
        mock_result.not_found_count = 0
        mock_result.error_count = 0

        close_called_during_sync = []

        def sync_side_effect(*args, **kwargs):
            close_called_during_sync.append(mock_client.close.call_count)
            return mock_result

        mock_client = MagicMock()
        mock_client.close.side_effect = None

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.client.SolarmanClient",
                return_value=mock_client,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch(
                "solgreen.integrations.solarman.sync.sync_solarman_station",
                side_effect=sync_side_effect,
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                ],
            )
            assert result.exit_code == 0
            assert len(close_called_during_sync) > 0
            assert all(c == 0 for c in close_called_during_sync)
            mock_client.close.assert_called_once()

    def test_sync_json_output_sanitizes_errors(self) -> None:
        import json
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        mock_settings = MagicMock()

        mock_result = MagicMock()
        mock_result.devices_queried = 1
        mock_result.devices_succeeded = 0
        mock_result.errors = [
            "Connection to postgresql://user:secret123@db.example.com:5432 failed",
            "Authentication failed for token=abc123xyz",
            "app_secret=mysecret123 user email=test@test.com station_id=ST001 device_sn=ABC123",
        ]
        mock_result.not_confirmed_count = 0
        mock_result.snapshots_inserted = 0
        mock_result.snapshots_skipped = 0
        mock_result.normalized_count = 0
        mock_result.not_found_count = 0
        mock_result.error_count = 3

        with (
            patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env",
                return_value=mock_settings,
            ),
            patch(
                "solgreen.integrations.solarman.station_resolver.resolve_station",
                return_value=mock_resolved,
            ),
            patch(
                "solgreen.integrations.solarman.sync.sync_solarman_station",
                return_value=mock_result,
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "solarman",
                    "sync",
                    "--json",
                    "--plant-id",
                    "X",
                    "--station-id",
                    "ST001",
                ],
            )
            assert result.exit_code == 1
            output = json.loads(result.stdout)
            assert output["ok"] is False
            assert output["error_count"] == 3
            assert isinstance(output["errors"], list)
            assert len(output["errors"]) == 3

            stdout_lower = result.stdout.lower()
            assert "secret123" not in stdout_lower
            assert "abc123xyz" not in stdout_lower
            assert "mysecret123" not in stdout_lower
            assert "test@test.com" not in stdout_lower
            assert "st001" not in stdout_lower
            assert "abc123" not in stdout_lower
            assert "postgresql://user:secret123@" not in stdout_lower


class TestSyncSkippedLocked:
    def test_skipped_locked_exit_0(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_resolved = MagicMock()
        mock_resolved.station_id = "ST001"
        mock_resolved.masked_id = "ST**"

        with patch("solgreen.db.connection.get_connection") as mock_get_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (False,)
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connection.close = MagicMock()
            mock_get_conn.return_value = mock_connection

            with patch(
                "solgreen.integrations.solarman.settings.build_settings_from_env"
            ) as mock_settings:
                mock_settings.return_value = MagicMock()

                with patch(
                    "solgreen.integrations.solarman.station_resolver.resolve_station",
                    return_value=mock_resolved,
                ):
                    result = runner.invoke(
                        app,
                        [
                            "solarman",
                            "sync",
                            "--plant-id",
                            "X",
                            "--station-id",
                            "ST001",
                            "--db-url",
                            "postgresql://x",
                        ],
                    )

                    assert result.exit_code == 0
