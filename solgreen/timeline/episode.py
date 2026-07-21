from __future__ import annotations

from datetime import datetime, timedelta
from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from solgreen.timeline.canonical import CanonicalSample

SIGNAL_COLUMNS = (
    "flow_potencia_produccion_w",
    "flow_potencia_consumo_w",
    "flow_grid_w",
    "flow_soc_pct",
    "flow_battery_w",
    "telemetry_pv_power_w",
    "telemetry_grid_power_w",
    "telemetry_battery_power_w",
    "telemetry_soc_pct",
)


class CanonicalEpisode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_type: Literal["pv_production", "standby", "grid_injection", "custom"] = Field(
        description="Tipo funcional del episodio derivado de señales."
    )
    start: datetime = Field(description="Timestamp del primer sample del grupo (UTC).")
    end: datetime = Field(description="Timestamp del último sample del grupo (UTC).")
    duration: timedelta = Field(description="Diferencia end - start.")
    sample_count: int = Field(description="Número de muestras en el grupo.")
    coverage_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Porcentaje de muestras con confidence > 0.5 vs total teórico (5min).",
    )
    source_summary: Literal["merged", "flow_only", "telemetry_only", "mixed"] = Field(
        description="Procedencia predominante de las muestras del grupo."
    )
    signals: dict[str, float] = Field(
        default_factory=dict, description="Promedio de señales numéricas no-None en el grupo."
    )


def _derive_episode_type(samples: list[CanonicalSample]) -> str:
    pv_count = 0
    standby_count = 0
    grid_count = 0

    for s in samples:
        has_pv = (
            s.flow_potencia_produccion_w is not None and s.flow_potencia_produccion_w > 0
        ) or (s.telemetry_pv_power_w is not None and s.telemetry_pv_power_w > 0)
        is_standby = (
            s.telemetry_inverter_state is not None
            and s.telemetry_inverter_state.lower()
            in (
                "standby",
                "idle",
                "waiting",
                "fault",
            )
        )
        has_grid = (s.flow_grid_w is not None and s.flow_grid_w > 0) or (
            s.telemetry_grid_power_w is not None and s.telemetry_grid_power_w > 0
        )

        if has_pv:
            pv_count += 1
        elif is_standby:
            standby_count += 1
        elif has_grid:
            grid_count += 1

    total = len(samples)
    if total == 0:
        return "custom"

    if pv_count / total > 0.5:
        return "pv_production"
    if standby_count / total > 0.5:
        return "standby"
    if grid_count / total > 0.5:
        return "grid_injection"
    return "custom"


def _compute_source_summary(samples: list[CanonicalSample]) -> str:
    sources = {s.source for s in samples}
    if sources == {"merged"}:
        return "merged"
    if sources == {"flow"}:
        return "flow_only"
    if sources == {"telemetry"}:
        return "telemetry_only"
    return "mixed"


def _compute_signals_avg(samples: list[CanonicalSample]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for s in samples:
        for col in SIGNAL_COLUMNS:
            val = getattr(s, col)
            if val is not None:
                totals[col] = totals.get(col, 0.0) + float(val)
                counts[col] = counts.get(col, 0) + 1

    return {col: totals[col] / counts[col] for col in totals}


def _compute_coverage(samples: list[CanonicalSample], duration: timedelta) -> float:
    if duration.total_seconds() <= 0:
        return 100.0 if samples[0].confidence > 0.5 else 0.0
    total_theoretical = int(duration.total_seconds() / 300) + 1
    high_conf = sum(1 for s in samples if s.confidence > 0.5)
    return min(100.0, (high_conf / total_theoretical) * 100.0)


def build_episodes(
    timeline: list[CanonicalSample],
    *,
    min_gap: timedelta = timedelta(minutes=10),
    min_samples: int = 2,
) -> list[CanonicalEpisode]:
    if not timeline:
        return []

    sorted_ts = sorted(timeline, key=lambda s: s.timestamp_axis)
    episodes: list[CanonicalEpisode] = []
    current_group: list[CanonicalSample] = [sorted_ts[0]]

    for prev, curr in pairwise(sorted_ts):
        gap = curr.timestamp_axis - prev.timestamp_axis
        if gap > min_gap:
            ep = _build_one_episode(current_group, min_samples)
            if ep is not None:
                episodes.append(ep)
            current_group = [curr]
        else:
            current_group.append(curr)

    ep = _build_one_episode(current_group, min_samples)
    if ep is not None:
        episodes.append(ep)

    return episodes


def _build_one_episode(
    samples: list[CanonicalSample],
    min_samples: int,
) -> CanonicalEpisode | None:
    if len(samples) < min_samples:
        return None

    start = samples[0].timestamp_axis
    end = samples[-1].timestamp_axis
    duration = end - start

    return CanonicalEpisode(
        episode_type=_derive_episode_type(samples),
        start=start,
        end=end,
        duration=duration,
        sample_count=len(samples),
        coverage_pct=_compute_coverage(samples, duration),
        source_summary=_compute_source_summary(samples),
        signals=_compute_signals_avg(samples),
    )
