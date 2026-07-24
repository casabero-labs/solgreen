"""
Pre-authorized sign profiles for SOLGREEN telemetry sources.

These profiles represent owner-approved sign conventions for the SolarMAN
telemetry (inverter telemetry) source. They are materialized after
explicit owner approval per signal.

Flow profiles are NOT included — they require independent assessment.

All profiles use:
    - authority_class = operational
    - measurement_point = "telemetry:inverter:<signal>"
    - unit = "W"
    - zero_deadband_w = 5.0 (SIGN_ZERO_DEADBAND_W)
"""

from __future__ import annotations

from datetime import UTC, datetime

from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    PowerDirection,
    PowerSignProfile,
    PowerSignProfileRegistry,
    ProfileStatus,
    SourceSystem,
)


def _build_legacy_telemetry_profiles(
    *,
    valid_to: datetime | None = None,
) -> tuple[PowerSignProfile, ...]:
    """Single source of truth for the four legacy telemetry/flow profiles.

    Each profile is constructed with `valid_to` set to the provided value,
    enabling the production builder to close the legacy interval at cutover
    without mutating frozen instances.

    Args:
        valid_to: Upper bound of the legacy validity interval.
                  Use None for an open-ended interval (legacy behavior).
                  Use a timezone-aware datetime to close the interval at cutover.
    """
    profiles: list[PowerSignProfile] = []

    profiles.append(
        PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:battery_power",
            unit="W",
            positive_means=PowerDirection.BATTERY_DISCHARGE,
            negative_means=PowerDirection.BATTERY_CHARGE,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=valid_to,
            notes=(
                "Owner-approved: positive = battery discharge, "
                "negative = battery charge, zero = idle. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    profiles.append(
        PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:grid_power",
            unit="W",
            positive_means=PowerDirection.GRID_EXPORT,
            negative_means=PowerDirection.GRID_IMPORT,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=valid_to,
            notes=(
                "Owner-approved: positive = export to Afinia, "
                "negative = import from Afinia. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    profiles.append(
        PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:pv_power",
            unit="W",
            positive_means=PowerDirection.PV_GENERATION,
            negative_means=PowerDirection.UNKNOWN,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=valid_to,
            notes=(
                "Owner-approved: PV production always non-negative. "
                "Negative values outside deadband indicate anomaly. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    profiles.append(
        PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="flow:plant:load_power",
            unit="W",
            positive_means=PowerDirection.LOAD_CONSUMPTION,
            negative_means=PowerDirection.UNKNOWN,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=valid_to,
            notes=(
                "Owner-approved: single -2.0 W value within ±5 W deadband "
                "classified as technical zero. No values below -5 W found. "
                "status=confirmed; validation_method=deadband; validation_result=passed. "
                "Uses flow canonical field (no telemetry load field exists in schema). "
                "Flow profiles are otherwise pending independent assessment."
            ),
        )
    )

    return tuple(profiles)


def build_telemetry_sign_profile_registry() -> PowerSignProfileRegistry:
    """
    Build and return a registry seeded with the four owner-approved
    telemetry sign profiles.

    Flow profiles are excluded — they retain PENDING_INDEPENDENT_ASSESSMENT
    status and must not be derived from these telemetry conventions.

    Returns a registry where all four profiles have an open-ended
    validity interval (valid_to=None).  Use
    `build_production_sign_profile_registry` for the D1.0 cutover.
    """
    registry = PowerSignProfileRegistry()
    for profile in _build_legacy_telemetry_profiles(valid_to=None):
        registry.register(profile)
    return registry


def build_production_sign_profile_registry(
    *,
    effective_from: datetime,
) -> PowerSignProfileRegistry:
    """Build the production sign profile registry after D1.0 cutover.

    Closes the four legacy telemetry/flow profiles at `effective_from`
    and opens the four D1.0 authoritative profiles with per-direction
    evidence status (ADR-009).

    The returned registry contains eight profiles:
      - Four legacy profiles with valid_to = effective_from (closed interval)
      - Four D1.0 profiles with valid_from = effective_from (open interval)

    `effective_from` is REQUIRED, must be timezone-aware (UTC offset set),
    and must be supplied explicitly by the operator or deployment
    configuration.  The function never invents a cutover timestamp.

    Idempotency: two independent calls with the same effective_from
    produce equivalent but distinct registry instances.  An error is
    raised only when registering the same profile twice within a single
    registry instance.

    Rollback: after D1.0 cutover, reverting to legacy behavior means
    calling `build_telemetry_sign_profile_registry()` instead, or
    reverting the integration commit.  No state is persisted.
    """
    from solgreen.energy.registry_d10_proposal import build_updated_profiles

    registry = PowerSignProfileRegistry()

    for profile in _build_legacy_telemetry_profiles(valid_to=effective_from):
        registry.register(profile)

    for profile in build_updated_profiles(effective_from=effective_from).values():
        registry.register(profile)

    return registry
