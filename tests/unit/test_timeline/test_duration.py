from __future__ import annotations

from datetime import timedelta

import pytest

from solgreen.timeline.duration import parse_iso_duration


class TestValidDurations:
    def test_pt1s(self) -> None:
        assert parse_iso_duration("PT1S") == timedelta(seconds=1)

    def test_pt30s(self) -> None:
        assert parse_iso_duration("PT30S") == timedelta(seconds=30)

    def test_pt5m(self) -> None:
        assert parse_iso_duration("PT5M") == timedelta(minutes=5)

    def test_pt2m30s(self) -> None:
        assert parse_iso_duration("PT2M30S") == timedelta(minutes=2, seconds=30)

    def test_pt1h(self) -> None:
        assert parse_iso_duration("PT1H") == timedelta(hours=1)

    def test_pt1h30m(self) -> None:
        assert parse_iso_duration("PT1H30M") == timedelta(hours=1, minutes=30)

    def test_p1d(self) -> None:
        assert parse_iso_duration("P1D") == timedelta(days=1)

    def test_p1dt2h30m15s(self) -> None:
        expected = timedelta(days=1, hours=2, minutes=30, seconds=15)
        assert parse_iso_duration("P1DT2H30M15S") == expected

    def test_pt0_5s_fractional(self) -> None:
        assert parse_iso_duration("PT0.5S") == timedelta(milliseconds=500)

    def test_microsecond_precision(self) -> None:
        result = parse_iso_duration("PT0.000001S")
        assert result == timedelta(microseconds=1)

    def test_fractional_seconds_with_minutes(self) -> None:
        result = parse_iso_duration("PT5M0.1S")
        expected = timedelta(minutes=5, microseconds=100000)
        assert result == expected


class TestRejectedDurations:
    def test_empty_string(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_iso_duration("")

    def test_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="whitespace"):
            parse_iso_duration("   ")

    def test_p_only(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("P")

    def test_pt_only(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("PT")

    def test_pt0s_zero_length(self) -> None:
        with pytest.raises(ValueError, match="Zero-length"):
            parse_iso_duration("PT0S")

    def test_p0d_zero_length(self) -> None:
        with pytest.raises(ValueError, match="Zero-length"):
            parse_iso_duration("P0D")

    def test_negative_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("-PT5M")

    def test_negative_days_syntax(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("P-1D")

    def test_years_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("P1Y")

    def test_months_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("P1M")

    def test_weeks_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("P1W")

    def test_human_format_5m(self) -> None:
        with pytest.raises(ValueError, match="uppercase"):
            parse_iso_duration("5m")

    def test_garbage_suffix(self) -> None:
        with pytest.raises(ValueError, match="uppercase"):
            parse_iso_duration("PT5Mgarbage")

    def test_lowercase_rejected(self) -> None:
        with pytest.raises(ValueError, match="uppercase"):
            parse_iso_duration("pt5m")

    def test_none_type_validation(self) -> None:
        with pytest.raises((TypeError, AttributeError)):
            parse_iso_duration(None)  # type: ignore[arg-type]

    def test_leading_whitespace_rejected(self) -> None:
        with pytest.raises(ValueError, match="whitespace"):
            parse_iso_duration(" PT5M")

    def test_empty_days_component(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            parse_iso_duration("PD")

    def test_pt0_123456s_max_precision(self) -> None:
        result = parse_iso_duration("PT0.123456S")
        assert result == timedelta(microseconds=123456)

    def test_pt0_1234567s_exceeds_max_precision(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum"):
            parse_iso_duration("PT0.1234567S")

    def test_precision_message_mentions_max_digits(self) -> None:
        with pytest.raises(ValueError, match="6 decimal"):
            parse_iso_duration("PT0.1234567S")

    def test_no_silent_truncation(self) -> None:
        result = parse_iso_duration("PT0.123456S")
        assert result.microseconds == 123456


class TestDeterminismAndPurity:
    def test_repeated_call_identical(self) -> None:
        for _ in range(3):
            assert parse_iso_duration("PT5M") == timedelta(minutes=5)

    def test_no_state_mutation(self) -> None:
        a = parse_iso_duration("PT1H")
        b = parse_iso_duration("PT2M")
        assert a == timedelta(hours=1)
        assert b == timedelta(minutes=2)

    def test_returns_timedelta_instance(self) -> None:
        result = parse_iso_duration("PT1S")
        assert isinstance(result, timedelta)

    def test_error_message_is_useful(self) -> None:
        with pytest.raises(ValueError, match="5m"):
            parse_iso_duration("5m")
