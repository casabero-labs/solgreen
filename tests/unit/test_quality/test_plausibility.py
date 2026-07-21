from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from solgreen.contracts.enums import SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags
from solgreen.quality._plausibility_types import (
    MeasurementPlausibilityProfile,
    MeasurementRange,
    PlausibilityReasonCode,
    PlausibilityResult,
    PlausibilityStatus,
)
from solgreen.quality.analyze import analyze_telemetry
from solgreen.quality.plausibility import (
    evaluate_inverter_telemetry,
    evaluate_plant_flow,
)

_TS = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _telemetry(
    signals: dict[str, Any] | None = None,
    *,
    timestamp_utc: datetime | None = None,
) -> InverterTelemetrySample:
    ts = timestamp_utc or _TS
    return InverterTelemetrySample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        signals=dict(signals or {}),
        validity=ValidityFlags(),
    )


def _flow(
    *,
    timestamp_utc: datetime | None = None,
    **fields: Any,
) -> PlantFlowSample:
    ts = timestamp_utc or _TS
    return PlantFlowSample(
        timestamp_original=ts,
        timestamp_utc=ts,
        timezone_source="UTC",
        validity=ValidityFlags(),
        **fields,
    )


def _range(
    canonical_name: str,
    *,
    minimum: float,
    maximum: float,
    unit: str = "V",
    status: PlausibilityStatus = PlausibilityStatus.PROVISIONAL,
    source: str = "synthetic-test-profile",
    profile_version: str = "0.0.1-test",
) -> MeasurementRange:
    return MeasurementRange(
        canonical_name=canonical_name,
        unit=unit,
        minimum=minimum,
        maximum=maximum,
        source=source,
        status=status,
        profile_version=profile_version,
    )


def _profile(*ranges: MeasurementRange) -> MeasurementPlausibilityProfile:
    return MeasurementPlausibilityProfile(
        profile_version="0.0.1-test",
        ranges={r.canonical_name: r for r in ranges},
    )


