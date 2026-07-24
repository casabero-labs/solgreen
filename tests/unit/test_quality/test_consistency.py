from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from solgreen.quality._consistency_types import (
    ConsistencyPair,
    ConsistencyReasonCode,
    ConsistencyResult,
    ConsistencyStatus,
    MeasurementConsistencyProfile,
)
from solgreen.quality._types import QualityDimensions
from solgreen.quality.consistency import (
    apply_consistency_to_dimensions,
    evaluate_consistency,
)
from solgreen.quality.score import aggregate_quality_score
from solgreen.timeline.canonical import CanonicalSample

_TS = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _merged(
    *,
    flow_soc: float | None = None,
    telemetry_soc: float | None = None,
    time_delta: timedelta | None = None,
) -> CanonicalSample:
    return CanonicalSample(
        timestamp_axis=_TS,
        source="merged",
        time_delta=time_delta,
        flow_soc_pct=flow_soc,
        telemetry_soc_pct=telemetry_soc,
    )


def _flow_only(**kwargs: object) -> CanonicalSample:
    return CanonicalSample(
        timestamp_axis=_TS,
        source="flow",
        **kwargs,
    )


def _telemetry_only(**kwargs: object) -> CanonicalSample:
    return CanonicalSample(
        timestamp_axis=_TS,
        source="telemetry",
        **kwargs,
    )


def _soc_pair(
    *,
    absolute_tolerance: float | None = 1.0,
    relative_tolerance: float | None = None,
    max_alignment_delta: timedelta = timedelta(seconds=150),
    status: ConsistencyStatus = ConsistencyStatus.PROVISIONAL,
    source: str = "synthetic-test-profile",
) -> ConsistencyPair:
    return ConsistencyPair(
        pair_id="SOC-001",
        pair_version="1.0.0",
        flow_field="flow_soc_pct",
        telemetry_field="telemetry_soc_pct",
        unit="%",
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        max_alignment_delta=max_alignment_delta,
        source=source,
        status=status,
        profile_version="0.0.1-test",
    )


def _profile(*pairs: ConsistencyPair) -> MeasurementConsistencyProfile:
    return MeasurementConsistencyProfile(
        profile_version="0.0.1-test",
        pairs=tuple(pairs),
    )


class TestConsistencyPairContract:
    def test_empty_profile_is_valid(self) -> None:
        p = MeasurementConsistencyProfile(profile_version="0.0.0")
        assert p.pairs == ()

    def test_pair_without_tolerances_rejected(self) -> None:
        with pytest.raises(ValidationError, match="At least one"):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="flow_soc_pct",
                telemetry_field="telemetry_soc_pct",
                unit="%",
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_negative_absolute_tolerance_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="flow_soc_pct",
                telemetry_field="telemetry_soc_pct",
                unit="%",
                absolute_tolerance=-1.0,
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_flow_field_nonexistent_rejected(self) -> None:
        with pytest.raises(ValidationError, match="does not exist"):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="flow_nonexistent",
                telemetry_field="telemetry_soc_pct",
                unit="%",
                absolute_tolerance=1.0,
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_telemetry_field_nonexistent_rejected(self) -> None:
        with pytest.raises(ValidationError, match="does not exist"):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="flow_soc_pct",
                telemetry_field="telemetry_nonexistent",
                unit="%",
                absolute_tolerance=1.0,
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_flow_flow_pair_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must start with"):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="flow_soc_pct",
                telemetry_field="flow_grid_w",
                unit="%",
                absolute_tolerance=1.0,
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_telemetry_telemetry_pair_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must start with"):
            ConsistencyPair(
                pair_id="X",
                pair_version="1.0.0",
                flow_field="telemetry_soc_pct",
                telemetry_field="telemetry_soc_pct",
                unit="%",
                absolute_tolerance=1.0,
                source="s",
                status=ConsistencyStatus.PROVISIONAL,
                profile_version="0.0.0",
            )

    def test_duplicate_pairs_rejected(self) -> None:
        pair = _soc_pair()
        with pytest.raises(ValidationError, match="Duplicate"):
            _profile(pair, pair)

    def test_serialization_round_trip(self) -> None:
        profile = _profile(_soc_pair())
        data = profile.model_dump()
        parsed = MeasurementConsistencyProfile.model_validate(data)
        assert parsed.profile_version == profile.profile_version
        assert len(parsed.pairs) == 1

    def test_models_are_frozen(self) -> None:
        result = ConsistencyResult()
        with pytest.raises(ValidationError, match="frozen"):
            result.evaluated_count = 1  # type: ignore[misc]
        pair = _soc_pair()
        with pytest.raises(ValidationError, match="frozen"):
            pair.unit = "W"  # type: ignore[misc]


