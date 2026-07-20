from datetime import UTC, datetime, timedelta

from solgreen.timeline.canonical import CanonicalSample


class TestCanonicalSample:
    def test_flow_source_all_fields(self) -> None:
        sample = CanonicalSample(
            timestamp_axis=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            source="flow",
            flow_potencia_produccion_w=2800.0,
            flow_potencia_consumo_w=900.0,
            flow_grid_w=-150.0,
            flow_soc_pct=72.5,
            flow_battery_w=-300.0,
            quality_level="measured",
            confidence=1.0,
        )
        assert sample.source == "flow"
        assert sample.flow_potencia_produccion_w == 2800.0
        assert sample.flow_grid_w == -150.0
        assert sample.telemetry_pv_power_w is None
        assert sample.quality_level == "measured"
        assert sample.confidence == 1.0

    def test_merged_source_has_both_signals(self) -> None:
        sample = CanonicalSample(
            timestamp_axis=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            source="merged",
            time_delta=timedelta(seconds=30),
            flow_potencia_produccion_w=2800.0,
            flow_grid_w=-150.0,
            telemetry_pv_power_w=2750.0,
            telemetry_grid_power_w=-148.0,
            telemetry_soc_pct=72.0,
            quality_level="normalized",
            confidence=0.8,
        )
        assert sample.source == "merged"
        assert sample.flow_potencia_produccion_w == 2800.0
        assert sample.telemetry_pv_power_w == 2750.0
        assert sample.time_delta == timedelta(seconds=30)
        assert sample.confidence == 0.8

    def test_confidence_bounds(self) -> None:
        sample = CanonicalSample(
            timestamp_axis=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
            source="flow",
            confidence=0.0,
        )
        assert sample.confidence == 0.0

    def test_extra_forbidden(self) -> None:
        import pytest
        with pytest.raises(Exception):
            CanonicalSample(
                timestamp_axis=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
                source="flow",
                unknown_field=1,  # type: ignore[call-arg]
            )
