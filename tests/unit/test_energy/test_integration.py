from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pydantic
import pytest

from solgreen.energy.integration import (
    DirectionalPowerObservation,
    EnergyInterval,
    EnergySeriesIdentity,
    EnergySummary,
    IntegrationMethod,
    IntegrationProfile,
    IntegrationResult,
    IntervalStatus,
    SampleSemantics,
    integrate_energy,
)
from solgreen.energy.normalization import NormalizationStatus
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerDirection,
    SourceSystem,
)

_TS0 = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)

_M5 = timedelta(minutes=5)
_M10 = timedelta(minutes=10)
_M15 = timedelta(minutes=15)
_M20 = timedelta(minutes=20)
_H1 = timedelta(hours=1)
_H2 = timedelta(hours=2)

_GRID = CanonicalPowerField.FLOW_GRID
_SOLARMAN = SourceSystem.SOLARMAN_PLANT_FLOW
_IMPORT = PowerDirection.GRID_IMPORT
_EXPORT = PowerDirection.GRID_EXPORT
_LOAD = PowerDirection.LOAD_CONSUMPTION
_CHARGE = PowerDirection.BATTERY_CHARGE
_DISCHARGE = PowerDirection.BATTERY_DISCHARGE
_PV = PowerDirection.PV_GENERATION
_ZONE = UTC

_SERIES_GRID_IMPORT = EnergySeriesIdentity(
    source_field=_GRID,
    source_system=_SOLARMAN,
    direction=_IMPORT,
)

_SERIES_GRID_EXPORT = EnergySeriesIdentity(
    source_field=_GRID,
    source_system=_SOLARMAN,
    direction=_EXPORT,
)

_SERIES_BATTERY_CHARGE = EnergySeriesIdentity(
    source_field=CanonicalPowerField.FLOW_BATTERY,
    source_system=_SOLARMAN,
    direction=_CHARGE,
)


def _obs(
    timestamp: datetime,
    power_w: float | None = None,
    status: NormalizationStatus = NormalizationStatus.NORMALIZED,
    profile_version: str = "1.0.0",
    direction: PowerDirection = _IMPORT,
    source: CanonicalPowerField = _GRID,
    system: SourceSystem = _SOLARMAN,
    lineage: tuple[str, ...] = (),
) -> DirectionalPowerObservation:
    pv = profile_version if status is NormalizationStatus.NORMALIZED else None
    return DirectionalPowerObservation(
        timestamp=timestamp,
        canonical_source=source,
        source_system=system,
        direction=direction,
        power_w=power_w,
        status=status,
        profile_version=pv,
        lineage=lineage,
    )


def _profile(
    sample_semantics: SampleSemantics = SampleSemantics.INSTANTANEOUS,
    integration_method: IntegrationMethod = IntegrationMethod.TRAPEZOIDAL,
    expected_interval: timedelta = _M5,
    max_authorized: timedelta = _H2,
) -> IntegrationProfile:
    return IntegrationProfile(
        profile_version="int-1.0.0",
        sample_semantics=sample_semantics,
        integration_method=integration_method,
        expected_interval=expected_interval,
        maximum_authorized_interval=max_authorized,
    )


_P = _profile()
_TS = _TS0


# ---------------------------------------------------------------------------
# Model validation — DirectionalPowerObservation
# ---------------------------------------------------------------------------


