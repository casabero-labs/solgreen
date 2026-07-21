from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from solgreen.quality._types import DuplicateTimestamp, QualityDimensions, TemporalGap

DUPLICATE_INTEGRITY_WEIGHT: float = 0.60
TEMPORAL_COVERAGE_WEIGHT: float = 0.40


def _detect_gaps_from_timestamps(
    sorted_ts: Sequence[datetime],
    expected_interval: timedelta,
    gap_factor: float = 1.5,
) -> tuple[TemporalGap, ...]:
    if len(sorted_ts) < 2:
        return ()

    threshold = expected_interval * gap_factor
    gaps: list[TemporalGap] = []
    for i in range(len(sorted_ts) - 1):
        delta = sorted_ts[i + 1] - sorted_ts[i]
        if delta > threshold:
            gaps.append(
                TemporalGap(
                    before_index=i,
                    after_index=i + 1,
                    gap_duration=delta,
                    expected_interval=expected_interval,
                    gap_ratio=delta / expected_interval,
                )
            )
    return tuple(gaps)


def compute_temporal_dimensions(
    timestamps: Sequence[datetime],
    *,
    expected_interval: timedelta,
    expected_sample_count: int | None = None,
    duplicates: tuple[DuplicateTimestamp, ...] = (),
    gaps: tuple[TemporalGap, ...] | None = None,
    gap_factor: float = 1.5,
) -> QualityDimensions:
    if not timestamps:
        return QualityDimensions(
            completeness=0.0,
            temporal_coverage=0.0,
            duplicate_integrity=1.0,
            plausibility_score=None,
            consistency_score=None,
        )

    sorted_ts = sorted(timestamps)
    analysis_span = sorted_ts[-1] - sorted_ts[0]

    if gaps is None:
        gaps = _detect_gaps_from_timestamps(sorted_ts, expected_interval, gap_factor)

    missing_duration = timedelta(0)
    for gap in gaps:
        missing_duration += max(gap.gap_duration - expected_interval, timedelta(0))

    if analysis_span.total_seconds() > 0:
        covered_duration = max(analysis_span - missing_duration, timedelta(0))
        temporal_coverage = covered_duration.total_seconds() / analysis_span.total_seconds()
    else:
        temporal_coverage = 0.0

    total = len(sorted_ts)
    dup_total = sum(d.count - 1 for d in duplicates)
    duplicate_integrity = 1.0 - (dup_total / total) if total > 0 else 1.0

    if expected_sample_count is not None and expected_sample_count > 0:
        unique_observed = total - dup_total
        completeness = unique_observed / expected_sample_count
    else:
        completeness = None

    return QualityDimensions(
        completeness=completeness,
        temporal_coverage=temporal_coverage,
        duplicate_integrity=duplicate_integrity,
        plausibility_score=None,
        consistency_score=None,
    )


def aggregate_quality_score(dimensions: QualityDimensions) -> float:
    parts: list[tuple[float, float]] = [
        (TEMPORAL_COVERAGE_WEIGHT, dimensions.temporal_coverage),
        (DUPLICATE_INTEGRITY_WEIGHT, dimensions.duplicate_integrity),
    ]

    total_weight = sum(weight for weight, _ in parts)
    if total_weight <= 0:
        return 0.0

    weighted_sum = sum(weight * value for weight, value in parts)
    return max(0.0, min(1.0, weighted_sum / total_weight))