class TestNonFiniteCheck:
    def test_nan_produces_finding(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": float("nan")})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.NAN
        assert math.isnan(result.findings[0].observed_value)

    def test_positive_infinity_produces_finding(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": float("inf")})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.POSITIVE_INFINITY
        assert math.isinf(result.findings[0].observed_value)
        assert result.findings[0].observed_value > 0

    def test_negative_infinity_produces_finding(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": float("-inf")})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.NEGATIVE_INFINITY
        assert result.findings[0].observed_value < 0

    def test_finite_normal_value_passes_with_profile_range(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 1500.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert result.findings == ()
        assert result.evaluated_count == 1
        assert result.passed_count == 1
        assert result.failed_count == 0
        assert result.score == pytest.approx(1.0, abs=1e-9)


class TestSocUniversalRange:
    def test_soc_minus_one_produces_finding(self) -> None:
        sample = _telemetry({"soc_pct": -1.0})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.reason_code == PlausibilityReasonCode.SOC_OUT_OF_RANGE
        assert finding.signal_name == "soc_pct"
        assert finding.minimum == 0.0
        assert finding.maximum == 100.0
        assert finding.unit == "%"

    def test_soc_101_produces_finding(self) -> None:
        sample = _telemetry({"soc_pct": 101.0})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.SOC_OUT_OF_RANGE

    def test_soc_zero_is_valid_no_finding(self) -> None:
        sample = _telemetry({"soc_pct": 0.0})
        result = evaluate_inverter_telemetry([sample])
        assert result.findings == ()

    def test_soc_100_is_valid_no_finding(self) -> None:
        sample = _telemetry({"soc_pct": 100.0})
        result = evaluate_inverter_telemetry([sample])
        assert result.findings == ()


class TestTemperatureAbsoluteZero:
    def test_below_absolute_zero_produces_finding(self) -> None:
        sample = _telemetry({"temperatura_ambiente_c": -300.0})
        result = evaluate_inverter_telemetry([sample])
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.reason_code == PlausibilityReasonCode.BELOW_ABSOLUTE_ZERO
        assert finding.minimum == -273.15
        assert finding.unit == "C"

    def test_high_temperature_without_profile_is_not_configured(self) -> None:
        sample = _telemetry({"temperatura_ambiente_c": 80.0})
        result = evaluate_inverter_telemetry([sample])
        assert result.findings == ()
        assert result.not_configured_count == 1
        assert result.evaluated_count == 0
        assert result.score is None

    def test_exactly_absolute_zero_does_not_fire(self) -> None:
        sample = _telemetry({"temperatura_ambiente_c": -273.15})
        result = evaluate_inverter_telemetry([sample])
        assert result.findings == ()


class TestProfileRange:
    def test_within_range_passes(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 2000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert result.findings == ()
        assert result.evaluated_count == 1
        assert result.passed_count == 1
        assert result.score == pytest.approx(1.0, abs=1e-9)

    def test_below_minimum_fails(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": -10.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.reason_code == PlausibilityReasonCode.BELOW_MINIMUM
        assert finding.minimum == 0.0
        assert finding.maximum == 5000.0
        assert finding.observed_value == -10.0
        assert result.evaluated_count == 1
        assert result.failed_count == 1
        assert result.score == 0.0

    def test_above_maximum_fails(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.ABOVE_MAXIMUM

    def test_unconfigured_range_does_not_penalize(self) -> None:
        sample = _telemetry({"voltaje_ca_r_u_a_v": 120.0})
        result = evaluate_inverter_telemetry([sample])
        assert result.findings == ()
        assert result.not_configured_count == 1
        assert result.evaluated_count == 0
        assert result.score is None


class TestProfileMetadataPreservation:
    def test_provisional_status_and_source_preserved_in_finding(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(
            _range(
                "potencia_cc_pv1_w",
                minimum=0.0,
                maximum=5000.0,
                unit="W",
                status=PlausibilityStatus.PROVISIONAL,
                source="test-synthetic-source",
                profile_version="0.1.0-test",
            )
        )
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.profile_status == PlausibilityStatus.PROVISIONAL
        assert finding.profile_source == "test-synthetic-source"
        assert finding.profile_version == "0.1.0-test"

    def test_confirmed_status_preserved(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(
            _range(
                "potencia_cc_pv1_w",
                minimum=0.0,
                maximum=5000.0,
                unit="W",
                status=PlausibilityStatus.CONFIRMED,
                source="manufacturer-datasheet",
                profile_version="2.0.0",
            )
        )
        result = evaluate_inverter_telemetry([sample], profile=profile)
        assert result.findings[0].profile_status == PlausibilityStatus.CONFIRMED


class TestOriginalSampleImmutability:
    def test_telemetry_sample_not_mutated(self) -> None:
        signals_before = {"potencia_cc_pv1_w": 1500.0, "current_state_of_machine": "Standby"}
        sample = _telemetry(signals_before)
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        evaluate_inverter_telemetry([sample], profile=profile)
        assert sample.signals == signals_before
        assert sample.timestamp_utc == _TS

    def test_flow_sample_not_mutated(self) -> None:
        sample = _flow(potencia_de_produccion_w=2000.0, soc_pct=50.0)
        profile = _profile(
            _range("potencia_de_produccion_w", minimum=0.0, maximum=5000.0, unit="W")
        )
        evaluate_plant_flow([sample], profile=profile)
        assert sample.potencia_de_produccion_w == 2000.0
        assert sample.soc_pct == 50.0
        assert sample.timestamp_utc == _TS


class TestDeterminism:
    def test_repeated_execution_produces_identical_result(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        r1 = evaluate_inverter_telemetry([sample], profile=profile)
        r2 = evaluate_inverter_telemetry([sample], profile=profile)
        assert r1 == r2


class TestScoreSemantics:
    def test_evaluated_count_zero_implies_none_score(self) -> None:
        result = evaluate_inverter_telemetry([])
        assert result.evaluated_count == 0
        assert result.score is None

    def test_one_failure_of_two_checks_implies_half_score(self) -> None:
        passing = _telemetry({"potencia_cc_pv1_w": 2000.0})
        failing = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([passing, failing], profile=profile)
        assert result.evaluated_count == 2
        assert result.passed_count == 1
        assert result.failed_count == 1
        assert result.score == pytest.approx(0.5, abs=1e-9)

    def test_not_configured_signals_dont_affect_score(self) -> None:
        passing = _telemetry({"potencia_cc_pv1_w": 2000.0})
        unconfigured = _telemetry({"voltaje_ca_r_u_a_v": 120.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([passing, unconfigured], profile=profile)
        assert result.evaluated_count == 1
        assert result.not_configured_count == 1
        assert result.passed_count == 1
        assert result.score == pytest.approx(1.0, abs=1e-9)


class TestSerialization:
    def test_model_dump_contains_findings_and_score(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        dumped = result.model_dump()
        assert "findings" in dumped
        assert "score" in dumped
        assert len(dumped["findings"]) == 1
        assert dumped["score"] == 0.0

    def test_model_dump_json_contains_findings_and_score(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 9000.0})
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = evaluate_inverter_telemetry([sample], profile=profile)
        json_str = result.model_dump_json()
        assert "findings" in json_str
        assert "score" in json_str
        assert "above_maximum" in json_str

    def test_model_dump_json_round_trip_with_nan(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": float("nan")})
        result = evaluate_inverter_telemetry([sample])
        dumped = result.model_dump()
        assert "findings" in dumped
        assert len(dumped["findings"]) == 1
        assert math.isnan(dumped["findings"][0]["observed_value"])


class TestQualityDimensionsIntegration:
    def test_plausibility_score_incorporated_when_evaluated(self) -> None:
        passing = _telemetry({"potencia_cc_pv1_w": 2000.0})
        failing = _telemetry({"potencia_cc_pv1_w": 9000.0})
        samples = [passing, failing]
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        result = analyze_telemetry(
            samples,
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            plausibility_profile=profile,
        )
        assert result.dimensions.plausibility_score == pytest.approx(0.5, abs=1e-9)

    def test_plausibility_score_none_when_no_profile(self) -> None:
        sample = _telemetry({"potencia_cc_pv1_w": 2000.0})
        result = analyze_telemetry([sample], SourceType.SOLARMAN_INVERTER_TELEMETRY)
        assert result.dimensions.plausibility_score is None

    def test_quality_score_unchanged_when_plausibility_score_added(self) -> None:
        clean_samples = [
            _telemetry({"potencia_cc_pv1_w": 1500.0}, timestamp_utc=_TS.replace(minute=m))
            for m in (0, 5, 10, 15)
        ]
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))

        without_profile = analyze_telemetry(clean_samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
        with_profile = analyze_telemetry(
            clean_samples,
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            plausibility_profile=profile,
        )

        assert without_profile.quality_score == with_profile.quality_score
        assert without_profile.dimensions.plausibility_score is None
        assert with_profile.dimensions.plausibility_score == pytest.approx(1.0, abs=1e-9)

    def test_quality_score_unchanged_when_plausibility_partial(self) -> None:
        passing = _telemetry({"potencia_cc_pv1_w": 2000.0}, timestamp_utc=_TS.replace(minute=0))
        failing = _telemetry({"potencia_cc_pv1_w": 9000.0}, timestamp_utc=_TS.replace(minute=5))
        profile = _profile(_range("potencia_cc_pv1_w", minimum=0.0, maximum=5000.0, unit="W"))
        without_profile = analyze_telemetry(
            [passing, failing], SourceType.SOLARMAN_INVERTER_TELEMETRY
        )
        with_profile = analyze_telemetry(
            [passing, failing],
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            plausibility_profile=profile,
        )
        assert without_profile.quality_score == with_profile.quality_score


class TestFlowPlausibility:
    def test_flow_with_nan_in_numeric_field_produces_finding(self) -> None:
        sample = _flow(potencia_de_produccion_w=float("nan"))
        result = evaluate_plant_flow([sample])
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == PlausibilityReasonCode.NAN

    def test_flow_soc_in_range_no_finding(self) -> None:
        sample = _flow(soc_pct=50.0)
        result = evaluate_plant_flow([sample])
        assert result.findings == ()

    def test_flow_soc_out_of_range_blocked_by_pydantic(self) -> None:
        with pytest.raises(ValidationError):
            _flow(soc_pct=120.0)

    def test_flow_with_profile_range_within(self) -> None:
        sample = _flow(potencia_de_produccion_w=2000.0)
        profile = _profile(
            _range("potencia_de_produccion_w", minimum=0.0, maximum=5000.0, unit="W")
        )
        result = evaluate_plant_flow([sample], profile=profile)
        assert result.evaluated_count == 1
        assert result.passed_count == 1
        assert result.score == pytest.approx(1.0, abs=1e-9)


class TestPlausibilityResultConstruction:
    def test_empty_result_is_well_formed(self) -> None:
        result = PlausibilityResult()
        assert result.evaluated_count == 0
        assert result.passed_count == 0
        assert result.failed_count == 0
        assert result.not_configured_count == 0
        assert result.findings == ()
        assert result.score is None

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlausibilityResult(extra_field=True)  # type: ignore[call-arg]

    def test_score_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlausibilityResult(
                evaluated_count=1,
                passed_count=1,
                score=1.5,
            )


class TestMeasurementProfileConstruction:
    def test_empty_profile_well_formed(self) -> None:
        profile = MeasurementPlausibilityProfile(profile_version="0.0.0")
        assert profile.ranges == {}

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MeasurementPlausibilityProfile(
                profile_version="0.0.0",
                extra_field=True,  # type: ignore[call-arg]
            )

    def test_range_minimum_above_maximum_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MeasurementRange(
                canonical_name="voltaje_ca_r_u_a_v",
                unit="V",
                minimum=300.0,
                maximum=100.0,
                source="synthetic",
                status=PlausibilityStatus.PROVISIONAL,
                profile_version="0.0.0",
            )
