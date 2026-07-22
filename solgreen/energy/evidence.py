"""
Pure analytical functions for sign-evidence analysis.

These functions operate on already-parsed data (lists of floats,
timestamps, dicts) and do NOT access files, secrets, or serials.
They are safe to import in public tests and to use from private analysis scripts.

All functions are side-effect-free and deterministic given the same inputs.
"""

from __future__ import annotations

import hashlib
import io
import statistics
from datetime import datetime
from typing import Any

SIGN_ZERO_DEADBAND_W = 5.0


def classify_power_value(
    raw_value: float,
    zero_deadband_w: float = 0.0,
) -> tuple[float, str, str]:
    """
    Classify a raw power value using a symmetric deadband.

    Returns (normalized_value, classification, reason) where:
    - normalized_value: the raw value (never modified)
    - classification: "positive" | "negative" | "zero"
    - reason: "positive_outside_deadband" | "negative_outside_deadband" | "within_zero_deadband"

    The raw value is NEVER modified — only classified.
    """
    if raw_value > zero_deadband_w:
        return (raw_value, "positive", "positive_outside_deadband")
    elif raw_value < -zero_deadband_w:
        return (raw_value, "negative", "negative_outside_deadband")
    else:
        return (raw_value, "zero", "within_zero_deadband")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def safe_stats(values: list[float]) -> dict[str, float | None]:
    """Compute min, max, median, mean, and count for a list of values."""
    if not values:
        return {"min": None, "max": None, "median": None, "mean": None, "count": 0}
    return {
        "min": min(values),
        "max": max(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "count": len(values),
    }


# ---------------------------------------------------------------------------
# Directional split
# ---------------------------------------------------------------------------


def directional_split(
    values: list[float],
    *,
    zero_deadband_w: float = 0.0,
) -> dict[str, Any]:
    """
    Separate values into positive, negative, and zero groups with stats.

    When zero_deadband_w > 0, values in [-deadband, +deadband] are classified as zero.
    Raw values are never modified; classification is based on the deadband threshold.
    """
    pos: list[float] = []
    neg: list[float] = []
    zero: list[float] = []
    for v in values:
        classification = classify_power_value(v, zero_deadband_w)
        bucket = classification[1]
        if bucket == "positive":
            pos.append(v)
        elif bucket == "negative":
            neg.append(v)
        else:
            zero.append(v)
    return {
        "positive": safe_stats(pos),
        "negative": safe_stats(neg),
        "zero_count": len(zero),
        "deadband_applied_w": zero_deadband_w,
    }


# ---------------------------------------------------------------------------
# Sign consistency
# ---------------------------------------------------------------------------


def sign_consistency(values: list[float]) -> float:
    """
    Fraction of non-zero values sharing the dominant sign.

    Returns 1.0 when all non-zero values share the same sign.
    Returns 0.5 when split evenly.
    Returns 0.0 when no non-zero values.
    """
    non_zero = [v for v in values if v != 0.0]
    if not non_zero:
        return 0.0
    pos = sum(1 for v in non_zero if v > 0)
    neg = len(non_zero) - pos
    return max(pos, neg) / len(non_zero)


# ---------------------------------------------------------------------------
# Episode detection
# ---------------------------------------------------------------------------


def detect_episodes(
    timestamped_values: list[tuple[datetime, float]],
    *,
    min_consecutive: int = 2,
    zero_deadband_w: float = 0.0,
) -> list[dict[str, Any]]:
    """
    Group consecutive same-sign values into episodes.

    Each timestamped_value is a (datetime, float) pair.
    Only episodes with at least `min_consecutive` samples are returned.
    Episodes with sign=zero are excluded.

    When zero_deadband_w > 0, values in [-deadband, +deadband] are classified
    as zero and cannot start episodes. Raw values are never modified.

    Returns list of dicts with:
        direction, start_iso, end_iso, duration_samples,
        magnitude_min, magnitude_max, magnitude_median, sign_consistency,
        deadband_applied_w
    """
    if len(timestamped_values) < min_consecutive:
        return []

    episodes: list[dict[str, Any]] = []
    current_dir: str | None = None
    current_start: datetime | None = None
    current_end: datetime | None = None
    current_values: list[float] = []

    for ts, val in timestamped_values:
        _, direction, _ = classify_power_value(val, zero_deadband_w)

        if direction != current_dir:
            if (
                current_dir is not None
                and current_dir != "zero"
                and len(current_values) >= min_consecutive
            ):
                episodes.append(
                    _build_episode(
                        current_dir, current_values, current_start, current_end, zero_deadband_w
                    )
                )
            current_dir = direction
            current_start = ts
            current_end = ts
            current_values = [val]
        else:
            current_end = ts
            current_values.append(val)

    if current_dir is not None and current_dir != "zero" and len(current_values) >= min_consecutive:
        assert current_start is not None
        assert current_end is not None
        episodes.append(
            _build_episode(current_dir, current_values, current_start, current_end, zero_deadband_w)
        )

    return episodes


def _build_episode(
    direction: str,
    values: list[float],
    start: datetime | None,
    end: datetime | None,
    deadband_applied_w: float = 0.0,
) -> dict[str, Any]:
    abs_vals = [abs(v) for v in values]
    return {
        "direction": direction,
        "start_iso": start.isoformat() if start else None,
        "end_iso": end.isoformat() if end else None,
        "duration_samples": len(values),
        "magnitude_min": round(min(abs_vals), 2),
        "magnitude_max": round(max(abs_vals), 2),
        "magnitude_median": round(statistics.median(abs_vals), 2),
        "sign_consistency": sign_consistency(values),
        "deadband_applied_w": deadband_applied_w,
    }


# ---------------------------------------------------------------------------
# SOC trend analysis
# ---------------------------------------------------------------------------


def soc_trend(
    telemetry_values: list[tuple[datetime, float | None, float | None]],
) -> list[dict[str, Any]]:
    """
    Compute SOC trend across consecutive telemetry samples.

    Each tuple: (timestamp_utc, soc_pct, battery_power_w).
    All values may be None.
    """
    trend: list[dict[str, Any]] = []
    if len(telemetry_values) < 2:
        return trend

    sorted_vals = sorted(telemetry_values, key=lambda t: t[0])
    prev_ts, prev_soc, prev_power = sorted_vals[0]

    for ts, soc, power in sorted_vals[1:]:
        if prev_soc is not None and soc is not None:
            delta = soc - prev_soc
            trend.append(
                {
                    "from_iso": prev_ts.isoformat(),
                    "to_iso": ts.isoformat(),
                    "soc_delta_pct": round(delta, 2),
                    "battery_power_w": prev_power,
                    "direction": "charging"
                    if delta > 0
                    else "discharging"
                    if delta < 0
                    else "flat",
                }
            )
        prev_ts, prev_soc, prev_power = ts, soc, power

    return trend


# ---------------------------------------------------------------------------
# Cumulative energy delta
# ---------------------------------------------------------------------------


def cumulative_delta(
    timestamped_values: list[tuple[datetime, float | None]],
) -> float | None:
    """
    Compute delta between first and last non-None cumulative value.

    Useful for detecting which direction a cumulative tracker is moving.
    """
    sorted_vals = sorted(timestamped_values, key=lambda t: t[0])
    first_val: float | None = None
    last_val: float | None = None

    for _, val in sorted_vals:
        if val is not None:
            if first_val is None:
                first_val = val
            last_val = val

    if first_val is not None and last_val is not None:
        return last_val - first_val
    return None


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def value_hash(values: list[float]) -> str:
    """Deterministic SHA-256 of a list of float values (6 decimal places)."""
    buf = io.BytesIO()
    for v in values:
        buf.write(f"{v:.6f}\n".encode())
    return hashlib.sha256(buf.getvalue()).hexdigest()


def file_sha256(path_bytes: bytes) -> str:
    """Deterministic SHA-256 of raw file bytes."""
    return hashlib.sha256(path_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Decision outcome types and helpers
# ---------------------------------------------------------------------------

DecisionOutcome = (
    str  # confirmed | provisional | insufficient_evidence | contradicted | not_assessed
)


def decide_signed_signal(
    pos_episodes: int = 0,
    neg_episodes: int = 0,
    contradictions: int = 0,
    has_state_signals: bool = False,
    *,
    requires_both_directions: bool = True,
) -> tuple[DecisionOutcome, str, str]:
    """Determine evidence decision for signed (bidirectional) signals like battery and grid."""
    if contradictions > 0:
        return "contradicted", f"{contradictions} sign contradiction(s) found", "high"

    if pos_episodes == 0 and neg_episodes == 0:
        return "insufficient_evidence", "no directional episodes detected", "low"

    if requires_both_directions:
        if pos_episodes > 0 and neg_episodes > 0:
            if has_state_signals:
                return (
                    "provisional",
                    f"both directions ({pos_episodes}+, {neg_episodes}-) with state signals",
                    "high",
                )
            return "provisional", f"both directions ({pos_episodes}+, {neg_episodes}-)", "medium"
        elif pos_episodes > 0:
            return (
                "insufficient_evidence",
                f"only positive direction ({pos_episodes} episodes)",
                "low",
            )
        elif neg_episodes > 0:
            return (
                "insufficient_evidence",
                f"only negative direction ({neg_episodes} episodes)",
                "low",
            )
    else:
        if pos_episodes > 0 or neg_episodes > 0:
            return (
                "provisional",
                f"{pos_episodes}+ positive, {neg_episodes}- negative episodes",
                "medium",
            )

    return "not_assessed", "no decision criteria met", "low"


def decide_unsigned_signal(
    positive_count: int = 0,
    negative_count: int = 0,
    positive_episodes: int = 0,
    *,
    signal_name: str = "unknown",
) -> tuple[DecisionOutcome, str, str]:
    """Determine evidence decision for unsigned signals like PV and load."""
    if negative_count > 0:
        return "contradicted", f"{negative_count} negative values in unsigned signal", "high"
    if positive_episodes > 0:
        if signal_name == "load":
            return (
                "confirmed_after_deadband_validation",
                f"{positive_episodes} positive episodes, no negatives outside deadband",
                "high",
            )
        return (
            "provisional",
            f"{positive_episodes} positive episodes, {negative_count} negatives",
            "medium",
        )
    return "not_assessed", "no episodes or values to assess", "low"


# ---------------------------------------------------------------------------
# Cross-signal verification (forbidden as primary, allowed as secondary)
# ---------------------------------------------------------------------------


def energy_balance_check(
    production_w: float | None,
    consumption_w: float | None,
    grid_w: float | None,
    battery_w: float | None,
    tolerance: float = 0.01,
) -> dict[str, Any]:
    """
    Secondary consistency check: production ≈ consumption + grid + battery.

    This MUST NOT be used as primary evidence for sign convention decisions.
    It is a sanity check only and may fail during transients or measurement lag.
    """
    prod = production_w if production_w is not None else 0.0
    cons = consumption_w if consumption_w is not None else 0.0
    grd = grid_w if grid_w is not None else 0.0
    bat = battery_w if battery_w is not None else 0.0

    lhs = prod
    rhs = cons + grd + bat
    error = lhs - rhs

    return {
        "production_w": round(prod, 2),
        "consumption_w": round(cons, 2),
        "grid_w": round(grd, 2),
        "battery_w": round(bat, 2),
        "error_w": round(error, 2),
        "within_tolerance": abs(error) <= tolerance * max(1.0, abs(lhs), abs(rhs)),
        "note": "SECONDARY CHECK ONLY — not primary evidence for sign convention",
    }
