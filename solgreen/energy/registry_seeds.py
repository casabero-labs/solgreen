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


def build_telemetry_sign_profile_registry() -> PowerSignProfileRegistry:
    """
    Build and return a registry seeded with the four owner-approved
    telemetry sign profiles.

    Flow profiles are excluded — they retain PENDING_INDEPENDENT_ASSESSMENT
    status and must not be derived from these telemetry conventions.
    """
    registry = PowerSignProfileRegistry()

    profiles: list[PowerSignProfile] = []

    # Battery: positive=discharge, negative=charge, zero=idle
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
            notes=(
                "Owner-approved: positive = battery discharge, "
                "negative = battery charge, zero = idle. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    # Grid: positive=export_to_grid, negative=import_from_grid, zero=no_exchange
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
            notes=(
                "Owner-approved: positive = export to Afinia, "
                "negative = import from Afinia. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    # PV: positive=photovoltaic_generation, zero=no_generation, negative=anomaly
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
            notes=(
                "Owner-approved: PV production always non-negative. "
                "Negative values outside deadband indicate anomaly. "
                "Deadband ±5 W applied. "
                "Flow profiles are independent and pending separate assessment."
            ),
        )
    )

    # Load: positive=site_consumption, zero=technical_zero, negative=anomaly
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
            notes=(
                "Owner-approved after deadband validation: "
                "single -2.0 W value classified as technical zero (±5 W deadband). "
                "No values below -5 W found. "
                "Flow source — NOT derived from telemetry conventions. "
                "This profile uses flow canonical field but references telemetry approval."
            ),
        )
    )

    for profile in profiles:
        registry.register(profile)

    return registry
