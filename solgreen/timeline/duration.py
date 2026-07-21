"""Tested ISO-8601 duration parser.

Supports the subset needed for Solgreen tolerance values:

    PT1S          PT30S         PT5M
    PT2M30S       PT1H          PT1H30M
    P1D           P1DT2H        P1DT2H30M
    P1DT2H30M15S  PT0.5S

All durations *strictly positive* (PT0S and P0D are rejected because a
zero-length tolerance causes division by zero in the confidence
function and there is no exact-match workload yet).

Only uppercase, no spaces, no leading sign, no year/month/week.
Returns ``datetime.timedelta`` directly.
"""

from __future__ import annotations

import re
from datetime import timedelta

_ISO_PATTERN = re.compile(
    r"^P"
    r"(?:(\d+)D)?"
    r"(?:T"
    r"(?:(\d+)H)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+)(?:\.(\d+))?S)?"
    r")?$"
)

_SECONDS_PER_HOUR = 3600
_SECONDS_PER_MINUTE = 60
_SECONDS_PER_DAY = 86400


def parse_iso_duration(value: str) -> timedelta:
    if value != value.strip():
        raise ValueError(f"ISO duration must not have leading or trailing whitespace: {value!r}")
    if not value:
        raise ValueError("ISO duration must not be empty")
    if value != value.upper():
        raise ValueError(f"ISO duration must be uppercase: {value!r}")

    match = _ISO_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(
            f"Invalid ISO duration: {value!r}. "
            f"Expected format P[nD][T[nH][nM][n.S]] with at least one component."
        )

    has_component = any(match.group(i) is not None for i in range(1, 5))
    if not has_component:
        raise ValueError(
            f"Invalid ISO duration: {value!r}. At least one D, H, M, or S component is required."
        )

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
    microseconds_str = match.group(5) or "0"

    if len(microseconds_str) > 6:
        raise ValueError(
            f"Fractional seconds precision exceeds maximum of 6 decimal "
            f"digits (microseconds): {value!r}. "
            f"Got {len(microseconds_str)} digits — truncation is not supported."
        )

    microseconds_str = microseconds_str.ljust(6, "0")
    microseconds = int(microseconds_str)

    total_seconds = (
        days * _SECONDS_PER_DAY
        + hours * _SECONDS_PER_HOUR
        + minutes * _SECONDS_PER_MINUTE
        + seconds
    )
    if total_seconds == 0 and microseconds == 0:
        raise ValueError(
            f"Zero-length duration is rejected: {value!r}. "
            f"A tolerance of zero can produce division by zero and is not "
            f"supported. Provide a positive duration."
        )

    return timedelta(seconds=total_seconds, microseconds=microseconds)
