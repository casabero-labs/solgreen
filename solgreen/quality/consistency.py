from __future__ import annotations

import math
from datetime import timedelta

from solgreen.quality._consistency_types import (
    ConsistencyFinding,
    ConsistencyReasonCode,
    ConsistencyResult,
    MeasurementConsistencyProfile,
)
from solgreen.quality._types import QualityDimensions
from solgreen.timeline.canonical import CanonicalSample


def _is_finite_numeric(value: object) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return True


def _compute_allowed_difference(
    flow_value: float,
    telemetry_value: float,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> float:
    absolute_component = absolute_tolerance
    relative_component = relative_tolerance * max(abs(flow_value), abs(telemetry_value))
    return max(absolute_component, relative_component)


def evaluate_consistency(
    canonical_samples: list[CanonicalSample],
    *,
    profile: MeasurementConsistencyProfile,
) -> ConsistencyResult:
    findings: list[ConsistencyFinding] = []
    evaluated_count = 0
    passed_count = 0
    failed_count = 0
    skipped_missing_count = 0
    skipped_alignment_count = 0
    skipped_nonfinite_count = 0

    merged_samples = [s for s in canonical_samples if s.source == "merged"]

    for samp in merged_samples:
        time_delta = samp.time_delta or timedelta(0)

        for pair in profile.pairs:
            flow_value = getattr(samp, pair.flow_field)
            telemetry_value = getattr(samp, pair.telemetry_field)

            if flow_value is None or telemetry_value is None:
                skipped_missing_count += 1
                continue

            if not _is_finite_numeric(flow_value) or not _is_finite_numeric(telemetry_value):
                skipped_nonfinite_count += 1
                findings.append(
                    ConsistencyFinding(
                        pair_id=pair.pair_id,
                        pair_version=pair.pair_version,
                        timestamp_utc=samp.timestamp_axis,
                        flow_field=pair.flow_field,
                        telemetry_field=pair.telemetry_field,
                        flow_value=flow_value,
                        telemetry_value=telemetry_value,
                        absolute_difference=None,
                        allowed_difference=None,
                        unit=pair.unit,
                        time_delta=time_delta if samp.time_delta else None,
                        profile_version=pair.profile_version,
                        profile_status=pair.status,
                        profile_source=pair.source,
                        reason_code=ConsistencyReasonCode.NONFINITE_VALUE,
                    )
                )
                continue

            if time_delta > pair.max_alignment_delta:
                skipped_alignment_count += 1
                continue

            abs_tol = pair.absolute_tolerance or 0.0
            rel_tol = pair.relative_tolerance or 0.0
            allowed = _compute_allowed_difference(
                float(flow_value), float(telemetry_value), abs_tol, rel_tol
            )
            absolute_diff = abs(float(flow_value) - float(telemetry_value))

            evaluated_count += 1
            if absolute_diff <= allowed:
                passed_count += 1
            else:
                failed_count += 1
                findings.append(
                    ConsistencyFinding(
                        pair_id=pair.pair_id,
                        pair_version=pair.pair_version,
                        timestamp_utc=samp.timestamp_axis,
                        flow_field=pair.flow_field,
                        telemetry_field=pair.telemetry_field,
                        flow_value=float(flow_value),
                        telemetry_value=float(telemetry_value),
                        absolute_difference=absolute_diff,
                        allowed_difference=allowed,
                        unit=pair.unit,
                        time_delta=time_delta if time_delta else None,
                        profile_version=pair.profile_version,
                        profile_status=pair.status,
                        profile_source=pair.source,
                        reason_code=ConsistencyReasonCode.OUTSIDE_TOLERANCE,
                    )
                )

    if evaluated_count == 0:
        score: float | None = None
    else:
        score = passed_count / evaluated_count

    return ConsistencyResult(
        evaluated_count=evaluated_count,
        passed_count=passed_count,
        failed_count=failed_count,
        skipped_missing_count=skipped_missing_count,
        skipped_alignment_count=skipped_alignment_count,
        skipped_nonfinite_count=skipped_nonfinite_count,
        findings=tuple(findings),
        score=score,
    )


def apply_consistency_to_dimensions(
    dimensions: QualityDimensions,
    canonical_samples: list[CanonicalSample],
    profile: MeasurementConsistencyProfile | None,
) -> QualityDimensions:
    if profile is None:
        return dimensions
    result = evaluate_consistency(canonical_samples, profile=profile)
    if result.evaluated_count == 0:
        return dimensions
    return dimensions.model_copy(update={"consistency_score": result.score})
