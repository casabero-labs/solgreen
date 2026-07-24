"""Station resolution with priority: CLI arg > ENV var > autodetection."""

from __future__ import annotations

import os
from dataclasses import dataclass

from solgreen.integrations.solarman.client import SolarmanClient


class StationResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedStation:
    """Resolved station with sanitized display values."""

    station_id: str
    masked_id: str
    station_name: str | None = None

    @property
    def display(self) -> str:
        return self.masked_id


def mask_station_id(station_id: str) -> str:
    """Return a masked version safe for display."""
    if not station_id:
        return "**"
    if len(station_id) <= 4:
        return station_id[:2] + "**"
    return station_id[:2] + "**" + station_id[-2:]


def resolve_station(
    client: SolarmanClient,
    explicit_station_id: str | None,
    env_station_id: str | None,
) -> ResolvedStation:
    """Resolve station ID with priority: explicit > env var > autodetect.

    Raises StationResolutionError if resolution fails.
    """
    target = explicit_station_id or env_station_id

    try:
        stations = client.list_stations()
    except Exception as exc:
        raise StationResolutionError(f"Failed to list stations: {exc}") from exc

    if target:
        for s in stations:
            if s.station_id == target:
                return ResolvedStation(
                    station_id=s.station_id,
                    masked_id=mask_station_id(s.station_id or ""),
                    station_name=s.station_name,
                )
        found = mask_station_id(target)
        raise StationResolutionError(f"Station '{found}' not found in account")

    if len(stations) == 1:
        s = stations[0]
        return ResolvedStation(
            station_id=s.station_id or "",
            masked_id=mask_station_id(s.station_id or ""),
            station_name=s.station_name,
        )

    if len(stations) == 0:
        raise StationResolutionError("No stations found in account")

    masked = [mask_station_id(s.station_id or "") for s in stations]
    raise StationResolutionError(
        f"Multiple stations ({len(stations)}). "
        f"Specify one via --station-id or SOLGREEN_SOLARMAN_STATION_ID. "
        f"Available (masked): {masked}"
    )


def get_station_from_env() -> str | None:
    """Read SOLGREEN_SOLARMAN_STATION_ID from environment."""
    return os.environ.get("SOLGREEN_SOLARMAN_STATION_ID") or None