class TestDirectionalPowerObservationValidation:
    def test_naive_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            DirectionalPowerObservation(
                timestamp=datetime(2026, 7, 24, 12, 0, 0),
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
            )

    def test_nonfinite_power_rejected(self) -> None:
        for bad in (float("nan"), float("inf"), -float("inf")):
            with pytest.raises(ValueError, match="finite"):
                DirectionalPowerObservation(
                    timestamp=_TS,
                    canonical_source=_GRID,
                    source_system=_SOLARMAN,
                    direction=_IMPORT,
                    power_w=bad,
                    status=NormalizationStatus.NORMALIZED,
                    profile_version="1.0.0",
                )

    def test_negative_directional_power_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            DirectionalPowerObservation(
                timestamp=_TS,
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                power_w=-100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
            )

    def test_normalized_without_profile_version_rejected(self) -> None:
        with pytest.raises(ValueError, match="profile_version"):
            DirectionalPowerObservation(
                timestamp=_TS,
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version=None,
            )

    def test_normalized_power_none_rejected(self) -> None:
        with pytest.raises(ValueError, match="power_w set"):
            DirectionalPowerObservation(
                timestamp=_TS,
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                power_w=None,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
            )

    def test_non_normalized_with_power_rejected(self) -> None:
        with pytest.raises(ValueError, match="power_w=None"):
            DirectionalPowerObservation(
                timestamp=_TS,
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                power_w=100.0,
                status=NormalizationStatus.MISSING_VALUE,
                profile_version=None,
            )

    def test_non_normalized_profile_version_none(self) -> None:
        obs = _obs(
            _TS,
            power_w=None,
            status=NormalizationStatus.MISSING_VALUE,
            profile_version=None,
        )
        assert obs.profile_version is None

    def test_invalid_direction_rejected(self) -> None:
        with pytest.raises(ValueError, match="direction must be one of"):
            DirectionalPowerObservation(
                timestamp=_TS,
                canonical_source=_GRID,
                source_system=_SOLARMAN,
                direction=PowerDirection.UNKNOWN,
                power_w=None,
                status=NormalizationStatus.MISSING_VALUE,
            )

    def test_valid_observation_accepted(self) -> None:
        obs = _obs(_TS, 100.0)
        assert obs.power_w == 100.0
        assert obs.status is NormalizationStatus.NORMALIZED

    def test_missing_observation_accepted(self) -> None:
        obs = _obs(
            _TS,
            power_w=None,
            status=NormalizationStatus.MISSING_VALUE,
        )
        assert obs.power_w is None
        assert obs.status is NormalizationStatus.MISSING_VALUE

    def test_frozen_model_immutable(self) -> None:
        obs = _obs(_TS, 100.0)
        with pytest.raises(pydantic.ValidationError, match="frozen"):
            obs.power_w = 200.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Model validation — IntegrationProfile
# ---------------------------------------------------------------------------


class TestIntegrationProfileValidation:
    def test_unsupported_sample_semantics_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"Only SampleSemantics\.INSTANTANEOUS"):
            IntegrationProfile(
                profile_version="1.0.0",
                sample_semantics=SampleSemantics.INTERVAL_AVERAGE,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=_M5,
                maximum_authorized_interval=_M15,
            )

    def test_unknown_sample_semantics_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"Only SampleSemantics\.INSTANTANEOUS"):
            IntegrationProfile(
                profile_version="1.0.0",
                sample_semantics=SampleSemantics.UNKNOWN,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=_M5,
                maximum_authorized_interval=_M15,
            )

    def test_negative_expected_interval_rejected(self) -> None:
        with pytest.raises(ValueError, match="strictly positive"):
            IntegrationProfile(
                profile_version="1.0.0",
                sample_semantics=SampleSemantics.INSTANTANEOUS,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=timedelta(seconds=-1),
                maximum_authorized_interval=_M15,
            )

    def test_zero_expected_interval_rejected(self) -> None:
        with pytest.raises(ValueError, match="strictly positive"):
            IntegrationProfile(
                profile_version="1.0.0",
                sample_semantics=SampleSemantics.INSTANTANEOUS,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=timedelta(0),
                maximum_authorized_interval=_M15,
            )

    def test_maximum_less_than_expected_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be >= expected_interval"):
            IntegrationProfile(
                profile_version="1.0.0",
                sample_semantics=SampleSemantics.INSTANTANEOUS,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                expected_interval=_M10,
                maximum_authorized_interval=_M5,
            )


# ---------------------------------------------------------------------------
# Model validation — EnergySeriesIdentity
# ---------------------------------------------------------------------------


class TestEnergySeriesIdentity:
    def test_valid_identity_accepted(self) -> None:
        id_ = EnergySeriesIdentity(
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
        )
        assert id_.source_field == _GRID

    def test_invalid_direction_rejected(self) -> None:
        with pytest.raises(ValueError, match="direction must be one of"):
            EnergySeriesIdentity(
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=PowerDirection.UNKNOWN,
            )

    def test_frozen(self) -> None:
        id_ = EnergySeriesIdentity(
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
        )
        with pytest.raises(pydantic.ValidationError, match="frozen"):
            id_.direction = _EXPORT  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Model validation — EnergyInterval
# ---------------------------------------------------------------------------


class TestEnergyIntervalValidation:
    def test_observed_must_have_energy(self) -> None:
        with pytest.raises(ValueError, match="energy_wh set"):
            EnergyInterval(
                start=_TS,
                end=_TS + _H1,
                duration=_H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                start_power_w=100.0,
                end_power_w=100.0,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                energy_wh=None,
                status=IntervalStatus.OBSERVED,
                sign_profile_version="1.0.0",
            )

    def test_non_observed_must_not_have_energy(self) -> None:
        with pytest.raises(ValueError, match="energy_wh=None"):
            EnergyInterval(
                start=_TS,
                end=_TS + _H1,
                duration=_H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                integration_method=IntegrationMethod.TRAPEZOIDAL,
                energy_wh=500.0,
                status=IntervalStatus.MISSING,
            )