class TestSocEvaluation:
    def test_equal_values_pass(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=50.0)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        assert result.passed_count == 1
        assert result.failed_count == 0
        assert result.findings == ()
        assert result.score == pytest.approx(1.0, abs=1e-9)

    def test_within_absolute_tolerance_passes(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=50.5)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.passed_count == 1
        assert result.failed_count == 0

    def test_outside_absolute_tolerance_fails(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=52.0)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        assert result.failed_count == 1
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == ConsistencyReasonCode.OUTSIDE_TOLERANCE
        assert result.score == 0.0

    def test_at_exact_limit_passes(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=51.0)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.passed_count == 1

    def test_relative_tolerance_works(self) -> None:
        samples = [_merged(flow_soc=100.0, telemetry_soc=105.0)]
        profile = _profile(_soc_pair(absolute_tolerance=None, relative_tolerance=0.05))
        result = evaluate_consistency(samples, profile=profile)
        assert result.passed_count == 1

    def test_relative_tolerance_above_fails(self) -> None:
        samples = [_merged(flow_soc=100.0, telemetry_soc=106.0)]
        profile = _profile(_soc_pair(absolute_tolerance=None, relative_tolerance=0.05))
        result = evaluate_consistency(samples, profile=profile)
        assert result.failed_count == 1

    def test_both_zero_pass(self) -> None:
        samples = [_merged(flow_soc=0.0, telemetry_soc=0.0)]
        profile = _profile(_soc_pair(absolute_tolerance=0.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.passed_count == 1

    def test_one_none_increments_skipped_missing(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=None)]
        profile = _profile(_soc_pair())
        result = evaluate_consistency(samples, profile=profile)
        assert result.skipped_missing_count == 1
        assert result.evaluated_count == 0
        assert result.score is None

    def test_nan_increments_skipped_nonfinite(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=float("nan"))]
        profile = _profile(_soc_pair())
        result = evaluate_consistency(samples, profile=profile)
        assert result.skipped_nonfinite_count == 1
        assert len(result.findings) == 1
        assert result.findings[0].reason_code == ConsistencyReasonCode.NONFINITE_VALUE
        assert result.evaluated_count == 0

    def test_infinity_increments_skipped_nonfinite(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=float("inf"))]
        profile = _profile(_soc_pair())
        result = evaluate_consistency(samples, profile=profile)
        assert result.skipped_nonfinite_count == 1
        assert result.findings[0].reason_code == ConsistencyReasonCode.NONFINITE_VALUE

    def test_flow_only_sample_ignored(self) -> None:
        samples = [_flow_only(flow_soc_pct=50.0)]
        profile = _profile(_soc_pair())
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 0
        assert result.skipped_missing_count == 0

    def test_telemetry_only_sample_ignored(self) -> None:
        samples = [_telemetry_only(telemetry_soc_pct=50.0)]
        profile = _profile(_soc_pair())
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 0
        assert result.skipped_missing_count == 0

    def test_time_delta_within_limit_evaluated(self) -> None:
        samples = [
            _merged(
                flow_soc=50.0,
                telemetry_soc=50.0,
                time_delta=timedelta(minutes=2),
            )
        ]
        profile = _profile(_soc_pair(max_alignment_delta=timedelta(minutes=2, seconds=30)))
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        assert result.skipped_alignment_count == 0

    def test_time_delta_exceeds_limit_skipped(self) -> None:
        samples = [
            _merged(
                flow_soc=50.0,
                telemetry_soc=50.0,
                time_delta=timedelta(minutes=5),
            )
        ]
        profile = _profile(_soc_pair(max_alignment_delta=timedelta(minutes=2, seconds=30)))
        result = evaluate_consistency(samples, profile=profile)
        assert result.skipped_alignment_count == 1
        assert result.evaluated_count == 0

    def test_failure_produces_structured_finding(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=60.0)]
        profile = _profile(
            _soc_pair(
                absolute_tolerance=1.0,
                source="manual-review",
                status=ConsistencyStatus.CONFIRMED,
            )
        )
        result = evaluate_consistency(samples, profile=profile)
        f = result.findings[0]
        assert f.pair_id == "SOC-001"
        assert f.flow_value == 50.0
        assert f.telemetry_value == 60.0
        assert f.absolute_difference == 10.0
        assert f.allowed_difference == 1.0
        assert f.unit == "%"
        assert f.profile_status == ConsistencyStatus.CONFIRMED
        assert f.profile_source == "manual-review"
        assert f.reason_code == ConsistencyReasonCode.OUTSIDE_TOLERANCE

    def test_pass_produces_no_finding(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=50.0)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.findings == ()

    def test_multiple_samples_correct_score(self) -> None:
        samples = [
            _merged(flow_soc=50.0, telemetry_soc=50.0),
            _merged(flow_soc=50.0, telemetry_soc=60.0),
            _merged(flow_soc=50.0, telemetry_soc=50.0),
        ]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 3
        assert result.passed_count == 2
        assert result.failed_count == 1
        assert result.score == pytest.approx(2 / 3, abs=1e-9)

    def test_invariant_evaluated_equals_passed_plus_failed(self) -> None:
        samples = [
            _merged(flow_soc=50.0, telemetry_soc=50.0),
            _merged(flow_soc=50.0, telemetry_soc=60.0),
            _merged(flow_soc=50.0, telemetry_soc=50.5),
        ]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == result.passed_count + result.failed_count

    def test_evaluated_zero_implies_none_score(self) -> None:
        result = evaluate_consistency([], profile=_profile(_soc_pair()))
        assert result.evaluated_count == 0
        assert result.score is None

    def test_determinism(self) -> None:
        samples = [
            _merged(flow_soc=50.0, telemetry_soc=51.0),
            _merged(flow_soc=50.0, telemetry_soc=52.0),
        ]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        r1 = evaluate_consistency(samples, profile=profile)
        r2 = evaluate_consistency(samples, profile=profile)
        assert r1 == r2

    def test_original_samples_not_mutated(self) -> None:
        samples = [
            _merged(flow_soc=50.0, telemetry_soc=55.0),
        ]
        flow_before = samples[0].flow_soc_pct
        tel_before = samples[0].telemetry_soc_pct
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        evaluate_consistency(samples, profile=profile)
        assert samples[0].flow_soc_pct == flow_before
        assert samples[0].telemetry_soc_pct == tel_before


