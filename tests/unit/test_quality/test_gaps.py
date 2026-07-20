from datetime import UTC, datetime, timedelta

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags
from solgreen.quality._gaps import detect_gaps, detect_gaps_flow


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


class TestDetectGaps:
    def test_empty_list(self) -> None:
        gaps = detect_gaps([])
        assert gaps == ()

    def test_single_sample(self) -> None:
        s = _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        gaps = detect_gaps([s])
        assert gaps == ()

    def test_no_gaps_within_interval(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 10, tzinfo=UTC)),
        ]
        gaps = detect_gaps(samples, expected_interval=timedelta(minutes=5))
        assert gaps == ()

    def test_detects_gap(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 13, 0, tzinfo=UTC)),
        ]
        gaps = detect_gaps(samples, expected_interval=timedelta(minutes=5))
        assert len(gaps) == 1
        assert gaps[0].before_index == 0
        assert gaps[0].after_index == 1
        assert gaps[0].gap_duration == timedelta(hours=1)
        assert gaps[0].gap_ratio == 12.0

    def test_gap_factor_filters_false_positives(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 7, tzinfo=UTC)),
        ]
        gaps = detect_gaps(
            samples,
            expected_interval=timedelta(minutes=5),
            gap_factor=1.5,
        )
        assert gaps == ()

    def test_multiple_gaps(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 13, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 13, 5, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 15, 0, tzinfo=UTC)),
        ]
        gaps = detect_gaps(samples, expected_interval=timedelta(minutes=5))
        assert len(gaps) == 2
        assert gaps[0].before_index == 0
        assert gaps[0].after_index == 1
        assert gaps[1].before_index == 2
        assert gaps[1].after_index == 3

    def test_gap_ratio_calculation(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 10, tzinfo=UTC)),
        ]
        gaps = detect_gaps(samples, expected_interval=timedelta(minutes=5))
        assert gaps[0].gap_ratio == 2.0


class TestDetectGapsFlow:
    def test_empty_list_flow(self) -> None:
        gaps = detect_gaps_flow([])
        assert gaps == ()

    def test_no_gaps_flow(self) -> None:
        samples = [
            _make_flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_flow(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
        ]
        gaps = detect_gaps_flow(samples, expected_interval=timedelta(minutes=5))
        assert gaps == ()

    def test_detects_gap_flow(self) -> None:
        samples = [
            _make_flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_flow(datetime(2026, 7, 17, 14, 0, tzinfo=UTC)),
        ]
        gaps = detect_gaps_flow(samples, expected_interval=timedelta(minutes=5))
        assert len(gaps) == 1
        assert gaps[0].gap_ratio == 24.0
