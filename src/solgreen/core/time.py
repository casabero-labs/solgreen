from __future__ import annotations

from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil import parser as date_parser

_DEFAULT_TIMEZONE = "UTC"


class TimestampParseError(ValueError):
    pass


def _resolve_zone(name: str) -> ZoneInfo | None:
    name = name.strip()
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return None


def _label_for(tz: tzinfo | None) -> str:
    if tz is None:
        return "naive"
    if isinstance(tz, ZoneInfo):
        return tz.key
    offset = tz.utcoffset(None)
    if offset is None or offset.total_seconds() == 0:
        return "UTC"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def parse_timestamp(
    raw: str,
    source_tz: str | None,
) -> tuple[datetime, datetime, str]:
    if not raw or not raw.strip():
        raise TimestampParseError("empty timestamp")

    raw = raw.strip()
    parsed = date_parser.parse(raw, fuzzy=False)
    explicit_tz = parsed.tzinfo is not None

    if explicit_tz:
        original = parsed
        label = _label_for(parsed.tzinfo)
    else:
        zone = _resolve_zone(source_tz or "") if source_tz else None
        if zone is not None:
            original = parsed.replace(tzinfo=zone)
            label = source_tz or _DEFAULT_TIMEZONE
        else:
            original = parsed
            label = "naive"

    if original.tzinfo is None:
        utc = original.replace(tzinfo=UTC)
    else:
        utc = original.astimezone(UTC).replace(tzinfo=UTC)
    return original, utc, label