class TestSemanticSafety:
    def test_no_automatic_pv_comparison(self) -> None:
        soc_pair = _soc_pair()
        profile = _profile(soc_pair)
        samples = [
            CanonicalSample(
                timestamp_axis=_TS,
                source="merged",
                flow_potencia_produccion_w=1000.0,
                telemetry_pv_power_w=900.0,
                flow_soc_pct=50.0,
                telemetry_soc_pct=50.0,
            )
        ]
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        for f in result.findings:
            assert "pv" not in f.flow_field.lower()
            assert "pv" not in f.telemetry_field.lower()

    def test_no_automatic_grid_comparison(self) -> None:
        profile = _profile(_soc_pair())
        samples = [
            CanonicalSample(
                timestamp_axis=_TS,
                source="merged",
                flow_grid_w=500.0,
                telemetry_grid_power_w=600.0,
                flow_soc_pct=50.0,
                telemetry_soc_pct=50.0,
            )
        ]
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        for f in result.findings:
            assert "grid" not in f.flow_field.lower()
            assert "grid" not in f.telemetry_field.lower()

    def test_no_automatic_battery_comparison(self) -> None:
        profile = _profile(_soc_pair())
        samples = [
            CanonicalSample(
                timestamp_axis=_TS,
                source="merged",
                flow_battery_w=200.0,
                telemetry_battery_power_w=250.0,
                flow_soc_pct=50.0,
                telemetry_soc_pct=50.0,
            )
        ]
        result = evaluate_consistency(samples, profile=profile)
        assert result.evaluated_count == 1
        for f in result.findings:
            assert "battery" not in f.flow_field.lower()
            assert "battery" not in f.telemetry_field.lower()

    def test_quality_score_unchanged_when_consistency_score_added(self) -> None:
        dims = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        samples = [_merged(flow_soc=50.0, telemetry_soc=50.0)]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        score_before = aggregate_quality_score(dims)
        updated = apply_consistency_to_dimensions(dims, samples, profile)
        score_after = aggregate_quality_score(updated)
        assert score_before == score_after
        assert updated.consistency_score == pytest.approx(1.0, abs=1e-9)

    def test_consistency_score_none_without_evaluations(self) -> None:
        dims = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        updated = apply_consistency_to_dimensions(dims, [], None)
        assert updated.consistency_score is None

    def test_consistency_score_incorporated_when_evaluated(self) -> None:
        dims = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        samples = [
            _merged(flow_soc=50.0, telemetry_soc=50.0),
            _merged(flow_soc=50.0, telemetry_soc=60.0),
        ]
        profile = _profile(_soc_pair(absolute_tolerance=1.0))
        updated = apply_consistency_to_dimensions(dims, samples, profile)
        assert updated.consistency_score == pytest.approx(0.5, abs=1e-9)


