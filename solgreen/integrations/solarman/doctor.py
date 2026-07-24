"""solarman doctor — operational diagnostics without persisting snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from solgreen.integrations.solarman.client import SolarmanClient
from solgreen.integrations.solarman.settings import SolarmanSettings
from solgreen.integrations.solarman.station_resolver import (
    StationResolutionError,
    get_station_from_env,
    resolve_station,
)


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

    client = SolarmanClient(settings)
    try:
        try:
            resolved = resolve_station(
                client,
                explicit_station_id=station_id,
                env_station_id=get_station_from_env(),
            )
            result.add(
                "station_resolution",
                CheckStatus.PASS,
                f"Resolved: {resolved.display}",
                masked_station_id=resolved.display,
            )
        except StationResolutionError as exc:
            result.add("station_resolution", CheckStatus.FAIL, str(exc))
            return result

        _check_devices(result, client, resolved.station_id)
        if not all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in result.checks):
            return result

        _check_current_data(result, client, resolved.station_id)
        if not all(c.status in (CheckStatus.PASS, CheckStatus.WARN) for c in result.checks):
            return result

    finally:
        client.close()

    if db_url:
        _check_database_with_conn(result, db_url)
    else:
        _check_database(result, None)

    return result


def _check_configuration(result: DoctorResult, settings: SolarmanSettings) -> None:
    try:
        if not settings.solarman_base_url:
            result.add("config", CheckStatus.FAIL, "solarman_base_url is missing")
        if not settings.solarman_app_id:
            result.add("config", CheckStatus.FAIL, "solarman_app_id is missing")
        if not settings.solarman_app_secret:
            result.add("config", CheckStatus.FAIL, "solarman_app_secret is missing")
        if not settings.solarman_email:
            result.add("config", CheckStatus.FAIL, "solarman_email is missing")
        if not settings.solarman_password_sha256:
            result.add("config", CheckStatus.FAIL, "solarman_password_sha256 is missing")
        if settings.solarman_base_url and settings.solarman_app_id and settings.solarman_app_secret:
            result.add("config", CheckStatus.PASS, "Configuration valid")
    except Exception as exc:
        result.add("config", CheckStatus.FAIL, f"Configuration error: {exc}")


def _check_authentication(result: DoctorResult, settings: SolarmanSettings) -> None:
    from solgreen.integrations.solarman.auth import SolarmanAuth

    try:
        auth = SolarmanAuth(settings)
        token = auth.get_token()
        if token:
            result.add("auth", CheckStatus.PASS, "Authentication successful")
        else:
            result.add("auth", CheckStatus.FAIL, "Authentication failed: no token returned")
    except Exception as exc:
        result.add("auth", CheckStatus.FAIL, f"Authentication failed: {exc}")


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
                signal_keys = {str(item.get("key", "")) for item in data_list}

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

        if checked == 0:
            result.add(
                "current_data", CheckStatus.FAIL, "Could not fetch current data from any device"
            )
        elif authorized_unit_errors:
            result.add(
                "current_data",
                CheckStatus.FAIL,
                f"Unit errors: {'; '.join(authorized_unit_errors[:3])}",
            )
        elif not has_valid_timestamp:
            result.add("current_data", CheckStatus.WARN, "No valid timestamps in current data")
        elif not has_required_signals:
            result.add(
                "current_data", CheckStatus.WARN, "Required signals not found in current data"
            )
        else:
            result.add(
                "current_data",
                CheckStatus.PASS,
                "Current data valid",
                signals_found=len(SYNC_AUTHORIZED_KEYS & signal_keys),
            )
    except Exception as exc:
        result.add("current_data", CheckStatus.FAIL, f"Failed to check current data: {exc}")


def _check_database(result: DoctorResult, conn: Any) -> None:
    result.add(
        "database",
        CheckStatus.WARN,
        "No database configured; persistence disabled",
        distributed_lock_enabled=False,
    )
    result.add(
        "migrations",
        CheckStatus.WARN,
        "No database configured; migrations not applicable",
    )


def _check_database_with_conn(result: DoctorResult, db_url: str) -> None:
    import psycopg2

    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations')"
        )
        exists = cur.fetchone()[0]
        cur.close()

        if not exists:
            result.add(
                "database",
                CheckStatus.PASS,
                "Database connected; schema_migrations not found",
                distributed_lock_enabled=True,
            )
            result.add("migrations", CheckStatus.WARN, "schema_migrations table not found")
        else:
            result.add(
                "database",
                CheckStatus.PASS,
                "Database connected; migrations table present",
                distributed_lock_enabled=True,
            )
            _check_migrations_with_conn(result, conn)
    except Exception as exc:
        result.add(
            "database",
            CheckStatus.FAIL,
            f"Database connection failed: {exc}",
        )
        result.add("migrations", CheckStatus.FAIL, "Database unavailable")
    finally:
        if conn:
            conn.close()


def _check_migrations_with_conn(result: DoctorResult, conn: Any) -> None:
    try:
        cur = conn.cursor()
        cur.execute("SELECT version, name FROM schema_migrations ORDER BY version")
        rows = cur.fetchall()
        cur.close()
        if rows:
            result.add(
                "migrations",
                CheckStatus.PASS,
                f"{len(rows)} migration(s) applied",
                applied_count=len(rows),
            )
        else:
            result.add("migrations", CheckStatus.WARN, "No migrations applied")
    except Exception as exc:
        result.add("migrations", CheckStatus.FAIL, f"Failed to check migrations: {exc}")
