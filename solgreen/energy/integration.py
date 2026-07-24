from __future__ import annotations

import math
from datetime import datetime, timedelta
from enum import StrEnum

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from solgreen.energy.normalization import DirectionalPowerResult, NormalizationStatus
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerDirection,
    SourceSystem,
    is_timezone_aware,
)

_VALID_INTEGRATION_DIRECTIONS: frozenset[PowerDirection] = frozenset(
    {
        PowerDirection.GRID_IMPORT,
        PowerDirection.GRID_EXPORT,
        PowerDirection.BATTERY_CHARGE,
        PowerDirection.BATTERY_DISCHARGE,
        PowerDirection.PV_GENERATION,
        PowerDirection.LOAD_CONSUMPTION,
    }
)


class SampleSemantics(StrEnum):
    INSTANTANEOUS = "instantaneous"
    INTERVAL_AVERAGE = "interval_average"
    UNKNOWN = "unknown"


class IntegrationMethod(StrEnum):
    TRAPEZOIDAL = "trapezoidal"


class IntegrationProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_version: str = Field(min_length=1)
    sample_semantics: SampleSemantics
    integration_method: IntegrationMethod
    expected_interval: timedelta
    maximum_authorized_interval: timedelta

    @pydantic.model_validator(mode="after")
    def _validate_supported_semantics(self) -> IntegrationProfile:
        if self.sample_semantics is not SampleSemantics.INSTANTANEOUS:
            raise ValueError(
                f"Only SampleSemantics.INSTANTANEOUS is supported; "
                f"got {self.sample_semantics.value}."
            )
        if self.integration_method is not IntegrationMethod.TRAPEZOIDAL:
            raise ValueError(
                f"Only IntegrationMethod.TRAPEZOIDAL is supported; "
                f"got {self.integration_method.value}."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_positive_durations(self) -> IntegrationProfile:
        if self.expected_interval <= timedelta(0):
            raise ValueError(
                f"expected_interval must be strictly positive; got {self.expected_interval}."
            )
        if self.maximum_authorized_interval <= timedelta(0):
            raise ValueError(
                f"maximum_authorized_interval must be strictly positive; "
                f"got {self.maximum_authorized_interval}."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_max_gte_expected(self) -> IntegrationProfile:
        if self.maximum_authorized_interval < self.expected_interval:
            raise ValueError(
                f"maximum_authorized_interval ({self.maximum_authorized_interval}) "
                f"must be >= expected_interval ({self.expected_interval})."
            )
        return self


class IntervalStatus(StrEnum):
    OBSERVED = "observed"
    MISSING = "missing"
    EXCLUDED_NONFINITE = "excluded_nonfinite"
    EXCLUDED_ZERO_DURATION = "excluded_zero_duration"
    EXCLUDED_UNCONFIRMED_SIGN = "excluded_unconfirmed_sign"
    NOT_APPLICABLE = "not_applicable"


def _power_or_none(result: DirectionalPowerResult, direction: PowerDirection) -> float | None:
    if direction is PowerDirection.GRID_IMPORT:
        return result.grid_import_w
    if direction is PowerDirection.GRID_EXPORT:
        return result.grid_export_w
    if direction is PowerDirection.BATTERY_CHARGE:
        return result.battery_charge_w
    if direction is PowerDirection.BATTERY_DISCHARGE:
        return result.battery_discharge_w
    if direction is PowerDirection.PV_GENERATION:
        return result.pv_generation_w
    if direction is PowerDirection.LOAD_CONSUMPTION:
        return result.load_consumption_w
    return None


class DirectionalPowerObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime
    canonical_source: CanonicalPowerField
    source_system: SourceSystem
    direction: PowerDirection
    power_w: float | None = None
    status: NormalizationStatus
    profile_version: str | None = None
    lineage: tuple[str, ...] = Field(default=())

    @classmethod
    def from_normalized(
        cls,
        result: DirectionalPowerResult,
        direction: PowerDirection,
        *,
        lineage_prefix: tuple[str, ...] = (),
    ) -> DirectionalPowerObservation:
        power = _power_or_none(result, direction)
        lineage = (*lineage_prefix, f"normalize:{result.status.value}")
        return cls(
            timestamp=result.timestamp if hasattr(result, "timestamp") else _UNSET,
            canonical_source=result.canonical_field,
            source_system=result.source_system,
            direction=direction,
            power_w=power,
            status=result.status,
            profile_version=result.profile_version,
            lineage=lineage,
        )

    @pydantic.model_validator(mode="after")
    def _validate_timestamp_aware(self) -> DirectionalPowerObservation:
        if not is_timezone_aware(self.timestamp):
            raise ValueError("timestamp must be timezone-aware.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_valid_direction(self) -> DirectionalPowerObservation:
        if self.direction not in _VALID_INTEGRATION_DIRECTIONS:
            raise ValueError(
                f"direction must be one of "
                f"{sorted(d.value for d in _VALID_INTEGRATION_DIRECTIONS)}; "
                f"got {self.direction.value}."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_normalized_observation(self) -> DirectionalPowerObservation:
        if self.status is NormalizationStatus.NORMALIZED:
            if self.power_w is None:
                raise ValueError("normalized observation must have power_w set.")
            if not math.isfinite(self.power_w):
                raise ValueError("normalized observation power_w must be finite.")
            if self.power_w < 0:
                raise ValueError("normalized observation power_w must be non-negative.")
            if not self.profile_version:
                raise ValueError("normalized observation must have non-empty profile_version.")
        else:
            if self.power_w is not None:
                raise ValueError(
                    f"non-normalized observation (status={self.status.value}) "
                    f"must have power_w=None."
                )
        return self


_UNSET: datetime = datetime(2000, 1, 1, tzinfo=datetime.now().astimezone().tzinfo)


class EnergyInterval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: datetime
    end: datetime
    duration: timedelta
    source_field: CanonicalPowerField
    source_system: SourceSystem
    direction: PowerDirection
    start_power_w: float | None = None
    end_power_w: float | None = None
    integration_method: IntegrationMethod
    energy_wh: float | None = None
    status: IntervalStatus
    sign_profile_version: str | None = None
    lineage: tuple[str, ...] = Field(default=())
    quality_flags: tuple[str, ...] = Field(default=())

    @pydantic.model_validator(mode="after")
    def _validate_timestamps_aware(self) -> EnergyInterval:
        if not is_timezone_aware(self.start):
            raise ValueError("start must be timezone-aware.")
        if not is_timezone_aware(self.end):
            raise ValueError("end must be timezone-aware.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_end_after_start(self) -> EnergyInterval:
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must not be before start ({self.start}).")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_duration_consistency(self) -> EnergyInterval:
        expected = self.end - self.start
        if expected != self.duration:
            raise ValueError(f"duration ({self.duration}) must equal end - start ({expected}).")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_observed_invariants(self) -> EnergyInterval:
        if self.status is IntervalStatus.OBSERVED:
            if self.duration <= timedelta(0):
                raise ValueError("observed interval must have positive duration.")
            if self.start_power_w is None or self.end_power_w is None:
                raise ValueError("observed interval must have both start_power_w and end_power_w.")
            if not math.isfinite(self.start_power_w) or self.start_power_w < 0:
                raise ValueError(
                    f"observed interval start_power_w must be finite and >= 0; "
                    f"got {self.start_power_w}."
                )
            if not math.isfinite(self.end_power_w) or self.end_power_w < 0:
                raise ValueError(
                    f"observed interval end_power_w must be finite and >= 0; "
                    f"got {self.end_power_w}."
                )
            if self.energy_wh is None:
                raise ValueError("observed interval must have energy_wh set.")
            if not math.isfinite(self.energy_wh) or self.energy_wh < 0:
                raise ValueError(
                    f"observed interval energy_wh must be finite and >= 0; got {self.energy_wh}."
                )
            if self.sign_profile_version is None:
                raise ValueError("observed interval must have sign_profile_version.")
        else:
            if self.energy_wh is not None:
                raise ValueError(
                    f"non-observed interval (status={self.status.value}) must have energy_wh=None."
                )
        return self


class EnergySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    period_start: datetime
    period_end: datetime
    source_field: CanonicalPowerField
    source_system: SourceSystem
    direction: PowerDirection
    observed_energy_wh: float = 0.0
    observed_energy_kwh: float = 0.0
    expected_duration: timedelta
    observed_duration: timedelta = timedelta(0)
    missing_duration: timedelta = timedelta(0)
    excluded_duration: timedelta = timedelta(0)
    coverage_fraction: float = 0.0
    interval_count: int = 0
    observed_interval_count: int = 0
    excluded_interval_count: int = 0
    sign_profile_version: str | None = None
    warnings: tuple[str, ...] = Field(default=())

    @pydantic.model_validator(mode="after")
    def _validate_kwh_conversion(self) -> EnergySummary:
        expected_kwh = self.observed_energy_wh / 1000.0
        if not math.isclose(self.observed_energy_kwh, expected_kwh, rel_tol=1e-12):
            raise ValueError(
                f"observed_energy_kwh ({self.observed_energy_kwh}) "
                f"must equal observed_energy_wh / 1000 ({expected_kwh})."
            )
        return self

    @pydantic.model_validator(mode="after")
    def _validate_coverage_invariant(self) -> EnergySummary:
        if self.expected_duration > timedelta(0):
            expected_cov = self.observed_duration / self.expected_duration
        else:
            expected_cov = 0.0
        if not math.isclose(self.coverage_fraction, expected_cov, rel_tol=1e-12):
            raise ValueError(
                f"coverage_fraction ({self.coverage_fraction}) "
                f"must equal observed_duration / expected_duration ({expected_cov})."
            )
        if self.coverage_fraction < 0.0 or self.coverage_fraction > 1.0:
            raise ValueError(f"coverage_fraction must be in [0, 1]; got {self.coverage_fraction}.")
        return self

    @pydantic.model_validator(mode="after")
    def _validate_energy_non_negative(self) -> EnergySummary:
        if self.observed_energy_wh < 0:
            raise ValueError("observed_energy_wh must be >= 0.")
        if self.observed_energy_kwh < 0:
            raise ValueError("observed_energy_kwh must be >= 0.")
        return self


class IntegrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intervals: tuple[EnergyInterval, ...]
    summary: EnergySummary


def _check_homogeneous_series(
    observations: list[DirectionalPowerObservation],
) -> None:
    if not observations:
        return
    first = observations[0]
    for idx, obs in enumerate(observations):
        if obs.canonical_source != first.canonical_source:
            raise ValueError(
                f"mixed canonical_source in batch: "
                f"observation 0 has {first.canonical_source.value}, "
                f"observation {idx} has {obs.canonical_source.value}."
            )
        if obs.source_system != first.source_system:
            raise ValueError(
                f"mixed source_system in batch: "
                f"observation 0 has {first.source_system.value}, "
                f"observation {idx} has {obs.source_system.value}."
            )
        if obs.direction != first.direction:
            raise ValueError(
                f"mixed direction in batch: "
                f"observation 0 has {first.direction.value}, "
                f"observation {idx} has {obs.direction.value}."
            )
        if (
            obs.status is NormalizationStatus.NORMALIZED
            and obs.profile_version is not None
            and first.profile_version is not None
            and obs.profile_version != first.profile_version
        ):
            raise ValueError(
                f"mixed profile_version in batch: "
                f"observation 0 has '{first.profile_version}', "
                f"observation {idx} has '{obs.profile_version}'."
            )


def _check_monotonic(
    observations: list[DirectionalPowerObservation],
) -> None:
    for idx in range(1, len(observations)):
        prev_ts = observations[idx - 1].timestamp
        curr_ts = observations[idx].timestamp
        if curr_ts < prev_ts:
            raise ValueError(
                f"out-of-order timestamp at position {idx}: {curr_ts} is before {prev_ts}."
            )


def integrate_energy(
    *,
    observations: list[DirectionalPowerObservation],
    profile: IntegrationProfile,
    period_start: datetime,
    period_end: datetime,
) -> IntegrationResult:
    if not is_timezone_aware(period_start):
        raise ValueError("period_start must be timezone-aware.")
    if not is_timezone_aware(period_end):
        raise ValueError("period_end must be timezone-aware.")
    if period_end <= period_start:
        raise ValueError("period_end must be > period_start.")

    _check_homogeneous_series(observations)
    _check_monotonic(observations)

    # Filter observations to those within [period_start, period_end].
    # Observations strictly outside the period do not participate in
    # interval creation, but their timestamps are still validated for
    # monotonicity in the raw input.
    in_window = [o for o in observations if period_start <= o.timestamp <= period_end]

    n = len(in_window)
    intervals: list[EnergyInterval] = []
    observed_energy_wh = 0.0
    observed_duration = timedelta(0)
    missing_duration = timedelta(0)
    excluded_duration = timedelta(0)
    observed_interval_count = 0
    excluded_interval_count = 0
    warnings: list[str] = []

    series_source = in_window[0].canonical_source if n > 0 else CanonicalPowerField.FLOW_GRID
    series_system = in_window[0].source_system if n > 0 else SourceSystem.SOLARMAN_PLANT_FLOW
    series_direction = in_window[0].direction if n > 0 else PowerDirection.GRID_IMPORT
    sign_profile_version: str | None = None

    for obs in in_window:
        if obs.status is NormalizationStatus.NORMALIZED and obs.profile_version:
            sign_profile_version = obs.profile_version
            break

    if n == 0:
        return IntegrationResult(
            intervals=(),
            summary=EnergySummary(
                period_start=period_start,
                period_end=period_end,
                source_field=series_source,
                source_system=series_system,
                direction=series_direction,
                observed_energy_wh=0.0,
                observed_energy_kwh=0.0,
                expected_duration=period_end - period_start,
                observed_duration=timedelta(0),
                missing_duration=period_end - period_start,
                excluded_duration=timedelta(0),
                coverage_fraction=0.0,
                interval_count=0,
                observed_interval_count=0,
                excluded_interval_count=0,
                sign_profile_version=None,
                warnings=("empty_series",),
            ),
        )

    # Account for leading boundary: period_start to first observation
    first_ts = in_window[0].timestamp
    if first_ts > period_start:
        missing_duration += first_ts - period_start

    # Process consecutive pairs within the period window
    max_auth = profile.maximum_authorized_interval

    for idx in range(n - 1):
        obs_a = in_window[idx]
        obs_b = in_window[idx + 1]
        start_ts = obs_a.timestamp
        end_ts = obs_b.timestamp

        duration = end_ts - start_ts

        if duration == timedelta(0):
            intervals.append(
                EnergyInterval(
                    start=start_ts,
                    end=end_ts,
                    duration=duration,
                    source_field=series_source,
                    source_system=series_system,
                    direction=series_direction,
                    start_power_w=None,
                    end_power_w=None,
                    integration_method=profile.integration_method,
                    energy_wh=None,
                    status=IntervalStatus.EXCLUDED_ZERO_DURATION,
                    sign_profile_version=None,
                    lineage=(f"integrate:zero_duration:{idx}",),
                    quality_flags=("zero_duration_interval",),
                )
            )
            excluded_interval_count += 1
            continue

        if duration > max_auth:
            intervals.append(
                EnergyInterval(
                    start=start_ts,
                    end=end_ts,
                    duration=duration,
                    source_field=series_source,
                    source_system=series_system,
                    direction=series_direction,
                    start_power_w=None,
                    end_power_w=None,
                    integration_method=profile.integration_method,
                    energy_wh=None,
                    status=IntervalStatus.MISSING,
                    sign_profile_version=None,
                    lineage=(f"integrate:missing:gap:{idx}",),
                    quality_flags=("interval_exceeds_maximum_authorized",),
                )
            )
            excluded_interval_count += 1
            missing_duration += duration
            continue

        status_a = obs_a.status
        status_b = obs_b.status
        power_a = obs_a.power_w
        power_b = obs_b.power_w

        def _is_usable(st: NormalizationStatus, pw: float | None) -> bool:
            return st is NormalizationStatus.NORMALIZED and pw is not None

        a_usable = _is_usable(status_a, power_a)
        b_usable = _is_usable(status_b, power_b)

        if not a_usable or not b_usable:
            if a_usable and not b_usable:
                problem = _unusable_reason(status_b, power_b)
            elif not a_usable and b_usable:
                problem = _unusable_reason(status_a, power_a)
            else:
                problem = _unusable_reason(status_a, power_a)

            if problem == "unconfirmed_sign":
                exc_status = IntervalStatus.EXCLUDED_UNCONFIRMED_SIGN
                quality_flag = "unconfirmed_sign_profile"
            elif problem == "nonfinite_value":
                exc_status = IntervalStatus.EXCLUDED_NONFINITE
                quality_flag = "nonfinite_power_value"
            elif problem == "missing_value":
                exc_status = IntervalStatus.EXCLUDED_NONFINITE
                quality_flag = "missing_power_value"
            elif problem == "profile_not_found":
                exc_status = IntervalStatus.EXCLUDED_UNCONFIRMED_SIGN
                quality_flag = "profile_not_found"
            else:
                exc_status = IntervalStatus.EXCLUDED_NONFINITE
                quality_flag = "unusable_observation"

            intervals.append(
                EnergyInterval(
                    start=start_ts,
                    end=end_ts,
                    duration=duration,
                    source_field=series_source,
                    source_system=series_system,
                    direction=series_direction,
                    start_power_w=power_a,
                    end_power_w=power_b,
                    integration_method=profile.integration_method,
                    energy_wh=None,
                    status=exc_status,
                    sign_profile_version=None,
                    lineage=(f"integrate:{exc_status.value}:{idx}",),
                    quality_flags=(quality_flag,),
                )
            )
            excluded_interval_count += 1
            excluded_duration += duration
            continue

        assert power_a is not None
        assert power_b is not None
        assert obs_a.profile_version is not None
        assert obs_b.profile_version is not None

        duration_hours = duration.total_seconds() / 3600.0
        energy_wh = ((power_a + power_b) / 2.0) * duration_hours

        intervals.append(
            EnergyInterval(
                start=start_ts,
                end=end_ts,
                duration=duration,
                source_field=series_source,
                source_system=series_system,
                direction=series_direction,
                start_power_w=power_a,
                end_power_w=power_b,
                integration_method=profile.integration_method,
                energy_wh=energy_wh,
                status=IntervalStatus.OBSERVED,
                sign_profile_version=obs_a.profile_version,
                lineage=(f"integrate:trapezoidal:{idx}",),
                quality_flags=(),
            )
        )
        observed_energy_wh += energy_wh
        observed_duration += duration
        observed_interval_count += 1

    # Account for trailing boundary: last observation to period_end
    last_ts = in_window[-1].timestamp
    if last_ts < period_end:
        missing_duration += period_end - last_ts

    total_intervals = len(intervals)
    expected_duration = period_end - period_start

    if total_intervals == 0 and n == 1:
        warnings.append("single_observation_no_intervals")
    if missing_duration > timedelta(0):
        warnings.append("partial_coverage")
    if excluded_interval_count > 0:
        warnings.append("excluded_intervals_present")
    if observed_interval_count == 0 and n > 0:
        warnings.append("no_observed_intervals")

    coverage = observed_duration / expected_duration if expected_duration > timedelta(0) else 0.0

    return IntegrationResult(
        intervals=tuple(intervals),
        summary=EnergySummary(
            period_start=period_start,
            period_end=period_end,
            source_field=series_source,
            source_system=series_system,
            direction=series_direction,
            observed_energy_wh=observed_energy_wh,
            observed_energy_kwh=observed_energy_wh / 1000.0,
            expected_duration=expected_duration,
            observed_duration=observed_duration,
            missing_duration=missing_duration,
            excluded_duration=excluded_duration,
            coverage_fraction=coverage,
            interval_count=total_intervals,
            observed_interval_count=observed_interval_count,
            excluded_interval_count=excluded_interval_count,
            sign_profile_version=sign_profile_version,
            warnings=tuple(warnings),
        ),
    )


def _unusable_reason(status: NormalizationStatus, power: float | None) -> str:
    if status is NormalizationStatus.PROFILE_NOT_CONFIRMED:
        return "unconfirmed_sign"
    if status is NormalizationStatus.PROFILE_NOT_FOUND:
        return "profile_not_found"
    if status is NormalizationStatus.MISSING_VALUE:
        return "missing_value"
    if status is NormalizationStatus.NONFINITE_VALUE:
        return "nonfinite_value"
    if status is NormalizationStatus.INVALID_UNSIGNED_NEGATIVE:
        return "nonfinite_value"
    if status is NormalizationStatus.FIELD_MISMATCH:
        return "unconfirmed_sign"
    if power is None:
        return "missing_value"
    return "unconfirmed_sign"
