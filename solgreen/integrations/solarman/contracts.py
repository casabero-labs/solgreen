"""Historical data query contracts for SOLARMAN API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HistoricalQuery:
    """Immutable contract for a historical data query."""

    device_id: str
    station_id: str
    start_time: datetime
    end_time: datetime
    time_zone: str = "America/Bogota"

    def __post_init__(self) -> None:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

    def start_iso(self) -> str:
        return self.start_time.isoformat()

    def end_iso(self) -> str:
        return self.end_time.isoformat()
