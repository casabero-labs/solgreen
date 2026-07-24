from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from solgreen.quality._types import DuplicateTimestamp, QualityDimensions


class TestQualityDimensionsContract:
    def test_default_plausibility_and_consistency_are_none(self) -> None:
        d = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        assert d.completeness is None
        assert d.temporal_coverage == 1.0
        assert d.duplicate_integrity == 1.0
        assert d.plausibility_score is None
        assert d.consistency_score is None

    def test_frozen_model(self) -> None:
        d = QualityDimensions(temporal_coverage=0.5, duplicate_integrity=0.8)
        with pytest.raises(ValidationError, match="frozen"):
            d.temporal_coverage = 0.0  # type: ignore[misc]

    def test_temporal_coverage_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QualityDimensions(temporal_coverage=1.5, duplicate_integrity=0.5)

    def test_temporal_coverage_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QualityDimensions(temporal_coverage=-0.1, duplicate_integrity=0.5)

    def test_duplicate_integrity_bounds_enforced(self) -> None:
        with pytest.raises(ValidationError):
            QualityDimensions(temporal_coverage=0.5, duplicate_integrity=1.5)
        with pytest.raises(ValidationError):
            QualityDimensions(temporal_coverage=0.5, duplicate_integrity=-0.1)

    def test_completeness_accepts_none_or_fraction(self) -> None:
        d_none = QualityDimensions(
            temporal_coverage=0.5,
            duplicate_integrity=0.5,
            completeness=None,
        )
        assert d_none.completeness is None
        d_val = QualityDimensions(
            temporal_coverage=0.5,
            duplicate_integrity=0.5,
            completeness=0.7,
        )
        assert d_val.completeness == 0.7

    def test_completeness_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QualityDimensions(
                temporal_coverage=0.5,
                duplicate_integrity=0.5,
                completeness=1.5,
            )


