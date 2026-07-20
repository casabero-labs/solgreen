from datetime import UTC, datetime

import pytest

from solgreen.core.time import TimestampParseError, parse_timestamp


def test_parse_timestamp_naive_with_source_tz() -> None:
    original, utc, label = parse_timestamp("2026-07-17 12:35:00", "America/Bogota")
    assert label == "America/Bogota"
    assert original.utcoffset().total_seconds() == -5 * 3600
    assert utc == datetime(2026, 7, 17, 17, 35, tzinfo=UTC)
    assert utc.tzinfo is UTC


def test_parse_timestamp_explicit_utc_zulu() -> None:
    original, utc, label = parse_timestamp("2026-07-17T17:35:00Z", None)
    assert label == "UTC" or label.endswith("UTC")
    assert utc == datetime(2026, 7, 17, 17, 35, tzinfo=UTC)
    assert original.utcoffset().total_seconds() == 0


def test_parse_timestamp_naive_without_source_tz_is_naive() -> None:
    original, utc, label = parse_timestamp("2026-07-17 12:35:00", None)
    assert label == "naive"
    assert original.tzinfo is None
    assert utc == datetime(2026, 7, 17, 12, 35, tzinfo=UTC)


def test_parse_timestamp_invalid_source_tz_falls_back_naive() -> None:
    original, _utc, label = parse_timestamp("2026-07-17 12:35:00", "Mars/Olympus")
    assert label == "naive"
    assert original.tzinfo is None


def test_parse_timestamp_empty_raises() -> None:
    with pytest.raises(TimestampParseError):
        parse_timestamp("", None)
    with pytest.raises(TimestampParseError):
        parse_timestamp("   ", None)


def test_parse_timestamp_whitespace_stripped() -> None:
    _original, utc, _ = parse_timestamp("  2026-07-17 12:35:00  ", "America/Bogota")
    assert utc == datetime(2026, 7, 17, 17, 35, tzinfo=UTC)


def test_parse_timestamp_explicit_offset_wins_over_source_tz() -> None:
    original, utc, _ = parse_timestamp("2026-07-17T17:35:00+00:00", "America/Bogota")
    assert utc == datetime(2026, 7, 17, 17, 35, tzinfo=UTC)
    assert original.utcoffset().total_seconds() == 0
