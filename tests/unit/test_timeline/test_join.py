from datetime import UTC, datetime, timedelta

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags
from solgreen.timeline.join import (
    _compute_confidence,
    _pv_power,
    join_by_tolerance,
)


def _flow(ts: datetime, **kwargs: object) -> PlantFlowSample:
    return PlantFlowSample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        validity=ValidityFlags(),
        **kwargs,
    )


def _telemetry(ts: datetime, **kwargs: object) -> InverterTelemetrySample:
    return InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals=dict(kwargs),
        validity=ValidityFlags(),
    )


class TestPvPower:
    def test_both_pv_signals(self) -> None:
        t = _telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC), potencia_cc_pv1_w=1500.0, potencia_cc_pv2_w=1300.0)
        assert _pv_power(t) == 2800.0

    def test_only_pv1(self) -> None:
        t = _telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC), potencia_cc_pv1_w=1500.0)
        assert _pv_power(t) == 1500.0

    def test_none_if_no_pv(self) -> None:
        t = _telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
        assert _pv_power(t) is None


class TestComputeConfidence:
    def test_zero_delta(self) -> None:
        assert _compute_confidence(timedelta(0), timedelta(minutes=2, seconds=30)) == 1.0

    def test_half_tolerance(self) -> None:
        tol = timedelta(minutes=2, seconds=30)
        assert _compute_confidence(timedelta(minutes=1, seconds=15), tol) == 0.5

    def test_at_tolerance(self) -> None:
        tol = timedelta(minutes=2, seconds=30)
        assert _compute_confidence(tol, tol) == 0.0

    def test_above_tolerance(self) -> None:
        tol = timedelta(minutes=2, seconds=30)
        assert _compute_confidence(timedelta(minutes=5), tol) == 0.0


class TestJoinByTolerance:
    def test_empty_lists(self) -> None:
        result = join_by_tolerance([], [])
        assert result == []

    def test_only_flow_samples(self) -> None:
        samples = [
            _flow(datetime(2026, 7, 17, 12, 0, tzinfo=UTC), potencia_de_produccion_w=2800.0),
            _flow(datetime(2026, 7, 17, 12, 5, tzinfo=UTC), potencia_de_produccion_w=2900.0),
        ]
        result = join_by_tolerance(samples, [])
        assert len(result) == 2
        assert all(r.source == "flow" for r in result)
        assert result[0].flow_potencia_produccion_w == 2800.0

    def test_only_telemetry_samples(self) -> None:
        samples = [
            _telemetry(datetime(2026, 7, 17, 12, 0, tzinfo=UTC), potencia_cc_pv1_w=1500.0),
        ]
        result = join_by_tolerance([], samples)
        assert len(result) == 1
        assert result[0].source == "telemetry"
        assert result[0].telemetry_pv_power_w == 1500.0

    def test_within_tolerance_merges(self) -> None:
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        flow_samples = [_flow(ts, potencia_de_produccion_w=2800.0)]
        tel_samples = [_telemetry(ts, potencia_cc_pv1_w=1500.0, potencia_cc_pv2_w=1300.0)]
        result = join_by_tolerance(flow_samples, tel_samples)
        assert len(result) == 1
        assert result[0].source == "merged"
        assert result[0].flow_potencia_produccion_w == 2800.0
        assert result[0].telemetry_pv_power_w == 2800.0
        assert result[0].time_delta == timedelta(0)

    def test_outside_tolerance_produces_separate(self) -> None:
        ts_flow = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts_tel = datetime(2026, 7, 17, 13, 0, tzinfo=UTC)
        flow_samples = [_flow(ts_flow, potencia_de_produccion_w=2800.0)]
        tel_samples = [_telemetry(ts_tel, potencia_cc_pv1_w=1500.0)]
        result = join_by_tolerance(flow_samples, tel_samples)
        assert len(result) == 2
        merged = [r for r in result if r.source == "merged"]
        assert merged == []
        flow_result = [r for r in result if r.source == "flow"]
        tel_result = [r for r in result if r.source == "telemetry"]
        assert len(flow_result) == 1
        assert len(tel_result) == 1

    def test_nearest_match_when_multiple_in_tolerance(self) -> None:
        ts_flow = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts_tel1 = datetime(2026, 7, 17, 12, 1, tzinfo=UTC)
        ts_tel2 = datetime(2026, 7, 17, 12, 3, tzinfo=UTC)
        flow_samples = [_flow(ts_flow)]
        tel_samples = [_telemetry(ts_tel1), _telemetry(ts_tel2)]
        result = join_by_tolerance(flow_samples, tel_samples)
        assert len(result) == 2
        merged = [r for r in result if r.source == "merged"][0]
        assert merged.time_delta == timedelta(minutes=1)
        unmatched = [r for r in result if r.source == "telemetry"][0]
        assert unmatched.timestamp_axis == ts_tel2

    def test_custom_tolerance(self) -> None:
        ts_flow = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts_tel = datetime(2026, 7, 17, 12, 3, tzinfo=UTC)
        flow_samples = [_flow(ts_flow)]
        tel_samples = [_telemetry(ts_tel)]
        result = join_by_tolerance(flow_samples, tel_samples, tolerance=timedelta(minutes=2))
        assert len(result) == 2
        assert all(r.source in ("flow", "telemetry") for r in result)
        result_wider = join_by_tolerance(flow_samples, tel_samples, tolerance=timedelta(minutes=5))
        assert len(result_wider) == 1
        assert result_wider[0].source == "merged"

    def test_output_sorted_by_timestamp(self) -> None:
        ts1 = datetime(2026, 7, 17, 12, 10, tzinfo=UTC)
        ts2 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts3 = datetime(2026, 7, 17, 12, 5, tzinfo=UTC)
        flow_samples = [_flow(ts1), _flow(ts2)]
        tel_samples = [_telemetry(ts3)]
        result = join_by_tolerance(flow_samples, tel_samples)
        assert result[0].timestamp_axis == ts2
        assert result[1].timestamp_axis == ts3
        assert result[2].timestamp_axis == ts1

    def test_unmatched_telemetry_appended_at_end(self) -> None:
        ts_flow = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        ts_tel = datetime(2026, 7, 17, 13, 0, tzinfo=UTC)
        flow_samples = [_flow(ts_flow)]
        tel_samples = [_telemetry(ts_tel)]
        result = join_by_tolerance(flow_samples, tel_samples)
        assert len(result) == 2
        assert result[0].source == "flow"
        assert result[1].source == "telemetry"
        assert result[1].timestamp_axis == ts_tel