# ---------------------------------------------------------------------------
# Model validation — EnergySummary
# ---------------------------------------------------------------------------


class TestEnergySummaryValidation:
    def test_kwh_conversion_exact(self) -> None:
        s = EnergySummary(
            period_start=_TS,
            period_end=_TS + _H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            observed_energy_wh=1000.0,
            observed_energy_kwh=1.0,
            expected_duration=_H1,
            observed_duration=_H1,
            coverage_fraction=1.0,
        )
        assert s.observed_energy_kwh == 1.0

    def test_kwh_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_energy_kwh"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=1000.0,
                observed_energy_kwh=999.0,
                expected_duration=_H1,
                observed_duration=_H1,
                coverage_fraction=1.0,
            )

    def test_coverage_fraction_out_of_bounds_rejected(self) -> None:
        with pytest.raises(ValueError, match="coverage_fraction must be in"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=0.0,
                observed_energy_kwh=0.0,
                expected_duration=_H1,
                observed_duration=_H1,
                missing_duration=timedelta(0),
                excluded_duration=timedelta(0),
                coverage_fraction=2.0,
            )

    def test_coverage_fraction_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="coverage_fraction"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=0.0,
                observed_energy_kwh=0.0,
                expected_duration=_H1,
                observed_duration=_M5,
                missing_duration=_H1 - _M5,
                excluded_duration=timedelta(0),
                coverage_fraction=0.5,
            )

    def test_negative_energy_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_energy_wh"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=-1.0,
                observed_energy_kwh=-0.001,
                expected_duration=_H1,
                observed_duration=_H1,
                missing_duration=timedelta(0),
                excluded_duration=timedelta(0),
                coverage_fraction=1.0,
            )

    def test_naive_period_start_rejected(self) -> None:
        with pytest.raises(ValueError, match="period_start must be timezone-aware"):
            EnergySummary(
                period_start=datetime(2026, 7, 24, 12, 0, 0),
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
            )

    def test_naive_period_end_rejected(self) -> None:
        with pytest.raises(ValueError, match="period_end must be timezone-aware"):
            EnergySummary(
                period_start=_TS,
                period_end=datetime(2026, 7, 24, 13, 0, 0),
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
            )

    def test_reversed_period_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"period_end.*must be >.*period_start"):
            EnergySummary(
                period_start=_TS + _H1,
                period_end=_TS,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=timedelta(0),
                observed_duration=timedelta(0),
                missing_duration=timedelta(0),
                excluded_duration=timedelta(0),
            )

    def test_zero_period_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"period_end.*must be >.*period_start"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=timedelta(0),
                observed_duration=timedelta(0),
                missing_duration=timedelta(0),
                excluded_duration=timedelta(0),
            )

    def test_incorrect_expected_duration_rejected(self) -> None:
        with pytest.raises(
            ValueError, match=r"expected_duration.*must equal.*period_end.*period_start"
        ):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_M5,
                observed_duration=timedelta(0),
                missing_duration=timedelta(0),
                excluded_duration=timedelta(0),
            )

    def test_negative_observed_duration_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_duration must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(seconds=-1),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
            )

    def test_negative_missing_duration_rejected(self) -> None:
        with pytest.raises(ValueError, match="missing_duration must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=timedelta(seconds=-1),
                excluded_duration=_H1,
            )

    def test_negative_excluded_duration_rejected(self) -> None:
        with pytest.raises(ValueError, match="excluded_duration must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(seconds=-1),
            )

    def test_duration_partition_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="duration partition must reconcile"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(minutes=30),
                missing_duration=timedelta(minutes=10),
                excluded_duration=timedelta(minutes=10),
            )

    def test_negative_interval_count_rejected(self) -> None:
        with pytest.raises(ValueError, match="interval_count must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=-1,
            )

    def test_negative_observed_interval_count_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_interval_count must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=1,
                observed_interval_count=-1,
            )

    def test_negative_excluded_interval_count_rejected(self) -> None:
        with pytest.raises(ValueError, match="excluded_interval_count must be >= 0"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=1,
                excluded_interval_count=-1,
            )

    def test_observed_count_exceeds_interval_count_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"observed_interval_count.*must be <= interval_count"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=1,
                observed_interval_count=2,
            )

    def test_excluded_count_exceeds_interval_count_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"excluded_interval_count.*must be <= interval_count"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=1,
                excluded_interval_count=2,
            )

    def test_counter_reconciliation_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"observed_interval_count.*must equal interval_count"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                interval_count=5,
                observed_interval_count=2,
                excluded_interval_count=2,
            )

    def test_nan_energy_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_energy_wh must be finite"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=float("nan"),
                observed_energy_kwh=float("nan"),
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
            )

    def test_inf_energy_rejected(self) -> None:
        with pytest.raises(ValueError, match="observed_energy_wh must be finite"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                observed_energy_wh=float("inf"),
                observed_energy_kwh=float("inf"),
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
            )

    def test_nan_coverage_rejected(self) -> None:
        with pytest.raises(ValueError, match="coverage_fraction must be finite"):
            EnergySummary(
                period_start=_TS,
                period_end=_TS + _H1,
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=_IMPORT,
                expected_duration=_H1,
                observed_duration=timedelta(0),
                missing_duration=_H1,
                excluded_duration=timedelta(0),
                coverage_fraction=float("nan"),
            )


