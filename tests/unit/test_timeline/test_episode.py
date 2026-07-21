from datetime import UTC, datetime, timedelta

from solgreen.timeline import CanonicalSample, build_episodes
from solgreen.timeline.episode import _derive_episode_type

TS0 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _sample(
    ts: datetime,
    *,
    pv_w: float | None = None,
    grid_w: float | None = None,
    inverter_state: str | None = None,
    source: str = "merged",
    confidence: float = 1.0,
) -> CanonicalSample:
    return CanonicalSample(
        timestamp_axis=ts,
        source=source,
        flow_potencia_produccion_w=pv_w,
        telemetry_pv_power_w=pv_w,
        flow_grid_w=grid_w,
        telemetry_grid_power_w=grid_w,
        telemetry_inverter_state=inverter_state,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# _derive_episode_type
# ---------------------------------------------------------------------------


class TestDeriveEpisodeType:
    def test_pv_production(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800),
        ]
        assert _derive_episode_type(samples) == "pv_production"

    def test_standby(self) -> None:
        samples = [
            _sample(TS0, inverter_state="standby"),
            _sample(TS0 + timedelta(minutes=5), inverter_state="standby"),
        ]
        assert _derive_episode_type(samples) == "standby"

    def test_standby_idle_variant(self) -> None:
        samples = [
            _sample(TS0, inverter_state="Idle"),
            _sample(TS0 + timedelta(minutes=5), inverter_state="idle"),
        ]
        assert _derive_episode_type(samples) == "standby"

    def test_grid_injection(self) -> None:
        samples = [
            _sample(TS0, grid_w=3000),
            _sample(TS0 + timedelta(minutes=5), grid_w=2500),
        ]
        assert _derive_episode_type(samples) == "grid_injection"

    def test_custom_mixed(self) -> None:
        samples = [
            _sample(TS0, pv_w=1000),
            _sample(TS0 + timedelta(minutes=5), inverter_state="standby"),
        ]
        assert _derive_episode_type(samples) == "custom"

    def test_empty_returns_custom(self) -> None:
        assert _derive_episode_type([]) == "custom"


# ---------------------------------------------------------------------------
# build_episodes
# ---------------------------------------------------------------------------


class TestBuildEpisodes:
    def test_single_group_no_gaps(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800),
            _sample(TS0 + timedelta(minutes=10), pv_w=5100),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 1
        ep = eps[0]
        assert ep.episode_type == "pv_production"
        assert ep.sample_count == 3
        assert ep.start == TS0
        assert ep.end == TS0 + timedelta(minutes=10)
        assert ep.duration == timedelta(minutes=10)
        assert ep.source_summary == "merged"

    def test_gap_splits_episodes(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800),
            _sample(TS0 + timedelta(minutes=20), pv_w=5100),
            _sample(TS0 + timedelta(minutes=25), pv_w=4900),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 2
        assert eps[0].sample_count == 2
        assert eps[1].sample_count == 2
        assert eps[0].start == TS0
        assert eps[0].end == TS0 + timedelta(minutes=5)
        assert eps[1].start == TS0 + timedelta(minutes=20)
        assert eps[1].end == TS0 + timedelta(minutes=25)

    def test_min_samples_filters_small_episode(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000),
            _sample(TS0 + timedelta(minutes=20), pv_w=5100),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 0

    def test_coverage_pct(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000, confidence=1.0),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800, confidence=0.3),
            _sample(TS0 + timedelta(minutes=10), pv_w=5100, confidence=1.0),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 1
        ep = eps[0]
        assert ep.coverage_pct > 0
        assert ep.coverage_pct <= 100.0

    def test_empty_timeline(self) -> None:
        assert build_episodes([]) == []

    def test_source_summary_mixed(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000, source="flow"),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800, source="telemetry"),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 1
        assert eps[0].source_summary == "mixed"

    def test_source_summary_flow_only(self) -> None:
        samples = [
            _sample(TS0, pv_w=5000, source="flow"),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800, source="flow"),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 1
        assert eps[0].source_summary == "flow_only"

    def test_signals_averaged(self) -> None:
        samples = [
            _sample(TS0, pv_w=1000, grid_w=500),
            _sample(TS0 + timedelta(minutes=5), pv_w=2000, grid_w=1000),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 1
        assert eps[0].signals["flow_potencia_produccion_w"] == 1500.0
        assert eps[0].signals["flow_grid_w"] == 750.0

    def test_episodes_sorted_by_start(self) -> None:
        samples = [
            _sample(TS0 + timedelta(minutes=30), pv_w=1000),
            _sample(TS0 + timedelta(minutes=35), pv_w=1200),
            _sample(TS0, pv_w=5000),
            _sample(TS0 + timedelta(minutes=5), pv_w=4800),
        ]
        eps = build_episodes(samples)
        assert len(eps) == 2
        assert eps[0].start < eps[1].start
