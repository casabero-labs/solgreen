"""solarman doctor — operational diagnostics without persisting snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from solgreen.integrations.solarman.client import SolarmanClient
from solgreen.integrations.solarman.models import StationInfo
from solgreen.integrations.solarman.settings import SolarmanSettings


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class DoctorCheck:
    name: str
    status: CheckStatus
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
        }
        if self.data:
            result["data"] = {k: v for k, v in self.data.items() if v is not None}
        return result


@dataclass
class DoctorResult:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in self.checks)

    def add(self, name: str, status: CheckStatus, detail: str = "", **data: Any) -> None:
        self.checks.append(DoctorCheck(name=name, status=status, detail=detail, data=data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "checks": [c.to_dict() for c in self.checks],
            "summary": {
                "total": len(self.checks),
                "pass": sum(1 for c in self.checks if c.status == CheckStatus.PASS),
                "warn": sum(1 for c in self.checks if c.status == CheckStatus.WARN),
                "fail": sum(1 for c in self.checks if c.status == CheckStatus.FAIL),
            },
        }


def mask_station_id(station_id: str) -> str:
    """Return a masked version safe for display."""
    if len(station_id) <= 4:
        return (
            station_id[:2] + "**" + station_id[-2:]
            if len(station_id) == 4
            else station_id[:2] + "**"
        )
    return station_id[:2] + "**" + station_id[-2:]


def run_doctor(
    settings: SolarmanSettings,
    station_id: str | None = None,
    db_url: str | None = None,
) -> DoctorResult:
    """Run all doctor checks and return aggregated result."""
    result = DoctorResult()

    _check_configuration(result, settings)
    if not all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in result.checks):
        return result

    _check_authentication(result, settings)
    if not all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in result.checks):
        return result

    conn = None
    client = SolarmanClient(settings)
    try:
        _check_stations(result, client)
        if not all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in result.checks):
            return result

        stations_data = [
            c.data.get("stations", []) for c in result.checks if c.name == "station_list"
        ]
        stations: list[StationInfo] = stations_data[0] if stations_data else []

        resolved = _resolve_station_safe(stations, station_id, result)
        if resolved is None:
            return result

        station_id_str = resolved.station_id
        assert station_id_str is not None

        _check_devices(result, client, station_id_str)
        _check_current_data(result, client, station_id_str)
    finally:
        client.close()

    if db_url:
        conn = _check_database_conn(db_url)
        if conn:
            try:
                _check_migrations_with_conn(result, conn)
            finally:
                conn.close()
    else:
        _check_database(result, None)

    return result


def _resolve_station_safe(
    stations: list[StationInfo], explicit_station_id: str | None, result: DoctorResult
) -> StationInfo | None:
    if explicit_station_id:
        for s in stations:
            if s.station_id == explicit_station_id:
                return s
        result.add(
            "station_resolution",
            CheckStatus.FAIL,
            f"Station '{mask_station_id(explicit_station_id)}' not found in account",
        )
        return None

    if len(stations) == 1:
        result.add("station_resolution", CheckStatus.PASS, "Single station auto-detected")
        return stations[0]

    if len(stations) == 0:
        result.add("station_resolution", CheckStatus.FAIL, "No stations found in account")
        return None

    masked = [mask_station_id(s.station_id or "") for s in stations]
    result.add(
        "station_resolution",
        CheckStatus.FAIL,
        f"Multiple stations ({len(stations)}). Specify one via --station-id or SOLGREEN_SOLARMAN_STATION_ID. Available (masked): {masked}",
    )
    return None


def _check_configuration(result: DoctorResult, settings: SolarmanSettings) -> None:
    try:
        if not settings.solarman_base_url:
            result.add("config", CheckStatus.FAIL, "solarman_base_url is empty")
            return
        if not settings.solarman_app_id:
            result.add("config", CheckStatus.FAIL, "solarman_app_id is missing")
            return
        if not settings.solarman_app_secret:
            result.add("config", CheckStatus.FAIL, "solarman_app_secret is missing")
            return
        if not settings.solarman_email:
            result.add("config", CheckStatus.FAIL, "solarman_email is missing")
            return
        if not settings.solarman_password_sha256:
            result.add("config", CheckStatus.FAIL, "solarman_password_sha256 is missing")
            return
        result.add("config", CheckStatus.PASS, "Configuration valid")
    except Exception as exc:
        result.add("config", CheckStatus.FAIL, f"Configuration error: {exc}")


def _check_authentication(result: DoctorResult, settings: SolarmanSettings) -> None:
    from solgreen.integrations.solarman.auth import SolarmanAuth

    try:
        auth = SolarmanAuth(settings)
        auth.obtain_token()
        result.add("auth", CheckStatus.PASS, "Authentication successful")
    except Exception as exc:
        result.add("auth", CheckStatus.FAIL, f"Authentication failed: {exc}")


def _check_stations(result: DoctorResult, client: SolarmanClient) -> None:
    try:
        stations = client.list_stations()
        result.add(
            "station_list",
            CheckStatus.PASS if stations else CheckStatus.WARN,
            f"Found {len(stations)} station(s)",
            station_count=len(stations),
        )
    except Exception as exc:
        result.add("station_list", CheckStatus.FAIL, f"Failed to list stations: {exc}")


def _check_devices(result: DoctorResult, client: SolarmanClient, station_id: str) -> None:
    try:
        devices = client.list_station_devices(station_id)
        result.add(
            "device_list",
            CheckStatus.PASS if devices else CheckStatus.WARN,
            f"Found {len(devices)} device(s)",
            device_count=len(devices),
        )
    except Exception as exc:
        result.add("device_list", CheckStatus.FAIL, f"Failed to list devices: {exc}")


def _check_current_data(result: DoctorResult, client: SolarmanClient, station_id: str) -> None:
    from solgreen.integrations.solarman.snapshot import SYNC_AUTHORIZED_KEYS

    try:
        devices = client.list_station_devices(station_id)
        if not devices:
            result.add("current_data", CheckStatus.WARN, "No devices to check")
            return

        device_ids = [d.device_id for d in devices if d.device_id]
        has_valid_timestamp = False
        has_required_signals = False
        authorized_unit_errors: list[str] = []
        checked = 0

        for dev_id in device_ids[:5]:
            try:
                data = client.get_device_current_data(dev_id)
                checked += 1
                if data.collection_time and data.collection_time > 0:
                    has_valid_timestamp = True

                data_list = data.data_list or []
                signal_keys = {item.get("key", "") for item in data_list}

                if SYNC_AUTHORIZED_KEYS & signal_keys:
                    has_required_signals = True

                for item in data_list:
                    key = str(item.get("key", ""))
                    unit = str(item.get("unit", "")).strip().upper()
                    if key in SYNC_AUTHORIZED_KEYS and unit and unit not in ("W",):
                        authorized_unit_errors.append(f"{key} has unit '{unit}' (expected W)")

                if has_valid_timestamp and has_required_signals and not authorized_unit_errors:
                    break
            except Exception:
                continue

        if not checked:
            result.add("current_data", CheckStatus.WARN, "Could not check any device")
        elif not has_valid_timestamp:
            result.add("current_data", CheckStatus.FAIL, "Invalid timestamps in current data")
        elif authorized_unit_errors:
            result.add(
                "current_data",
                CheckStatus.FAIL,
                f"Invalid units on authorized signals: {authorized_unit_errors[0]}",
            )
        elif not has_required_signals:
            missing = SYNC_AUTHORIZED_KEYS - signal_keys
            result.add(
                "current_data",
                CheckStatus.WARN,
                f"Missing required signals: {missing}",
            )
        else:
            result.add(
                "current_data",
                CheckStatus.PASS,
                f"Current data valid (checked {checked} device(s))",
            )
    except Exception as exc:
        result.add("current_data", CheckStatus.FAIL, f"Failed to check current data: {exc}")


def _check_database(result: DoctorResult, db_url: str | None) -> None:
    if not db_url:
        result.add("database", CheckStatus.WARN, "No database configured (--no-db mode)")
        return
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        result.add("database", CheckStatus.PASS, "PostgreSQL connection OK")
    except Exception as exc:
        result.add("database", CheckStatus.FAIL, f"Database connection failed: {exc}")


def _check_database_conn(db_url: str) -> Any:
    import psycopg2
    try:
        return psycopg2.connect(db_url)
    except Exception:
        return None


def _check_migrations_with_conn(result: DoctorResult, conn: Any) -> None:
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations')"
        )
        exists = cur.fetchone()[0]
        cur.close()

        if not exists:
            result.add("migrations", CheckStatus.WARN, "schema_migrations table not found")
            return

        from solgreen.db.migrations.runner import get_migration_runner
        runner = get_migration_runner(conn)
        applied, pending = runner.status()
        if pending:
            result.add(
                "migrations",
                CheckStatus.WARN,
                f"{len(pending)} pending migration(s)",
                pending_count=len(pending),
            )
        else:
            result.add(
                "migrations",
                CheckStatus.PASS,
                f"All {len(applied)} migration(s) applied",
                applied_count=len(applied),
            )
    except Exception as exc:
        result.add("migrations", CheckStatus.FAIL, f"Migration check failed: {exc}")
