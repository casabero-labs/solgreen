from solgreen.quality._consistency_types import (
    ConsistencyFinding,
    ConsistencyPair,
    ConsistencyReasonCode,
    ConsistencyResult,
    ConsistencyStatus,
    MeasurementConsistencyProfile,
)
from solgreen.quality._gaps import detect_gaps, detect_gaps_flow
from solgreen.quality._plausibility_types import (
    MeasurementPlausibilityProfile,
    MeasurementRange,
    PlausibilityFinding,
    PlausibilityReasonCode,
    PlausibilityResult,
    PlausibilityStatus,
)
from solgreen.quality._types import (
    DuplicateTimestamp,
    OrderingInfo,
    QualityDimensions,
    QualityResult,
    TemporalGap,
)
from solgreen.quality.analyze import analyze_plant_flow, analyze_telemetry
from solgreen.quality.consistency import (
    apply_consistency_to_dimensions,
    evaluate_consistency,
)
from solgreen.quality.plausibility import (
    evaluate_inverter_telemetry,
    evaluate_plant_flow,
)
from solgreen.quality.score import (
    DUPLICATE_INTEGRITY_WEIGHT,
    TEMPORAL_COVERAGE_WEIGHT,
    aggregate_quality_score,
    compute_temporal_dimensions,
)

__all__ = [
    "DUPLICATE_INTEGRITY_WEIGHT",
    "TEMPORAL_COVERAGE_WEIGHT",
    "ConsistencyFinding",
    "ConsistencyPair",
    "ConsistencyReasonCode",
    "ConsistencyResult",
    "ConsistencyStatus",
    "DuplicateTimestamp",
    "MeasurementConsistencyProfile",
    "MeasurementPlausibilityProfile",
    "MeasurementRange",
    "OrderingInfo",
    "PlausibilityFinding",
    "PlausibilityReasonCode",
    "PlausibilityResult",
    "PlausibilityStatus",
    "QualityDimensions",
    "QualityResult",
    "TemporalGap",
    "aggregate_quality_score",
    "analyze_plant_flow",
    "analyze_telemetry",
    "apply_consistency_to_dimensions",
    "compute_temporal_dimensions",
    "detect_gaps",
    "detect_gaps_flow",
    "evaluate_consistency",
    "evaluate_inverter_telemetry",
    "evaluate_plant_flow",
]
