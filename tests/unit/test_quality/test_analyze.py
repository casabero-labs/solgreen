import pytest
from datetime import datetime, timedelta, UTC

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags
from solgreen.quality import analyze_plant_flow, analyze_telemetry


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


class TestAnalyzeTelemetry:
    def test_empty_batch(self) -> None:
        result = analyze_telemetry([], SourceType.SOLARMAN_INVERTER_TELEMETRY)
        assert result.total_rows == 0
        assert result.source_type == SourceType.SOLARMAN_INVERTER_TELEMETRY
        assert result.ordering.was_ordered is True
        assert result.ordering.was_strict is True
        assert result.duplicates == ()
        assert result.gaps == ()
        assert result.quality_score == 1.0

    def test_clean_batch(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 10, tzinfo=UTC)),
        ]
        result = analyze_telemetry(samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
        assert result.total_rows == 3
        assert result.ordering.was_ordered is True
        assert result.ordering.was_strict is True
        assert result.duplicates == ()
        assert result.gaps == ()
        assert result.quality_score == 1.0

    def test_detects_duplicates(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        samples = [
            _make_telemetry(ts),
            _make_telemetry(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
            _make_telemetry(ts),
        ]
        result = analyze_telemetry(samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
        assert result.ordering.was_strict is False
        assert len(result.duplicates) == 1
        assert result.duplicates[0].count == 2
        assert result.quality_score < 1.0

    def test_detects_gaps(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 13, 0, tzinfo=UTC)),
        ]
        result = analyze_telemetry(samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
        assert len(result.gaps) == 1
        assert result.gaps[0].gap_ratio == 12.0

    def test_custom_interval(self) -> None:
        samples = [
            _make_telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_telemetry(datetime(2026, 7, 17, 12, 30, tzinfo=UTC)),
        ]
        result = analyze_telemetry(
            samples,
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            expected_interval=timedelta(minutes=30),
        )
        assert result.gaps == ()


class TestAnalyzePlantFlow:
    def test_empty_batch_flow(self) -> None:
        result = analyze_plant_flow([], SourceType.SOLARMAN_PLANT_FLOW)
        assert result.total_rows == 0
        assert result.quality_score == 1.0

    def test_clean_batch_flow(self) -> None:
        samples = [
            _make_flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_flow(datetime(2026, 7, 17, 12, 5, tzinfo=UTC)),
        ]
        result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
        assert result.total_rows == 2
        assert result.ordering.was_strict is True
        assert result.quality_score == 1.0

    def test_detects_duplicates_flow(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        samples = [
            _make_flow(ts),
            _make_flow(ts),
        ]
        result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
        assert len(result.duplicates) == 1
        assert result.duplicates[0].count == 2

    def test_detects_gaps_flow(self) -> None:
        samples = [
            _make_flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC)),
            _make_flow(datetime(2026, 7, 17, 14, 0, tzinfo=UTC)),
        ]
        result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
        assert len(result.gaps) == 1
        assert result.quality_score < 1.0
