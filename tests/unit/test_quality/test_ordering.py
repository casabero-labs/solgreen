import pytest
from datetime import datetime, timedelta, UTC

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags
from solgreen.quality._ordering import _detect_duplicates, _detect_duplicates_flow


def _make_telemetry(ts: datetime) -> InverterTelemetrySample:
    return InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals={},
        validity=ValidityFlags(),
    )


def _make_flow(ts: datetime) -> PlantFlowSample:
    return PlantFlowSample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        validity=ValidityFlags(),
    )


class TestDetectDuplicates:
    def test_empty_list(self) -> None:
        ordering, dups = _detect_duplicates([])
        assert ordering.was_ordered is True
        assert ordering.was_strict is True
        assert dups == ()

    def test_single_sample(self) -> None:
        s = _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        ordering, dups = _detect_duplicates([s])
        assert ordering.was_ordered is True
        assert ordering.was_strict is True
        assert dups == ()

    def test_no_duplicates(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 10, tzinfo=UTC)),
        ]
        ordering, dups = _detect_duplicates(samples)
        assert ordering.was_ordered is True
        assert ordering.was_strict is True
        assert dups == ()

    def test_detects_duplicate(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        samples = [
            _make_telemetry(ts),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_telemetry(ts),
        ]
        ordering, dups = _detect_duplicates(samples)
        assert ordering.was_strict is False
        assert len(dups) == 1
        assert dups[0].count == 2
        assert dups[0].indices == (0, 2)

    def test_detects_triple_duplicate(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        samples = [
            _make_telemetry(ts),
            _make_telemetry(ts),
            _make_telemetry(ts),
        ]
        ordering, dups = _detect_duplicates(samples)
        assert ordering.was_strict is False
        assert len(dups) == 1
        assert dups[0].count == 3
        assert dups[0].indices == (0, 1, 2)

    def test_multiple_duplicate_groups(self) -> None:
        ts1 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts2 = datetime(2026, 7, 17, 12, 5, tzinfo=UTC)
        ts3 = datetime(2026, 7, 17, 12, 10, tzinfo=UTC)
        samples = [
            _make_telemetry(ts1),
            _make_telemetry(ts1),
            _make_telemetry(ts2),
            _make_telemetry(ts2),
            _make_telemetry(ts3),
        ]
        ordering, dups = _detect_duplicates(samples)
        assert ordering.was_strict is False
        assert len(dups) == 2
        assert dups[0].indices == (0, 1)
        assert dups[1].indices == (2, 3)

    def test_out_of_order_marks_not_ordered(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 10, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
        ]
        ordering, dups = _detect_duplicates(samples)
        assert ordering.was_ordered is False
        assert ordering.was_strict is True


class TestDetectDuplicatesFlow:
    def test_empty_list(self) -> None:
        ordering, dups = _detect_duplicates_flow([])
        assert ordering.was_ordered is True
        assert ordering.was_strict is True

    def test_no_duplicates_flow(self) -> None:
        samples = [
            _make_flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_flow(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
        ]
        ordering, dups = _detect_duplicates_flow(samples)
        assert ordering.was_strict is True
        assert dups == ()

    def test_detects_duplicate_flow(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        samples = [
            _make_flow(ts),
            _make_flow(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_flow(ts),
        ]
        ordering, dups = _detect_duplicates_flow(samples)
        assert ordering.was_strict is False
        assert len(dups) == 1
        assert dups[0].count == 2
