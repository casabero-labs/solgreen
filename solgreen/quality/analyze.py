from __future__ import annotations

from datetime import timedelta

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.quality._gaps import detect_gaps, detect_gaps_flow
from solgreen.quality._ordering import _detect_duplicates, _detect_duplicates_flow
from solgreen.quality._plausibility_types import MeasurementPlausibilityProfile
from solgreen.quality._types import QualityDimensions, QualityResult
from solgreen.quality.plausibility import (
    evaluate_inverter_telemetry,
    evaluate_plant_flow,
)
from solgreen.quality.score import aggregate_quality_score, compute_temporal_dimensions


def _apply_plausibility(
    dimensions: QualityDimensions,
    profile: MeasurementPlausibilityProfile | None,
    samples: list[InverterTelemetrySample] | list[PlantFlowSample],
    source_type: SourceType,
) -> QualityDimensions:
    if profile is None:
        return dimensions
    if source_type == SourceType.SOLARMAN_INVERTER_TELEMETRY:
        plausibility = evaluate_inverter_telemetry(
            samples,  # type: ignore[arg-type]
            profile=profile,
        )
    elif source_type == SourceType.SOLARMAN_PLANT_FLOW:
        plausibility = evaluate_plant_flow(
            samples,  # type: ignore[arg-type]
            profile=profile,
        )
    else:
        return dimensions
    if plausibility.evaluated_count == 0:
        return dimensions
    return dimensions.model_copy(update={"plausibility_score": plausibility.score})


def analyze_telemetry(
    samples: list[InverterTelemetrySample],
    source_type: SourceType,
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
    expected_sample_count: int | None = None,
    plausibility_profile: MeasurementPlausibilityProfile | None = None,
) -> QualityResult:
    ordering, duplicates = _detect_duplicates(samples)
    gaps = detect_gaps(samples, expected_interval=expected_interval, gap_factor=gap_factor)

    timestamps = [s.timestamp_utc for s in samples]
    dimensions = compute_temporal_dimensions(
        timestamps,
        expected_interval=expected_interval,
        expected_sample_count=expected_sample_count,
        duplicates=duplicates,
        gaps=gaps,
    )

    dimensions = _apply_plausibility(dimensions, plausibility_profile, samples, source_type)

    quality_score = 0.0 if not samples else aggregate_quality_score(dimensions)

    return QualityResult(
        source_type=source_type,
        total_rows=len(samples),
        ordering=ordering,
        duplicates=duplicates,
        gaps=gaps,
        quality_score=quality_score,
        dimensions=dimensions,
    )


def analyze_plant_flow(
    samples: list[PlantFlowSample],
    source_type: SourceType,
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
    expected_sample_count: int | None = None,
    plausibility_profile: MeasurementPlausibilityProfile | None = None,
) -> QualityResult:
    ordering, duplicates = _detect_duplicates_flow(samples)
    gaps = detect_gaps_flow(samples, expected_interval=expected_interval, gap_factor=gap_factor)

    timestamps = [s.timestamp_utc for s in samples]
    dimensions = compute_temporal_dimensions(
        timestamps,
        expected_interval=expected_interval,
        expected_sample_count=expected_sample_count,
        duplicates=duplicates,
        gaps=gaps,
    )

    dimensions = _apply_plausibility(dimensions, plausibility_profile, samples, source_type)

    quality_score = 0.0 if not samples else aggregate_quality_score(dimensions)

    return QualityResult(
        source_type=source_type,
        total_rows=len(samples),
        ordering=ordering,
        duplicates=duplicates,
        gaps=gaps,
        quality_score=quality_score,
        dimensions=dimensions,
    )
