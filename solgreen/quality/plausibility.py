from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import TypeVar

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import SIGNAL_SPECS, InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.quality._plausibility_types import (
    MeasurementPlausibilityProfile,
    MeasurementRange,
    PlausibilityFinding,
    PlausibilityReasonCode,
    PlausibilityResult,
)


_SampleT = TypeVar("_SampleT", InverterTelemetrySample, PlantFlowSample)

CHECK_VERSION = "1.0.0"

CHECK_ID_NONFINITE = "PLB-NONFINITE"
CHECK_ID_SOC_RANGE = "PLB-SOC-RANGE"
CHECK_ID_ABS_ZERO = "PLB-ABS-ZERO"
CHECK_ID_PROFILE_RANGE = "PLB-PROFILE-RANGE"

ABSOLUTE_ZERO_C: float = -273.15
SOC_PCT_CANONICAL = "soc_pct"

_TEMPERATURE_CANONICALS: frozenset[str] = frozenset(
    spec.canonical_name for spec in SIGNAL_SPECS if spec.kind.value == "temperature_c"
)


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return True


def _classify_nonfinite(value: float) -> PlausibilityReasonCode:
    if math.isnan(value):
        return PlausibilityReasonCode.NAN
    if math.isinf(value):
        return (
            PlausibilityReasonCode.POSITIVE_INFINITY
            if value > 0
            else PlausibilityReasonCode.NEGATIVE_INFINITY
        )
    raise ValueError(f"Value {value} is finite")


def _is_temperature_signal(canonical_name: str) -> bool:
    return canonical_name in _TEMPERATURE_CANONICALS


def _numeric_signals_from_telemetry(
    sample: InverterTelemetrySample,
) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for name, value in sample.signals.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            out.append((name, float(value)))
    return out


def _numeric_signals_from_flow(sample: PlantFlowSample) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for name in PlantFlowSample.model_fields:
        value = getattr(sample, name)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            out.append((name, float(value)))
    return out


def _make_finding(
    *,
    check_id: str,
    signal_name: str,
    value: float,
    timestamp_utc: datetime,
    source_type: SourceType,
    reason_code: PlausibilityReasonCode,
    minimum: float | None,
    maximum: float | None,
    unit: str | None,
    range_: MeasurementRange | None,
) -> PlausibilityFinding:
    return PlausibilityFinding(
        check_id=check_id,
        check_version=CHECK_VERSION,
        source_type=source_type,
        signal_name=signal_name,
        timestamp_utc=timestamp_utc,
        observed_value=value,
        minimum=minimum,
        maximum=maximum,
        unit=unit,
        profile_version=range_.profile_version if range_ is not None else None,
        profile_status=range_.status if range_ is not None else None,
        profile_source=range_.source if range_ is not None else None,
        reason_code=reason_code,
    )


