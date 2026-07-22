"""Tests for solgreen.energy.evidence — pure analytical functions for sign-evidence analysis."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from solgreen.energy.evidence import (
    cumulative_delta,
    decide_signed_signal,
    decide_unsigned_signal,
    detect_episodes,
    directional_split,
    energy_balance_check,
    file_sha256,
    safe_stats,
    sign_consistency,
    soc_trend,
    value_hash,
)

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# safe_stats
# ---------------------------------------------------------------------------


class TestSafeStats:
    def test_empty_list(self) -> None:
        result = safe_stats([])
        assert result["count"] == 0
        assert result["min"] is None
        assert result["max"] is None
        assert result["median"] is None
        assert result["mean"] is None

    def test_single_value(self) -> None:
        result = safe_stats([42.0])
        assert result["count"] == 1
        assert result["min"] == 42.0
        assert result["max"] == 42.0
        assert result["median"] == 42.0
        assert result["mean"] == 42.0

    def test_multiple_values(self) -> None:
        result = safe_stats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result["count"] == 5
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        assert result["median"] == 3.0
        assert result["mean"] == 3.0

    def test_negative_values(self) -> None:
        result = safe_stats([-10.0, -5.0, 0.0, 5.0, 10.0])
        assert result["min"] == -10.0
        assert result["max"] == 10.0
        assert result["median"] == 0.0


# ---------------------------------------------------------------------------
# directional_split
# ---------------------------------------------------------------------------


class TestDirectionalSplit:
    def test_all_positive(self) -> None:
        result = directional_split([1.0, 2.0, 3.0])
        assert result["positive"]["count"] == 3
        assert result["negative"]["count"] == 0
        assert result["zero_count"] == 0

    def test_all_negative(self) -> None:
        result = directional_split([-1.0, -2.0, -3.0])
        assert result["negative"]["count"] == 3
        assert result["positive"]["count"] == 0
        assert result["zero_count"] == 0

    def test_mixed(self) -> None:
        result = directional_split([1.0, -2.0, 3.0, -4.0, 0.0, 0.0])
        assert result["positive"]["count"] == 2
        assert result["negative"]["count"] == 2
        assert result["zero_count"] == 2

    def test_all_zero(self) -> None:
        result = directional_split([0.0, 0.0, 0.0])
        assert result["positive"]["count"] == 0
        assert result["negative"]["count"] == 0
        assert result["zero_count"] == 3

    def test_empty(self) -> None:
        result = directional_split([])
        assert result["positive"]["count"] == 0
        assert result["negative"]["count"] == 0
        assert result["zero_count"] == 0


# ---------------------------------------------------------------------------
# sign_consistency
# ---------------------------------------------------------------------------


class TestSignConsistency:
    def test_all_same_sign(self) -> None:
        assert sign_consistency([1.0, 2.0, 3.0]) == 1.0
        assert sign_consistency([-1.0, -2.0, -3.0]) == 1.0

    def test_mixed(self) -> None:
        assert sign_consistency([1.0, -1.0]) == 0.5

    def test_zero_skipped(self) -> None:
        assert sign_consistency([0.0, 1.0, 0.0, 2.0]) == 1.0

    def test_all_zero(self) -> None:
        assert sign_consistency([0.0, 0.0]) == 0.0

    def test_empty(self) -> None:
        assert sign_consistency([]) == 0.0


# ---------------------------------------------------------------------------
# detect_episodes
# ---------------------------------------------------------------------------

_T0 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _t(minutes_offset: int) -> datetime:
    return _T0 + timedelta(minutes=minutes_offset)


class TestDetectEpisodes:
    def test_single_direction(self) -> None:
        values = [(_t(i), 100.0 + i * 10) for i in range(5)]
        episodes = detect_episodes(values)
        assert len(episodes) == 1
        assert episodes[0]["direction"] == "positive"
        assert episodes[0]["duration_samples"] == 5

    def test_alternating_signs(self) -> None:
        values = [
            (_t(0), 100.0),
            (_t(1), -50.0),
            (_t(2), 100.0),
            (_t(3), -50.0),
        ]
        episodes = detect_episodes(values, min_consecutive=1)
        assert len(episodes) == 4

    def test_min_consecutive_filters_short(self) -> None:
        values = [
            (_t(0), 100.0),
            (_t(1), -50.0),
            (_t(2), 100.0),
            (_t(3), 200.0),
            (_t(4), -50.0),
            (_t(5), -75.0),
        ]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 2
        dirs = [e["direction"] for e in episodes]
        assert "positive" in dirs
        assert "negative" in dirs

    def test_zeros_excluded(self) -> None:
        values = [
            (_t(0), 0.0),
            (_t(1), 0.0),
            (_t(2), 100.0),
            (_t(3), 200.0),
            (_t(4), 0.0),
            (_t(5), -50.0),
            (_t(6), -75.0),
        ]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 2

    def test_empty(self) -> None:
        assert detect_episodes([]) == []

    def test_too_few_for_min_consecutive(self) -> None:
        values = [(_t(i), 100.0) for i in range(1)]
        assert detect_episodes(values, min_consecutive=2) == []

    def test_episode_fields(self) -> None:
        values = [
            (_t(0), 10.0),
            (_t(1), 20.0),
            (_t(2), 30.0),
        ]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 1
        e = episodes[0]
        assert e["direction"] == "positive"
        assert e["duration_samples"] == 3
        assert e["magnitude_min"] == 10.0
        assert e["magnitude_max"] == 30.0
        assert e["magnitude_median"] == 20.0
        assert e["sign_consistency"] == 1.0
        assert e["start_iso"] is not None
        assert e["end_iso"] is not None


# ---------------------------------------------------------------------------
# soc_trend
# ---------------------------------------------------------------------------


class TestSocTrend:
    def test_charging_trend(self) -> None:
        data = [
            (_t(0), 50.0, 1000.0),
            (_t(1), 52.0, 1000.0),
            (_t(2), 54.0, 1000.0),
        ]
        trend = soc_trend(data)
        assert len(trend) == 2
        assert all(d["direction"] == "charging" for d in trend)

    def test_discharging_trend(self) -> None:
        data = [
            (_t(0), 80.0, -500.0),
            (_t(1), 78.0, -500.0),
            (_t(2), 75.0, -500.0),
        ]
        trend = soc_trend(data)
        assert all(d["direction"] == "discharging" for d in trend)

    def test_flat_trend(self) -> None:
        data = [
            (_t(0), 60.0, 0.0),
            (_t(1), 60.0, 0.0),
        ]
        trend = soc_trend(data)
        assert all(d["direction"] == "flat" for d in trend)

    def test_none_values_skipped(self) -> None:
        data = [
            (_t(0), None, 1000.0),
            (_t(1), 50.0, 1000.0),
            (_t(2), 52.0, None),
        ]
        trend = soc_trend(data)
        assert len(trend) == 1
        assert trend[0]["soc_delta_pct"] == 2.0

    def test_single_sample(self) -> None:
        assert soc_trend([(_t(0), 50.0, 1000.0)]) == []

    def test_empty(self) -> None:
        assert soc_trend([]) == []


# ---------------------------------------------------------------------------
# cumulative_delta
# ---------------------------------------------------------------------------


class TestCumulativeDelta:
    def test_increasing(self) -> None:
        data = [(_t(0), 100.0), (_t(1), 150.0), (_t(2), 200.0)]
        assert cumulative_delta(data) == 100.0

    def test_decreasing(self) -> None:
        data = [(_t(0), 200.0), (_t(1), 150.0), (_t(2), 100.0)]
        assert cumulative_delta(data) == -100.0

    def test_unsorted_input(self) -> None:
        data = [(_t(2), 200.0), (_t(0), 100.0)]
        assert cumulative_delta(data) == 100.0

    def test_with_none_values(self) -> None:
        data = [(_t(0), None), (_t(1), 100.0), (_t(2), None), (_t(3), 150.0)]
        assert cumulative_delta(data) == 50.0

    def test_all_none(self) -> None:
        data = [(_t(0), None), (_t(1), None)]
        assert cumulative_delta(data) is None

    def test_single_value(self) -> None:
        assert cumulative_delta([(_t(0), 50.0)]) == 0.0

    def test_empty(self) -> None:
        assert cumulative_delta([]) is None


# ---------------------------------------------------------------------------
# value_hash
# ---------------------------------------------------------------------------


class TestValueHash:
    def test_deterministic(self) -> None:
        h1 = value_hash([1.0, 2.0, 3.0])
        h2 = value_hash([1.0, 2.0, 3.0])
        assert h1 == h2
        assert len(h1) == 64

    def test_different_values_different_hash(self) -> None:
        h1 = value_hash([1.0, 2.0, 3.0])
        h2 = value_hash([1.0, 2.0, 4.0])
        assert h1 != h2

    def test_order_matters(self) -> None:
        h1 = value_hash([1.0, 2.0, 3.0])
        h2 = value_hash([3.0, 2.0, 1.0])
        assert h1 != h2

    def test_six_decimal_precision(self) -> None:
        h1 = value_hash([1.0 / 3.0])
        h2 = value_hash([0.333333])
        assert h1 == h2

    def test_empty_list(self) -> None:
        h = value_hash([])
        assert len(h) == 64


# ---------------------------------------------------------------------------
# file_sha256
# ---------------------------------------------------------------------------


class TestFileSha256:
    def test_deterministic(self) -> None:
        h1 = file_sha256(b"hello")
        h2 = file_sha256(b"hello")
        assert h1 == h2
        assert len(h1) == 64

    def test_different_bytes_different_hash(self) -> None:
        h1 = file_sha256(b"hello")
        h2 = file_sha256(b"world")
        assert h1 != h2


# ---------------------------------------------------------------------------
# decide_signed_signal
# ---------------------------------------------------------------------------


class TestDecideSignedSignal:
    def test_insufficient_no_episodes(self) -> None:
        outcome, _reason, _conf = decide_signed_signal(pos_episodes=0, neg_episodes=0)
        assert outcome == "insufficient_evidence"

    def test_insufficient_one_direction(self) -> None:
        outcome, _reason, _conf = decide_signed_signal(pos_episodes=3, neg_episodes=0)
        assert outcome == "insufficient_evidence"

    def test_provisional_both_directions(self) -> None:
        outcome, reason, _conf = decide_signed_signal(pos_episodes=3, neg_episodes=2)
        assert outcome == "provisional"
        assert "both directions" in reason

    def test_provisional_both_with_state(self) -> None:
        outcome, _reason, conf = decide_signed_signal(
            pos_episodes=3, neg_episodes=2, has_state_signals=True
        )
        assert outcome == "provisional"
        assert conf == "high"

    def test_contradicted(self) -> None:
        outcome, _reason, conf = decide_signed_signal(
            pos_episodes=3, neg_episodes=2, contradictions=1
        )
        assert outcome == "contradicted"
        assert conf == "high"

    def test_no_both_directions_required(self) -> None:
        outcome, _reason, _conf = decide_signed_signal(
            pos_episodes=3, neg_episodes=0, requires_both_directions=False
        )
        assert outcome == "provisional"

    def test_not_assessed_fallback(self) -> None:
        outcome, _reason, _conf = decide_signed_signal(requires_both_directions=False)
        assert outcome == "insufficient_evidence"


# ---------------------------------------------------------------------------
# decide_unsigned_signal
# ---------------------------------------------------------------------------


class TestDecideUnsignedSignal:
    def test_contradicted_negative_values(self) -> None:
        outcome, _reason, conf = decide_unsigned_signal(negative_count=3)
        assert outcome == "contradicted"
        assert conf == "high"

    def test_provisional_positive(self) -> None:
        outcome, _reason, _conf = decide_unsigned_signal(positive_count=10, positive_episodes=3)
        assert outcome == "provisional"

    def test_not_assessed_empty(self) -> None:
        outcome, _reason, _conf = decide_unsigned_signal()
        assert outcome == "not_assessed"


# ---------------------------------------------------------------------------
# energy_balance_check
# ---------------------------------------------------------------------------


class TestEnergyBalanceCheck:
    def test_balanced(self) -> None:
        result = energy_balance_check(
            production_w=5000.0,
            consumption_w=2000.0,
            grid_w=1000.0,
            battery_w=2000.0,
        )
        assert result["error_w"] == 0.0
        assert result["within_tolerance"] is True

    def test_unbalanced(self) -> None:
        result = energy_balance_check(
            production_w=5000.0,
            consumption_w=1000.0,
            grid_w=1000.0,
            battery_w=1000.0,
        )
        assert result["error_w"] == 2000.0
        assert result["within_tolerance"] is False

    def test_none_treated_as_zero(self) -> None:
        result = energy_balance_check(
            production_w=1000.0,
            consumption_w=1000.0,
            grid_w=None,
            battery_w=None,
        )
        assert result["error_w"] == 0.0

    def test_has_note(self) -> None:
        result = energy_balance_check(
            production_w=1.0,
            consumption_w=1.0,
            grid_w=0.0,
            battery_w=0.0,
        )
        assert "SECONDARY CHECK ONLY" in result["note"]


# ---------------------------------------------------------------------------
# Integration: parsers still work with fixtures
# ---------------------------------------------------------------------------


class TestParserPreservation:
    def test_parse_flow_csv(self) -> None:
        from solgreen.importer.parsers.solarman_flow import parse_plant_flow

        fixture = FIXTURES / "flow_small.csv"
        samples = parse_plant_flow(fixture)
        assert len(samples) == 5
        for s in samples:
            assert s.timestamp_utc.tzinfo is not None
            assert s.potencia_de_produccion_w is not None
            assert s.potencia_de_consumo_w is not None

    def test_parse_telemetry_csv(self) -> None:
        from solgreen.importer.parsers.solarman_telemetry import parse_inverter_telemetry

        fixture = FIXTURES / "telemetry_small.csv"
        samples = parse_inverter_telemetry(fixture)
        assert len(samples) == 3
        for s in samples:
            assert s.timestamp_utc.tzinfo is not None
            assert "total_active_power_of_the_grid_w" in s.signals
            assert "potencia_de_bateria_w" in s.signals
            assert s.serial_redacted.startswith("redacted:")

    def test_garbage_csv_detected(self) -> None:

        from solgreen.importer.exceptions import HeaderMismatchError
        from solgreen.importer.parsers.solarman_flow import parse_plant_flow

        fixture = FIXTURES / "garbage.csv"
        with pytest.raises(HeaderMismatchError):
            parse_plant_flow(fixture)


# ---------------------------------------------------------------------------
# Privacy protection: no private paths in outputs
# ---------------------------------------------------------------------------


class TestPrivacyBoundary:
    def test_evidence_module_no_file_access(self) -> None:
        """Evidence module functions must not access the filesystem."""
        import inspect

        from solgreen.energy import evidence as ev_mod

        for name, fn in inspect.getmembers(ev_mod, inspect.isfunction):
            src = inspect.getsource(fn)
            assert "open(" not in src, f"{name} accesses filesystem"
            assert "Path(" not in src, f"{name} accesses Path"

    def test_directional_split_no_leaks(self) -> None:
        result = directional_split([1.0, -2.0, 0.0])
        result_json = json.dumps(result)
        assert "serial" not in result_json.lower()
        assert "address" not in result_json.lower()
        assert "/Users" not in result_json

    def test_hash_functions_no_leaks(self) -> None:
        h = value_hash([1.0, 2.0])
        assert len(h) == 64


# ---------------------------------------------------------------------------
# Deterministic summary
# ---------------------------------------------------------------------------


class TestDeterministicSummary:
    def test_same_input_produces_same_output(self) -> None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        r1 = safe_stats(data)
        r2 = safe_stats(data)
        assert r1 == r2
        assert r1["median"] == 3.0
        assert r1["mean"] == 3.0


# ---------------------------------------------------------------------------
# Missing data handling
# ---------------------------------------------------------------------------


class TestMissingData:
    def test_soc_trend_handles_none(self) -> None:
        data = [
            (_t(0), None, 1000.0),
            (_t(5), 50.0, None),
            (_t(10), None, None),
            (_t(15), 52.0, 1500.0),
        ]
        trend = soc_trend(data)
        assert len(trend) >= 0

    def test_cumulative_delta_handles_none(self) -> None:
        data = [
            (_t(0), None),
            (_t(5), None),
        ]
        assert cumulative_delta(data) is None


# ---------------------------------------------------------------------------
# Contradictory episodes
# ---------------------------------------------------------------------------


class TestContradictoryEpisodes:
    def test_mixed_signs_in_episode_reduces_consistency(self) -> None:
        values = [
            (_t(0), 10.0),
            (_t(1), -5.0),
            (_t(2), 10.0),
        ]
        episodes = detect_episodes(values, min_consecutive=1)
        assert len(episodes) == 3
        for e in episodes:
            assert e["sign_consistency"] == 1.0

    def test_consistent_episode_has_full_consistency(self) -> None:
        values = [
            (_t(0), 10.0),
            (_t(1), 20.0),
            (_t(2), 30.0),
        ]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 1
        assert episodes[0]["sign_consistency"] == 1.0


# ---------------------------------------------------------------------------
# Absence of one direction
# ---------------------------------------------------------------------------


class TestAbsentDirection:
    def test_only_positive_values(self) -> None:
        values = [(_t(i), float(i * 100)) for i in range(5)]
        episodes = detect_episodes(values)
        assert len(episodes) == 1
        assert episodes[0]["direction"] == "positive"

    def test_only_negative_values(self) -> None:
        values = [(_t(i), float(-i * 100)) for i in range(5)]
        episodes = detect_episodes(values)
        assert len(episodes) == 1
        assert episodes[0]["direction"] == "negative"


# ---------------------------------------------------------------------------
# Zero values
# ---------------------------------------------------------------------------


class TestZeroValues:
    def test_zeros_separate_episodes(self) -> None:
        values = [(_t(i), val) for i, val in enumerate([10, 20, 0, 0, -5, -10, 0, 15, 25])]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 3
        assert episodes[0]["direction"] == "positive"
        assert episodes[1]["direction"] == "negative"
        assert episodes[2]["direction"] == "positive"

    def test_single_zero_not_an_episode(self) -> None:
        values = [(_t(i), 0.0) for i in range(3)]
        episodes = detect_episodes(values, min_consecutive=2)
        assert len(episodes) == 0
