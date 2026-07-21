from solgreen.quality._gaps import detect_gaps, detect_gaps_flow
from solgreen.quality._types import (
    DuplicateTimestamp,
    OrderingInfo,
    QualityDimensions,
    QualityResult,
    TemporalGap,
)
from solgreen.quality.analyze import analyze_plant_flow, analyze_telemetry
from solgreen.quality.score import (
    DUPLICATE_INTEGRITY_WEIGHT,
    TEMPORAL_COVERAGE_WEIGHT,
    aggregate_quality_score,
    compute_temporal_dimensions,
)

__all__ = [
    "DUPLICATE_INTEGRITY_WEIGHT",
    "TEMPORAL_COVERAGE_WEIGHT",
    "DuplicateTimestamp",
    "OrderingInfo",
    "QualityDimensions",
    "QualityResult",
    "TemporalGap",
    "aggregate_quality_score",
    "analyze_plant_flow",
    "analyze_telemetry",
    "compute_temporal_dimensions",
    "detect_gaps",
    "detect_gaps_flow",
]