# ---------------------------------------------------------------------------
# Model validation — IntegrationResult
# ---------------------------------------------------------------------------


class TestIntegrationResultValidation:
    def test_wrong_interval_count_rejected(self) -> None:
        summary = EnergySummary(
            period_start=_TS,
            period_end=_TS + _H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            expected_duration=_H1,
            observed_duration=timedelta(0),
            missing_duration=timedelta(0),
            excluded_duration=_H1,
            coverage_fraction=0.0,
            interval_count=5,
            observed_interval_count=0,
            excluded_interval_count=5,
        )
        interval = EnergyInterval(
            start=_TS,
            end=_TS + _H1,
            duration=_H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            integration_method=IntegrationMethod.TRAPEZOIDAL,
            energy_wh=None,
            status=IntervalStatus.MISSING,
        )
        with pytest.raises(ValueError, match=r"interval_count.*must equal len"):
            IntegrationResult(intervals=(interval,), summary=summary)

    def test_wrong_observed_count_rejected(self) -> None:
        summary = EnergySummary(
            period_start=_TS,
            period_end=_TS + _H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            expected_duration=_H1,
            observed_duration=timedelta(0),
            missing_duration=timedelta(0),
            excluded_duration=_H1,
            coverage_fraction=0.0,
            interval_count=1,
            observed_interval_count=0,
            excluded_interval_count=1,
        )
        interval = EnergyInterval(
            start=_TS,
            end=_TS + _H1,
            duration=_H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            start_power_w=100.0,
            end_power_w=100.0,
            integration_method=IntegrationMethod.TRAPEZOIDAL,
            energy_wh=100.0,
            status=IntervalStatus.OBSERVED,
            sign_profile_version="1.0.0",
        )
        with pytest.raises(ValueError, match=r"observed_interval_count.*must equal actual"):
            IntegrationResult(intervals=(interval,), summary=summary)

    def test_wrong_energy_total_rejected(self) -> None:
        summary = EnergySummary(
            period_start=_TS,
            period_end=_TS + _H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            expected_duration=_H1,
            observed_duration=_H1,
            missing_duration=timedelta(0),
            excluded_duration=timedelta(0),
            coverage_fraction=1.0,
            observed_energy_wh=999.0,
            observed_energy_kwh=0.999,
            interval_count=1,
            observed_interval_count=1,
            excluded_interval_count=0,
        )
        interval = EnergyInterval(
            start=_TS,
            end=_TS + _H1,
            duration=_H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            start_power_w=100.0,
            end_power_w=100.0,
            integration_method=IntegrationMethod.TRAPEZOIDAL,
            energy_wh=100.0,
            status=IntervalStatus.OBSERVED,
            sign_profile_version="1.0.0",
        )
        with pytest.raises(ValueError, match=r"sum of observed interval energies.*must equal"):
            IntegrationResult(intervals=(interval,), summary=summary)


# ---------------------------------------------------------------------------
# Integration behavior — happy path
# ---------------------------------------------------------------------------