def _evaluate_signal(
    *,
    signal_name: str,
    value: float,
    timestamp_utc: datetime,
    source_type: SourceType,
    profile: MeasurementPlausibilityProfile | None,
) -> tuple[list[PlausibilityFinding], bool, bool]:
    """Returns (findings, evaluated, has_finding)."""
    findings: list[PlausibilityFinding] = []

    if not _is_finite_number(value):
        findings.append(
            _make_finding(
                check_id=CHECK_ID_NONFINITE,
                signal_name=signal_name,
                value=value,
                timestamp_utc=timestamp_utc,
                source_type=source_type,
                reason_code=_classify_nonfinite(value),
                minimum=None,
                maximum=None,
                unit=None,
                range_=None,
            )
        )
        return findings, False, True

    if signal_name == SOC_PCT_CANONICAL and (value < 0.0 or value > 100.0):
        findings.append(
            _make_finding(
                check_id=CHECK_ID_SOC_RANGE,
                signal_name=signal_name,
                value=value,
                timestamp_utc=timestamp_utc,
                source_type=source_type,
                reason_code=PlausibilityReasonCode.SOC_OUT_OF_RANGE,
                minimum=0.0,
                maximum=100.0,
                unit="%",
                range_=None,
            )
        )
        return findings, True, True

    if _is_temperature_signal(signal_name) and value < ABSOLUTE_ZERO_C:
        findings.append(
            _make_finding(
                check_id=CHECK_ID_ABS_ZERO,
                signal_name=signal_name,
                value=value,
                timestamp_utc=timestamp_utc,
                source_type=source_type,
                reason_code=PlausibilityReasonCode.BELOW_ABSOLUTE_ZERO,
                minimum=ABSOLUTE_ZERO_C,
                maximum=None,
                unit="C",
                range_=None,
            )
        )
        return findings, True, True

    if profile is not None and signal_name in profile.ranges:
        range_ = profile.ranges[signal_name]
        if value < range_.minimum:
            findings.append(
                _make_finding(
                    check_id=CHECK_ID_PROFILE_RANGE,
                    signal_name=signal_name,
                    value=value,
                    timestamp_utc=timestamp_utc,
                    source_type=source_type,
                    reason_code=PlausibilityReasonCode.BELOW_MINIMUM,
                    minimum=range_.minimum,
                    maximum=range_.maximum,
                    unit=range_.unit,
                    range_=range_,
                )
            )
        elif value > range_.maximum:
            findings.append(
                _make_finding(
                    check_id=CHECK_ID_PROFILE_RANGE,
                    signal_name=signal_name,
                    value=value,
                    timestamp_utc=timestamp_utc,
                    source_type=source_type,
                    reason_code=PlausibilityReasonCode.ABOVE_MAXIMUM,
                    minimum=range_.minimum,
                    maximum=range_.maximum,
                    unit=range_.unit,
                    range_=range_,
                )
            )
        return findings, True, bool(findings)

    return findings, False, False


def _evaluate_samples(
    samples: Iterable[_SampleT],
    *,
    source_type: SourceType,
    profile: MeasurementPlausibilityProfile | None,
    extract: Callable[[_SampleT], list[tuple[str, float]]],
) -> PlausibilityResult:
    findings: list[PlausibilityFinding] = []
    evaluated_count = 0
    passed_count = 0
    failed_count = 0
    not_configured_count = 0

    for sample in samples:
        for signal_name, value in extract(sample):
            sample_findings, evaluated, has_finding = _evaluate_signal(
                signal_name=signal_name,
                value=value,
                timestamp_utc=sample.timestamp_utc,
                source_type=source_type,
                profile=profile,
            )
            findings.extend(sample_findings)
            if evaluated:
                evaluated_count += 1
                if has_finding:
                    failed_count += 1
                else:
                    passed_count += 1
            else:
                not_configured_count += 1

    if evaluated_count == 0:
        score: float | None = None
    else:
        score = passed_count / evaluated_count

    return PlausibilityResult(
        evaluated_count=evaluated_count,
        passed_count=passed_count,
        failed_count=failed_count,
        not_configured_count=not_configured_count,
        findings=tuple(findings),
        score=score,
    )


def evaluate_inverter_telemetry(
    samples: list[InverterTelemetrySample],
    *,
    profile: MeasurementPlausibilityProfile | None = None,
) -> PlausibilityResult:
    return _evaluate_samples(
        samples,
        source_type=SourceType.SOLARMAN_INVERTER_TELEMETRY,
        profile=profile,
        extract=_numeric_signals_from_telemetry,
    )


def evaluate_plant_flow(
    samples: list[PlantFlowSample],
    *,
    profile: MeasurementPlausibilityProfile | None = None,
) -> PlausibilityResult:
    return _evaluate_samples(
        samples,
        source_type=SourceType.SOLARMAN_PLANT_FLOW,
        profile=profile,
        extract=_numeric_signals_from_flow,
    )