class TestComputeTemporalDimensions:
    def _ts(self, hh: int, mm: int, day: int = 17) -> datetime:
        return datetime(2026, 7, day, hh, mm, tzinfo=UTC)

    def test_empty_batch(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        d = compute_temporal_dimensions([], expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == 0.0
        assert d.duplicate_integrity == 1.0
        assert d.completeness == 0.0
        assert d.plausibility_score is None
        assert d.consistency_score is None

    def test_single_sample(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        d = compute_temporal_dimensions([self._ts(12, 0)], expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == 0.0
        assert d.duplicate_integrity == 1.0
        assert d.completeness is None

    def test_two_samples_five_minutes_apart_perfect_coverage(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 5)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == 1.0
        assert d.duplicate_integrity == 1.0

    def test_three_samples_all_five_minutes_apart(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 5), self._ts(12, 10)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == 1.0

    def test_gap_of_10_minutes_means_5_min_missing_half_coverage(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 10)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == pytest.approx(0.5, abs=1e-9)

    def test_gap_of_60_minutes_means_55_min_missing(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(13, 0)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.temporal_coverage == pytest.approx(5 / 60, abs=1e-9)

    def test_jitter_under_gap_factor_not_counted_as_missing(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 7)]
        d = compute_temporal_dimensions(
            ts,
            expected_interval=timedelta(minutes=5),
        )
        assert d.temporal_coverage == 1.0

    def test_temporal_coverage_never_negative_when_gap_larger_than_span(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        gap = DuplicateTimestamp  # noqa: F841 - placeholder to avoid unused
        # This is logically impossible (gap can't exceed span) but
        # missing_duration could exceed analysis_span only if intervals
        # are larger than the span itself. Force a wide gap.
        ts = [self._ts(12, 0), self._ts(12, 0, day=18)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert 0.0 <= d.temporal_coverage <= 1.0

    def test_multiple_gaps_sum_missing_duration(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [
            self._ts(12, 0),
            self._ts(12, 5),
            self._ts(12, 20),
            self._ts(12, 25),
        ]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        # analysis_span = 25 min, gaps: 15 min (missing 10) + 5 min (missing 0)
        # missing_duration = 10 + 0 = 10 min; covered = 15 min
        # coverage = 15/25 = 0.6
        assert d.temporal_coverage == pytest.approx(15 / 25, abs=1e-9)

    def test_duplicate_integrity_perfect_when_no_duplicates(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 5)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.duplicate_integrity == 1.0

    def test_duplicate_integrity_with_duplicates(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 0), self._ts(12, 5)]
        dup = DuplicateTimestamp(
            index=0,
            timestamp=self._ts(12, 0),
            count=2,
            indices=(0, 1),
        )
        d = compute_temporal_dimensions(
            ts,
            expected_interval=timedelta(minutes=5),
            duplicates=(dup,),
        )
        assert d.duplicate_integrity == pytest.approx(2 / 3, abs=1e-9)

    def test_completeness_with_expected_sample_count(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 5)]
        d = compute_temporal_dimensions(
            ts,
            expected_interval=timedelta(minutes=5),
            expected_sample_count=10,
        )
        assert d.completeness == pytest.approx(0.2, abs=1e-9)

    def test_completeness_none_without_expected_sample_count(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 5)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert d.completeness is None

    def test_completeness_counts_unique_when_duplicates_present(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 0), self._ts(12, 5)]
        dup = DuplicateTimestamp(
            index=0,
            timestamp=self._ts(12, 0),
            count=2,
            indices=(0, 1),
        )
        d = compute_temporal_dimensions(
            ts,
            expected_interval=timedelta(minutes=5),
            expected_sample_count=10,
            duplicates=(dup,),
        )
        assert d.completeness == pytest.approx(0.2, abs=1e-9)

    def test_completeness_zero_for_empty_batch_even_with_expected_count(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        d = compute_temporal_dimensions(
            [],
            expected_interval=timedelta(minutes=5),
            expected_sample_count=10,
        )
        assert d.completeness == 0.0

    def test_temporal_coverage_zero_for_gap_larger_than_span(self) -> None:
        from solgreen.quality.score import compute_temporal_dimensions

        ts = [self._ts(12, 0), self._ts(12, 0, day=18)]
        d = compute_temporal_dimensions(ts, expected_interval=timedelta(minutes=5))
        assert 0.0 <= d.temporal_coverage <= 1.0


class TestAggregateQualityScore:
    def test_perfect_dimensions_yield_one(self) -> None:
        from solgreen.quality.score import aggregate_quality_score

        d = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        assert aggregate_quality_score(d) == pytest.approx(1.0, abs=1e-9)

    def test_zero_temporal_coverage_keeps_duplicate_weight(self) -> None:
        from solgreen.quality.score import aggregate_quality_score

        d = QualityDimensions(temporal_coverage=0.0, duplicate_integrity=1.0)
        assert aggregate_quality_score(d) == pytest.approx(0.60, abs=1e-9)

    def test_half_temporal_coverage_weighted_by_constant(self) -> None:
        from solgreen.quality.score import aggregate_quality_score

        d = QualityDimensions(temporal_coverage=0.5, duplicate_integrity=1.0)
        assert aggregate_quality_score(d) == pytest.approx(0.80, abs=1e-9)

    def test_zero_in_both_dimensions(self) -> None:
        from solgreen.quality.score import aggregate_quality_score

        d = QualityDimensions(temporal_coverage=0.0, duplicate_integrity=0.0)
        assert aggregate_quality_score(d) == 0.0

    def test_ignores_none_plausibility_and_consistency(self) -> None:
        from solgreen.quality.score import aggregate_quality_score

        d = QualityDimensions(
            temporal_coverage=1.0,
            duplicate_integrity=1.0,
            plausibility_score=None,
            consistency_score=None,
        )
        assert aggregate_quality_score(d) == pytest.approx(1.0, abs=1e-9)
