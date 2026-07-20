from datetime import timedelta

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.quality._gaps import detect_gaps, detect_gaps_flow
from solgreen.quality._ordering import _detect_duplicates, _detect_duplicates_flow
from solgreen.quality._types import QualityResult
from solgreen.quality.score import compute_quality_score


def analyze_telemetry(
    samples: list[InverterTelemetrySample],
    source_type: SourceType,
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
) -> QualityResult:
    ordering, duplicates = _detect_duplicates(samples)
    gaps = detect_gaps(samples, expected_interval=expected_interval, gap_factor=gap_factor)

    dup_total = sum(d.count - 1 for d in duplicates)
    quality_score = compute_quality_score(
        total_rows=len(samples),
        duplicate_count=dup_total,
        gap_count=len(gaps),
    )

    return QualityResult(
        source_type=source_type,
        total_rows=len(samples),
        ordering=ordering,
        duplicates=duplicates,
        gaps=gaps,
        quality_score=quality_score,
    )


def analyze_plant_flow(
    samples: list[PlantFlowSample],
    source_type: SourceType,
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
) -> QualityResult:
    ordering, duplicates = _detect_duplicates_flow(samples)
    gaps = detect_gaps_flow(samples, expected_interval=expected_interval, gap_factor=gap_factor)

    dup_total = sum(d.count - 1 for d in duplicates)
    quality_score = compute_quality_score(
        total_rows=len(samples),
        duplicate_count=dup_total,
        gap_count=len(gaps),
    )

    return QualityResult(
        source_type=source_type,
        total_rows=len(samples),
        ordering=ordering,
        duplicates=duplicates,
        gaps=gaps,
        quality_score=quality_score,
    )