class TestToleranceFormula:
    def test_absolute_takes_max_of_components(self) -> None:
        from solgreen.quality.consistency import _compute_allowed_difference

        allowed = _compute_allowed_difference(100.0, 100.0, 2.0, 0.01)
        assert allowed == 2.0

    def test_relative_can_exceed_absolute(self) -> None:
        from solgreen.quality.consistency import _compute_allowed_difference

        allowed = _compute_allowed_difference(1000.0, 1000.0, 1.0, 0.05)
        assert allowed == pytest.approx(50.0, abs=1e-9)

    def test_passes_when_diff_equals_allowed(self) -> None:
        samples = [_merged(flow_soc=50.0, telemetry_soc=55.0)]
        profile = _profile(_soc_pair(absolute_tolerance=5.0))
        result = evaluate_consistency(samples, profile=profile)
        assert result.passed_count == 1


class TestConsistencyResultInvariants:
    def test_evaluated_count_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            ConsistencyResult(
                evaluated_count=2,
                passed_count=1,
                failed_count=0,
                score=0.5,
            )

    def test_zero_evaluated_with_score_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            ConsistencyResult(
                evaluated_count=0,
                passed_count=0,
                failed_count=0,
                score=0.5,
            )

    def test_nonzero_evaluated_with_none_score_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            ConsistencyResult(
                evaluated_count=2,
                passed_count=1,
                failed_count=1,
                score=None,
            )

    def test_score_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="invariant"):
            ConsistencyResult(
                evaluated_count=3,
                passed_count=1,
                failed_count=2,
                score=0.9,
            )

    def test_valid_construction_succeeds(self) -> None:
        result = ConsistencyResult(
            evaluated_count=4,
            passed_count=3,
            failed_count=1,
            score=0.75,
        )
        assert result.score == 0.75


class TestApplyToDimensionsNoProfile:
    def test_none_profile_returns_unchanged(self) -> None:
        dims = QualityDimensions(temporal_coverage=1.0, duplicate_integrity=1.0)
        updated = apply_consistency_to_dimensions(
            dims, [_merged(flow_soc=50.0, telemetry_soc=50.0)], None
        )
        assert updated is dims