class TestIntegrationHappyPath:
    def test_constant_1000w_one_hour_equals_1000wh(self) -> None:
        obs = [
            _obs(_TS, 1000.0),
            _obs(_TS + _H1, 1000.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert len(result.intervals) == 1
        ival = result.intervals[0]
        assert ival.status is IntervalStatus.OBSERVED
        assert ival.energy_wh == pytest.approx(1000.0)
        assert result.summary.observed_energy_wh == pytest.approx(1000.0)
        assert result.summary.observed_energy_kwh == pytest.approx(1.0)
        assert result.summary.coverage_fraction == pytest.approx(1.0)

    def test_linear_ramp_0_to_1000_over_one_hour_equals_500wh(self) -> None:
        obs = [
            _obs(_TS, 0.0),
            _obs(_TS + _H1, 1000.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.intervals[0].energy_wh == pytest.approx(500.0)
        assert result.summary.observed_energy_wh == pytest.approx(500.0)
        assert result.summary.coverage_fraction == pytest.approx(1.0)

    def test_zero_power_over_valid_hour_is_observed(self) -> None:
        obs = [
            _obs(_TS, 0.0),
            _obs(_TS + _H1, 0.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.intervals[0].status is IntervalStatus.OBSERVED
        assert result.intervals[0].energy_wh == 0.0
        assert result.summary.observed_energy_wh == 0.0
        assert result.summary.coverage_fraction == pytest.approx(1.0)

    def test_irregular_authorized_interval_integrates(self) -> None:
        p = _profile(max_authorized=timedelta(minutes=7))
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + timedelta(minutes=6), 300.0),
        ]
        duration_h = 6.0 / 60.0
        expected = ((100.0 + 300.0) / 2.0) * duration_h
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=p,
            period_start=_TS,
            period_end=_TS + timedelta(minutes=6),
        )
        assert result.intervals[0].energy_wh == pytest.approx(expected)

    def test_multiple_intervals_accumulate_energy(self) -> None:
        obs = [
            _obs(_TS, 500.0),
            _obs(_TS + _H1, 500.0),
            _obs(_TS + _H2, 500.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H2,
        )
        assert len(result.intervals) == 2
        assert result.summary.observed_energy_wh == pytest.approx(1000.0)

    def test_wh_to_kwh_conversion_exact(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _H1, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.observed_energy_wh == pytest.approx(100.0)
        assert result.summary.observed_energy_kwh == pytest.approx(0.1)

    def test_durations_and_interval_counters_reconcile(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _H1, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        s = result.summary
        assert s.interval_count == 1
        assert s.observed_interval_count == 1
        assert s.excluded_interval_count == 0
        assert s.observed_duration == _H1
        assert s.missing_duration == timedelta(0)
        assert s.expected_duration == _H1


# ---------------------------------------------------------------------------
# Gap and boundary policies
# ---------------------------------------------------------------------------


class TestGapPolicy:
    def test_interval_above_max_authorized_is_missing(self) -> None:
        p = _profile(max_authorized=_M5)
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _M10, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=p,
            period_start=_TS,
            period_end=_TS + _M10,
        )
        assert result.intervals[0].status is IntervalStatus.MISSING
        assert result.intervals[0].energy_wh is None
        assert result.summary.observed_energy_wh == 0.0
        assert result.summary.missing_duration == _M10

    def test_uncovered_leading_boundary_counts_as_missing(self) -> None:
        obs = [
            _obs(_TS + _M5, 100.0),
            _obs(_TS + _M10, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M10,
        )
        assert result.summary.missing_duration == _M5
        assert result.summary.coverage_fraction < 1.0

    def test_uncovered_trailing_boundary_counts_as_missing(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _M5, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M15,
        )
        assert result.summary.missing_duration == _M10
        assert result.summary.coverage_fraction < 1.0

    def test_observations_outside_period_are_filtered(self) -> None:
        p = _profile(max_authorized=_M10)
        obs = [
            _obs(_TS - _H1, 999.0),
            _obs(_TS, 100.0),
            _obs(_TS + _M5, 200.0),
            _obs(_TS + _H2, 999.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=p,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        assert len(result.intervals) == 1
        assert result.intervals[0].status is IntervalStatus.OBSERVED


# ---------------------------------------------------------------------------
# Edge cases — empty, single, duplicates
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_input_produces_zero_energy_zero_coverage(self) -> None:
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.observed_energy_wh == 0.0
        assert result.summary.observed_energy_kwh == 0.0
        assert result.summary.coverage_fraction == 0.0
        assert result.summary.observed_duration == timedelta(0)
        assert result.summary.missing_duration == _H1
        assert result.summary.interval_count == 0
        assert len(result.intervals) == 0
        assert "empty_series" in result.summary.warnings

    def test_empty_grid_import_series_preserves_identity(self) -> None:
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.source_field == _GRID
        assert result.summary.source_system == _SOLARMAN
        assert result.summary.direction == _IMPORT

    def test_empty_battery_charge_series_preserves_identity(self) -> None:
        result = integrate_energy(
            series=_SERIES_BATTERY_CHARGE,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.source_field == CanonicalPowerField.FLOW_BATTERY
        assert result.summary.direction == _CHARGE

    def test_observations_outside_window_preserve_identity(self) -> None:
        obs = [
            _obs(_TS - _H1, 100.0),
            _obs(_TS - _H1 + _M5, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.source_field == _GRID
        assert result.summary.direction == _IMPORT

    def test_single_observation_produces_zero_energy_zero_coverage(self) -> None:
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[_obs(_TS, 500.0)],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.observed_energy_wh == 0.0
        assert result.summary.coverage_fraction == 0.0
        assert result.summary.missing_duration == _H1
        assert result.summary.interval_count == 0
        assert "single_observation_no_intervals" in result.summary.warnings

    def test_duplicate_timestamp_produces_excluded_zero_duration(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS, 200.0),
            _obs(_TS + _H1, 300.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.intervals[0].status is IntervalStatus.EXCLUDED_ZERO_DURATION
        assert result.intervals[0].energy_wh is None
        assert result.intervals[0].duration == timedelta(0)
        assert result.intervals[1].status is IntervalStatus.OBSERVED
        assert result.summary.excluded_interval_count == 1

    def test_out_of_order_timestamp_raises(self) -> None:
        obs = [
            _obs(_TS + _H1, 200.0),
            _obs(_TS, 100.0),
        ]
        with pytest.raises(ValueError, match="out-of-order"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )

    def test_coverage_never_scales_energy(self) -> None:
        obs = [
            _obs(_TS, 1000.0),
            _obs(_TS + _M5, 1000.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.coverage_fraction < 1.0
        assert result.summary.observed_energy_wh == pytest.approx(1000.0 * (5.0 / 60.0))


# ---------------------------------------------------------------------------
# Excluded intervals
# ---------------------------------------------------------------------------


class TestExcludedIntervals:
    def test_missing_endpoint_produces_excluded_nonfinite(self) -> None:
        obs = [
            _obs(_TS, 100.0, status=NormalizationStatus.NORMALIZED),
            _obs(
                _TS + _M5,
                power_w=None,
                status=NormalizationStatus.MISSING_VALUE,
            ),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        assert result.intervals[0].status is IntervalStatus.EXCLUDED_NONFINITE
        assert result.intervals[0].energy_wh is None
        assert result.summary.excluded_duration == _M5

    def test_non_normalized_endpoint_produces_excluded_unconfirmed_sign(self) -> None:
        obs = [
            _obs(_TS, 100.0, status=NormalizationStatus.NORMALIZED),
            _obs(
                _TS + _M5,
                power_w=None,
                status=NormalizationStatus.PROFILE_NOT_CONFIRMED,
                profile_version="1.0.0",
            ),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        assert result.intervals[0].status is IntervalStatus.EXCLUDED_UNCONFIRMED_SIGN

    def test_both_nonfinite_endpoints_excluded(self) -> None:
        obs = [
            _obs(
                _TS,
                power_w=None,
                status=NormalizationStatus.NONFINITE_VALUE,
            ),
            _obs(
                _TS + _M5,
                power_w=None,
                status=NormalizationStatus.NONFINITE_VALUE,
            ),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        assert result.intervals[0].status is IntervalStatus.EXCLUDED_NONFINITE


# ---------------------------------------------------------------------------
# Series identity validation
# ---------------------------------------------------------------------------


class TestSeriesIdentityValidation:
    def test_source_field_mismatch_raises(self) -> None:
        obs = [
            _obs(_TS, 100.0, source=CanonicalPowerField.FLOW_BATTERY),
            _obs(_TS + _H1, 100.0, source=CanonicalPowerField.FLOW_BATTERY),
        ]
        with pytest.raises(ValueError, match=r"canonical_source.*does not match series"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )

    def test_source_system_mismatch_raises(self) -> None:
        obs = [
            _obs(_TS, 100.0, system=SourceSystem.INVERTER_TELEMETRY),
            _obs(_TS + _H1, 100.0, system=SourceSystem.INVERTER_TELEMETRY),
        ]
        with pytest.raises(ValueError, match=r"source_system.*does not match series"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )

    def test_direction_mismatch_raises(self) -> None:
        obs = [
            _obs(_TS, 100.0, direction=_EXPORT),
            _obs(_TS + _H1, 100.0, direction=_EXPORT),
        ]
        with pytest.raises(ValueError, match=r"direction.*does not match series"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )

    def test_no_default_series_identity(self) -> None:
        with pytest.raises(TypeError, match="series"):
            integrate_energy(
                observations=[_obs(_TS, 100.0)],
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )


# ---------------------------------------------------------------------------
# Profile-version transition validation
# ---------------------------------------------------------------------------


class TestProfileVersionTransition:
    def test_first_observation_non_normalized_second_v1(self) -> None:
        obs = [
            _obs(_TS, power_w=None, status=NormalizationStatus.MISSING_VALUE),
            _obs(_TS + _M5, 100.0, profile_version="1.0.0"),
            _obs(_TS + _M10, 200.0, profile_version="2.0.0"),
        ]
        with pytest.raises(ValueError, match="mixed profile_version"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _M10,
            )

    def test_first_observation_non_normalized_second_v2_third_v1(self) -> None:
        obs = [
            _obs(_TS, power_w=None, status=NormalizationStatus.MISSING_VALUE),
            _obs(_TS + _M5, 100.0, profile_version="2.0.0"),
            _obs(_TS + _M10, 200.0, profile_version="1.0.0"),
        ]
        with pytest.raises(ValueError, match="mixed profile_version"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _M10,
            )

    def test_reversed_order_still_raises_mixed_version(self) -> None:
        obs = [
            _obs(_TS, 200.0, profile_version="2.0.0"),
            _obs(_TS + _M5, 100.0, profile_version="1.0.0"),
        ]
        with pytest.raises(ValueError, match="mixed profile_version"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _M5,
            )

    def test_single_profile_version_accepted(self) -> None:
        obs = [
            _obs(_TS, 100.0, profile_version="1.0.0"),
            _obs(_TS + _M5, 200.0, profile_version="1.0.0"),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        assert result.summary.sign_profile_version == "1.0.0"


# ---------------------------------------------------------------------------
# Synthetic timestamp removal — no from_normalized factory
# ---------------------------------------------------------------------------


class TestNoSyntheticTimestampFactory:
    def test_no_from_normalized_in_public_api(self) -> None:
        from solgreen.energy import integration as integration_module

        assert not hasattr(integration_module, "from_normalized")
        assert not hasattr(integration_module, "_UNSET")
        assert not hasattr(integration_module, "_power_or_none")

    def test_no_datetime_now_dependency(self) -> None:
        with open("solgreen/energy/integration.py") as f:
            source = f.read()
        assert "datetime.now" not in source
        assert "_UNSET" not in source

    def test_no_local_timezone_sentinel(self) -> None:
        with open("solgreen/energy/integration.py") as f:
            source = f.read()
        assert "astimezone()" not in source


# ---------------------------------------------------------------------------
# Immutability and regression
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_input_order_not_modified(self) -> None:
        obs = [
            _obs(_TS, 100.0, lineage=("a",)),
            _obs(_TS + _H1, 200.0, lineage=("b",)),
        ]
        obs_copy = list(obs)
        integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert obs == obs_copy

    def test_result_is_frozen(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _H1, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        with pytest.raises(pydantic.ValidationError, match="frozen"):
            result.summary = result.summary  # type: ignore[misc]
        with pytest.raises(pydantic.ValidationError, match="frozen"):
            result.summary.observed_energy_wh = 999.0  # type: ignore[misc]

    def test_lineage_stable(self) -> None:
        obs = [
            _obs(_TS, 100.0, lineage=("step:1",)),
            _obs(_TS + _H1, 100.0, lineage=("step:2",)),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.intervals[0].lineage
        assert any("trapezoidal" in e for e in result.intervals[0].lineage)

    def test_warnings_deterministic(self) -> None:
        result1 = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        result2 = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result1.summary.warnings == result2.summary.warnings

    def test_energy_interval_frozen(self) -> None:
        iv = EnergyInterval(
            start=_TS,
            end=_TS + _H1,
            duration=_H1,
            source_field=_GRID,
            source_system=_SOLARMAN,
            direction=_IMPORT,
            start_power_w=100.0,
            end_power_w=100.0,
            integration_method=IntegrationMethod.TRAPEZOIDAL,
            energy_wh=100.0,
            status=IntervalStatus.OBSERVED,
            sign_profile_version="1.0.0",
        )
        with pytest.raises(pydantic.ValidationError, match="frozen"):
            iv.energy_wh = 999.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Additional integration scenarios
# ---------------------------------------------------------------------------


class TestAdditionalScenarios:
    def test_all_six_directions_valid(self) -> None:
        for direction in (
            PowerDirection.GRID_IMPORT,
            PowerDirection.GRID_EXPORT,
            PowerDirection.BATTERY_CHARGE,
            PowerDirection.BATTERY_DISCHARGE,
            PowerDirection.PV_GENERATION,
            PowerDirection.LOAD_CONSUMPTION,
        ):
            series = EnergySeriesIdentity(
                source_field=_GRID,
                source_system=_SOLARMAN,
                direction=direction,
            )
            obs = [
                _obs(_TS, 100.0, direction=direction),
                _obs(_TS + _H1, 100.0, direction=direction),
            ]
            result = integrate_energy(
                series=series,
                observations=obs,
                profile=_P,
                period_start=_TS,
                period_end=_TS + _H1,
            )
            assert result.intervals[0].status is IntervalStatus.OBSERVED

    def test_period_end_equals_period_start_rejected(self) -> None:
        with pytest.raises(ValueError, match="period_end must be > period_start"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=[_obs(_TS, 100.0)],
                profile=_P,
                period_start=_TS,
                period_end=_TS,
            )

    def test_naive_period_start_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            integrate_energy(
                series=_SERIES_GRID_IMPORT,
                observations=[_obs(_TS, 100.0)],
                profile=_P,
                period_start=datetime(2026, 7, 24, 12, 0, 0),
                period_end=_TS + _H1,
            )

    def test_mixed_timezones_handled(self) -> None:
        cat = timezone(timedelta(hours=-5))
        ts_cat = datetime(2026, 7, 24, 12, 0, 0, tzinfo=cat)
        obs = [
            _obs(ts_cat, 100.0),
            _obs(ts_cat + _H1, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=ts_cat,
            period_end=ts_cat + _H1,
        )
        assert result.intervals[0].status is IntervalStatus.OBSERVED
        assert result.summary.coverage_fraction == pytest.approx(1.0)

    def test_zero_power_not_treated_as_missing(self) -> None:
        obs = [
            _obs(_TS, 0.0),
            _obs(_TS + _H1, 0.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.intervals[0].status is IntervalStatus.OBSERVED
        assert result.summary.observed_interval_count == 1
        assert result.summary.excluded_interval_count == 0

    def test_no_negative_energy_produced(self) -> None:
        obs = [_obs(_TS + i * _M5, max(0.0, 500.0 - 100.0 * i)) for i in range(13)]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + 12 * _M5,
        )
        for ival in result.intervals:
            if ival.status is IntervalStatus.OBSERVED:
                assert ival.energy_wh >= 0.0
        assert result.summary.observed_energy_wh >= 0.0


# ---------------------------------------------------------------------------
# Floating-point precision
# ---------------------------------------------------------------------------


class TestFloatingPointPrecision:
    def test_energy_preserves_full_precision(self) -> None:
        obs = [
            _obs(_TS, 0.1),
            _obs(_TS + _H1, 0.2),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        expected = ((0.1 + 0.2) / 2.0) * 1.0
        assert result.intervals[0].energy_wh == expected

    def test_large_power_still_precise(self) -> None:
        obs = [
            _obs(_TS, 15000.0),
            _obs(_TS + _M5, 14999.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M5,
        )
        duration_h = 5.0 / 60.0
        expected = ((15000.0 + 14999.0) / 2.0) * duration_h
        assert result.intervals[0].energy_wh == pytest.approx(expected)

    def test_wh_kwh_zero_energy(self) -> None:
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=[],
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        assert result.summary.observed_energy_wh == 0.0
        assert result.summary.observed_energy_kwh == 0.0


# ---------------------------------------------------------------------------
# Profile validation at call time
# ---------------------------------------------------------------------------


class TestProfileGateAtCallTime:
    def test_interval_average_profile_rejected_during_validation(self) -> None:
        with pytest.raises(ValueError, match=r"Only SampleSemantics\.INSTANTANEOUS"):
            _profile(sample_semantics=SampleSemantics.INTERVAL_AVERAGE)

    def test_unknown_profile_rejected_during_validation(self) -> None:
        with pytest.raises(ValueError, match=r"Only SampleSemantics\.INSTANTANEOUS"):
            _profile(sample_semantics=SampleSemantics.UNKNOWN)


# ---------------------------------------------------------------------------
# Duration partition reconciliation
# ---------------------------------------------------------------------------


class TestDurationPartitionReconciliation:
    def test_complete_coverage_reconciles(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _H1, 100.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _H1,
        )
        s = result.summary
        assert s.observed_duration + s.missing_duration + s.excluded_duration == s.expected_duration

    def test_partial_coverage_reconciles(self) -> None:
        p = _profile(max_authorized=_M5)
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _M10, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=p,
            period_start=_TS,
            period_end=_TS + _M10,
        )
        s = result.summary
        assert s.observed_duration + s.missing_duration + s.excluded_duration == s.expected_duration

    def test_leading_gap_reconciles(self) -> None:
        obs = [
            _obs(_TS + _M5, 100.0),
            _obs(_TS + _M10, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M10,
        )
        s = result.summary
        assert s.observed_duration + s.missing_duration + s.excluded_duration == s.expected_duration

    def test_trailing_gap_reconciles(self) -> None:
        obs = [
            _obs(_TS, 100.0),
            _obs(_TS + _M5, 200.0),
        ]
        result = integrate_energy(
            series=_SERIES_GRID_IMPORT,
            observations=obs,
            profile=_P,
            period_start=_TS,
            period_end=_TS + _M10,
        )
        s = result.summary
        assert s.observed_duration + s.missing_duration + s.excluded_duration == s.expected_duration
