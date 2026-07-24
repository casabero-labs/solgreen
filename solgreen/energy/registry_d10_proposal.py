"""
D1.0 SOLARMAN Sign Profile Registry — U2.1b.1 Proposal (Redesign).

PRINCIPLES
==========

1. PowerSignProfile represents exclusively power in watts.
   The schema `unit: Literal["W"]` is NOT extended.
   No "A" (amperes), per-phase, or per-string variants are promoted
   as PowerSignProfile.

2. One authoritative signal per (canonical_field, source_system) tuple.
   Promotion replaces old profiles using semi-open intervals:
       old.valid_to  = effective_from
       new.valid_from = effective_from
   New and old profiles never coexist at any timestamp.

3. Per-direction evidence status (ADR-009).
   `profile.status` is administrative only. Authorization for normalizing
   a direction is held by `positive_evidence_status` and
   `negative_evidence_status`. This lets a single profile express
   "import confirmed, export deferred" without losing either direction.
   The grid profile is the canonical example: profile.status=CONFIRMED
   with positive_evidence_status=NOT_ASSESSED and
   negative_evidence_status=CONFIRMED.

ARCHITECTURE
============

- UPDATED_PROFILES: 4 PowerSignProfile-compatible entries (W only).
    battery_b_p1       — BATTERY_DISCHARGE / BATTERY_CHARGE   — CONFIRMED
    grid_t_a_p_o_g     — UNKNOWN         / GRID_IMPORT       — CONFIRMED
                         (per-direction evidence: NOT_ASSESSED / CONFIRMED)
    pv_c_p_pvt         — PV_GENERATION   / UNKNOWN           — CONFIRMED
    load_e_puse_t1     — LOAD_CONSUMPTION/ UNKNOWN           — CONFIRMED

- SUPPORTING_SIGNALS: 7 raw signals documented but NOT registered.
    B_C1 (A, current), DP1/DP2 (W, per-string PV), C_P_L1/C_P_L2 (W,
    per-phase load), UAP1/UAP2 (W, per-phase grid). All carry
    production_registry_allowed=False.

- DEFERRED_SIGNALS: 11 directions without owner-anchored evidence.
    Grid export, UAP1±, UAP2±, PV negative, load negative.

TEMPORAL PROVENANCE
===================

- Existing registry (registry_seeds.py):
    valid_from = 2026-07-01
    evidence_refs = "owner_decision_2026_07_21"
- Real evidence was collected and is documented in private evidence files.
- The 2026-07-01 valid_from predates the owner decision. The existing
  profiles are LEGACY_PRE_EVIDENCE and are NOT silently extended.
- This file does NOT define a default `effective_from`. The cutover
  timestamp is supplied explicitly to `build_updated_profiles(effective_from=...)`.
  See ADR-009 §"Temporal semantics".
- Promotion geometry uses semi-open intervals; see PRINCIPLES #2.

CONSUMER AUDIT (PROFILE_NOT_CONFIRMED)
======================================

As of this proposal, `normalize_power_value()` has NO production consumer
in solgreen/. Search results across `solgreen/**/*.py` show:
- normalize_power_value is referenced ONLY in tests.
- PROFILE_NOT_CONFIRMED is referenced ONLY in tests.
- DirectionalPowerResult is referenced ONLY in tests.

Implications for the new grid profile (per-direction evidence):
- No code converts PROFILE_NOT_CONFIRMED to zero.
- No code adds PROFILE_NOT_CONFIRMED to import.
- No code treats PROFILE_NOT_CONFIRMED as confirmed export.
- No code raises unhandled exception (status is a closed enum value,
  DirectionalPowerResult is built without errors for this status).

Behavioral guarantee (per ADR-009):
- raw grid < 0   (outside deadband)  -> NORMALIZED as GRID_IMPORT.
- raw grid > 0   (outside deadband)  -> PROFILE_NOT_CONFIRMED.
- |raw grid|    <= zero_deadband_w   -> NORMALIZED with both
                                         directional magnitudes = 0.0
                                         (NO_FLOW).

OPERATIONAL STATUS
==================

- This file is NOT loaded by `build_telemetry_sign_profile_registry()`.
- This file is NOT exported from `solgreen.energy.__init__`.
- Promoting the new profiles requires, in order:
    1. Owner-supplied `effective_from` (timezone-aware datetime approved
       by the operator) passed to `build_updated_profiles()`.
    2. Edit to `registry_seeds.py` adding `valid_to=effective_from` to
       each existing profile that the new profile replaces.
    3. Edit to `registry_seeds.py` registering new profiles from the
       dict returned by `build_updated_profiles()` (in any order; register
       order does not affect resolution).
    4. CI must pass (ruff, mypy, pytest).
    5. Rollout follows ADR-008 principles.

ROLLBACK
========

If promotion causes an operational regression:
    1. Remove the new profiles from `registry_seeds.py`.
    2. Remove `valid_to` from the closed profiles (set back to None).
    3. The registry reverts to the LEGACY_PRE_REAL_EVIDENCE behavior.
"""

from __future__ import annotations

from datetime import datetime

from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    DirectionEvidenceStatus,
    PowerDirection,
    PowerSignProfile,
    ProfileStatus,
    SourceSystem,
    is_timezone_aware,
)

PROFILE_VERSION = "u2_1b.1-d1.0"


# ── Provenance constants ───────────────────────────────────────────────────────
#
# Owner approval of the cutover timestamp is REQUIRED before promotion.
# No default effective_from is provided at module level; the timestamp must
# be supplied explicitly via `build_updated_profiles(effective_from=...)`.
# See the rationale in ADR-009 §"Temporal semantics".
#
# Evidence reference for the new profiles. References the private
# evidence collected during the owner-approved evidence window.
EVIDENCE_REF = "owner_decision_post_2026_07_23_u2_1b.1"

# Legacy evidence reference used by the existing registry_seeds.py profiles.
# Kept here ONLY for traceability comparison; not used by new profiles.
LEGACY_EVIDENCE_REF = "owner_decision_2026_07_21"


# ── Authoritative sign profiles (4 templates) ────────────────────────────────
#
# Each entry below is a TEMPLATE: it is missing `valid_from` because that
# timestamp must be supplied explicitly by the operator via
# `build_updated_profiles(effective_from=...)`. No default effective_from is
# provided at module level — see ADR-009 §"Temporal semantics" for the
# rationale (the operator must choose a real cutover timestamp; the
# proposal never invents one).
#
# Promotion path: build_updated_profiles() -> registry.register().


def build_updated_profiles(*, effective_from: datetime) -> dict[str, PowerSignProfile]:
    """Build the four authoritative PowerSignProfile instances for promotion.

    `effective_from` is REQUIRED. It must be a timezone-aware datetime
    (UTC offset set). Naive datetimes and `None` are rejected; the
    function never invents a cutover timestamp.

    Returns a dict mapping profile key -> PowerSignProfile with
    `valid_from=effective_from`. The four keys are:

        - "battery_b_p1"
        - "grid_t_a_p_o_g"
        - "pv_c_p_pvt"
        - "load_e_puse_t1"
    """
    if effective_from is None:
        raise ValueError(
            "effective_from is required and must not be None. "
            "No default cutover timestamp is provided at module level; "
            "the operator must supply a real, owner-approved datetime."
        )
    if not is_timezone_aware(effective_from):
        raise ValueError(
            f"effective_from must be timezone-aware "
            f"(tzinfo and utcoffset both set), got naive: {effective_from!r}"
        )
    result: dict[str, PowerSignProfile] = {}
    for key, template in UPDATED_PROFILES.items():
        data = dict(template)
        data["valid_from"] = effective_from
        result[key] = PowerSignProfile(**data)
    return result


UPDATED_PROFILES: dict[str, dict[str, object]] = {
    "battery_b_p1": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_BATTERY,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:b_p1",
        "unit": "W",
        "positive_means": PowerDirection.BATTERY_DISCHARGE,
        "negative_means": PowerDirection.BATTERY_CHARGE,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "positive_evidence_status": DirectionEvidenceStatus.CONFIRMED,
        "negative_evidence_status": DirectionEvidenceStatus.CONFIRMED,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "notes": (
            "B_P1: bidirectional battery power. "
            "positive = battery discharging (B_P1>0 + B_ST1='Discharging'). "
            "negative = battery charging (B_P1<0 + B_ST1='Charging'). "
            "Both directions owner-anchored. "
            "Replaces legacy_pre_real_evidence profile "
            "(valid_from=2026-07-01, evidence_refs=owner_decision_2026_07_21)."
        ),
    },
    "grid_t_a_p_o_g": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_GRID,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:t_a_p_o_g",
        "unit": "W",
        "positive_means": PowerDirection.UNKNOWN,
        "negative_means": PowerDirection.GRID_IMPORT,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        # ADR-009: per-direction evidence status is the actual gate for
        # normalization. profile.status=CONFIRMED is administrative only.
        # Positive direction (export) carries NOT_ASSESSED; the corresponding
        # raw values return PROFILE_NOT_CONFIRMED until an export event is
        # anchored by ST_PG1='Selling energy'.
        # Negative direction (import) is owner-anchored by
        # ST_PG1='Purchasing energy' (n=4, ap=4) and CONFIRMED per direction.
        "positive_evidence_status": DirectionEvidenceStatus.NOT_ASSESSED,
        "negative_evidence_status": DirectionEvidenceStatus.CONFIRMED,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "notes": (
            "T_A_P_O_G: per-direction evidence (ADR-009). "
            "negative_evidence_status=CONFIRMED: import anchored by "
            "ST_PG1='Purchasing energy' (n=4, ap=4). Negative raw values "
            "normalize as GRID_IMPORT. "
            "positive_evidence_status=NOT_ASSESSED: export not anchored. "
            "Positive raw values return PROFILE_NOT_CONFIRMED until a "
            "natural authorized export event with ST_PG1='Selling energy' "
            "is collected. profile.status=CONFIRMED is administrative only; "
            "the per-direction evidence status is the actual gate."
        ),
    },
    "pv_c_p_pvt": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_PV,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:c_p_pvt",
        "unit": "W",
        "positive_means": PowerDirection.PV_GENERATION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "positive_evidence_status": DirectionEvidenceStatus.CONFIRMED,
        "negative_evidence_status": DirectionEvidenceStatus.NOT_ASSESSED,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "notes": (
            "C_P_PVT: PV total charging power. "
            "positive = PV generation feeding battery/inverter (CONFIRMED). "
            "zero = no PV generation. "
            "negative = NOT_ASSESSED (zero in practice, anomaly if observed). "
            "Per-direction evidence: positive CONFIRMED, negative NOT_ASSESSED."
        ),
    },
    "load_e_puse_t1": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.FLOW_CONSUMO,
        "source_system": SourceSystem.SOLARMAN_PLANT_FLOW,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "flow:plant:e_puse_t1",
        "unit": "W",
        "positive_means": PowerDirection.LOAD_CONSUMPTION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "positive_evidence_status": DirectionEvidenceStatus.CONFIRMED,
        "negative_evidence_status": DirectionEvidenceStatus.NOT_ASSESSED,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "notes": (
            "E_Puse_t1: total household consumption power. "
            "positive = load consumption (CONFIRMED). "
            "Identity: C_P_L1 + C_P_L2 == E_Puse_t1 within 0-0.4% (4 samples). "
            "negative = NOT_ASSESSED. "
            "Per-direction evidence: positive CONFIRMED, negative NOT_ASSESSED. "
            "Replaces legacy_pre_real_evidence profile "
            "(valid_from=2026-07-01, evidence_refs=owner_decision_2026_07_21)."
        ),
    },
}


# ── Supporting signals (7 entries) — NOT registered ────────────────────────────
#
# Documented to acknowledge existence and reason for non-promotion.
# NONE of these entries are ever loaded into a PowerSignProfileRegistry.
#
# Reason categories:
#   - B_C1 (unit=A): schema requires W. Current is not power.
#   - DP1/DP2: redundant with pv_c_p_pvt (PV string sums into C_P_PVT).
#   - C_P_L1/C_P_L2: redundant with load_e_puse_t1 (phase sums into E_Puse_t1).
#   - UAP1/UAP2: per-phase grid signals not yet supported by schema;
#     require CanonicalPowerField enum extension (TELEMETRY_GRID_L1/L2).


SUPPORTING_SIGNALS: dict[str, dict[str, object]] = {
    "b_c1": {
        "raw_signal": "B_C1",
        "unit": "A",
        "supports_profile": "battery_b_p1",
        "observed_positive_meaning": "battery discharge current",
        "observed_negative_meaning": "battery charge current",
        "production_registry_allowed": False,
        "blocking_reason": (
            "unit=A is outside PowerSignProfile schema (Literal['W']). "
            "Current (amperes) is a different physical quantity than power. "
            "Requires separate derivation layer (A x V -> W)."
        ),
    },
    "dp1": {
        "raw_signal": "DP1",
        "unit": "W",
        "supports_profile": "pv_c_p_pvt",
        "meaning": "PV string 1 DC power",
        "production_registry_allowed": False,
        "blocking_reason": (
            "Sub-component of pv_c_p_pvt. Single authoritative profile per "
            "(canonical_field, source_system) tuple. Aggregated into C_P_PVT."
        ),
    },
    "dp2": {
        "raw_signal": "DP2",
        "unit": "W",
        "supports_profile": "pv_c_p_pvt",
        "meaning": "PV string 2 DC power",
        "production_registry_allowed": False,
        "blocking_reason": ("Sub-component of pv_c_p_pvt. Aggregated into C_P_PVT."),
    },
    "c_p_l1": {
        "raw_signal": "C_P_L1",
        "unit": "W",
        "supports_profile": "load_e_puse_t1",
        "meaning": "L1 phase load consumption",
        "production_registry_allowed": False,
        "blocking_reason": ("Sub-component of load_e_puse_t1. C_P_L1 + C_P_L2 == E_Puse_t1."),
    },
    "c_p_l2": {
        "raw_signal": "C_P_L2",
        "unit": "W",
        "supports_profile": "load_e_puse_t1",
        "meaning": "L2 phase load consumption",
        "production_registry_allowed": False,
        "blocking_reason": ("Sub-component of load_e_puse_t1. C_P_L1 + C_P_L2 == E_Puse_t1."),
    },
    "uap1": {
        "raw_signal": "UAP1",
        "unit": "W",
        "supports_profile": "grid_t_a_p_o_g",
        "negative_meaning_candidate": "L1 grid import",
        "production_registry_allowed": False,
        "blocking_reason": (
            "Requires CanonicalPowerField.TELEMETRY_GRID_L1 enum extension. "
            "Per-phase fields not in schema. UAP1 negative confirmed in "
            "private evidence (n=4, ap=4) but deferred as family until "
            "UAP2 ambiguity is resolved."
        ),
    },
    "uap2": {
        "raw_signal": "UAP2",
        "unit": "W",
        "supports_profile": "grid_t_a_p_o_g",
        "status": "ambiguous",
        "production_registry_allowed": False,
        "blocking_reason": (
            "Requires CanonicalPowerField.TELEMETRY_GRID_L2 enum extension. "
            "Per-phase fields not in schema. UAP2 positive (n=2) observed at "
            "night during GRID_IMPORTING regime with no selling anchor; "
            "UAP2 negative (n=1) is a strong candidate but single observation "
            "is insufficient. Status: ambiguous."
        ),
    },
}


# ── Deferred directions (11 entries) — NOT registered ─────────────────────────
#
# Each direction without owner-anchored evidence is documented here.
# NONE of these entries are ever loaded into a PowerSignProfileRegistry.
# Each entry references the parent authoritative profile (parent_profile).


DEFERRED_SIGNALS: list[dict[str, object]] = [
    {
        "raw_signal": "T_A_P_O_G",
        "direction": "positive",
        "proposed_meaning": "grid exporting (selling to Afinia)",
        "parent_profile": "grid_t_a_p_o_g",
        "status": "DEFERRED",
        "evidence_count": 0,
        "reason": (
            "No ST_PG1='Selling energy' anchor confirmed. "
            "Requires natural authorized export event with semantic anchor."
        ),
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "UAP1",
        "direction": "positive",
        "proposed_meaning": "L1 phase exporting to grid",
        "parent_profile": "grid_t_a_p_o_g",
        "status": "DEFERRED",
        "evidence_count": 0,
        "reason": "No positive UAP1 samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "UAP1",
        "direction": "negative",
        "proposed_meaning": "L1 grid import",
        "parent_profile": "grid_t_a_p_o_g",
        "status": "DEFERRED_FAMILY_PENDING_UAP2",
        "evidence_count": 4,
        "reason": (
            "UAP1 negative aligned with ST_PG1='Purchasing energy' (n=4, ap=4). "
            "Confirmed one-direction in private evidence. "
            "DEFERRED as family — UAP2 ambiguity must be resolved first."
        ),
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "UAP2",
        "direction": "positive",
        "proposed_meaning": "L2 phase exporting to grid",
        "parent_profile": "grid_t_a_p_o_g",
        "status": "DEFERRED_AMBIGUOUS",
        "evidence_count": 2,
        "reason": (
            "2 positive UAP2 samples at night during GRID_IMPORTING regime. "
            "No ST_PG1='Selling energy' anchor."
        ),
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "UAP2",
        "direction": "negative",
        "proposed_meaning": "L2 grid import",
        "parent_profile": "grid_t_a_p_o_g",
        "status": "DEFERRED_STRONG_CANDIDATE",
        "evidence_count": 1,
        "reason": (
            "1 negative UAP2 sample aligned with ST_PG1='Purchasing energy' "
            "(n=1, ap=1). Single observation insufficient."
        ),
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "DP1",
        "direction": "negative",
        "proposed_meaning": "reverse DC power — anomaly",
        "parent_profile": "pv_c_p_pvt",
        "status": "NOT_ASSESSED",
        "evidence_count": 0,
        "reason": "No negative DP1 samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "DP2",
        "direction": "negative",
        "proposed_meaning": "reverse DC power — anomaly",
        "parent_profile": "pv_c_p_pvt",
        "status": "NOT_ASSESSED",
        "evidence_count": 0,
        "reason": "No negative DP2 samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "C_P_PVT",
        "direction": "negative",
        "proposed_meaning": "reverse PV charging — anomaly",
        "parent_profile": "pv_c_p_pvt",
        "status": "NOT_ASSESSED",
        "evidence_count": 0,
        "reason": "No negative C_P_PVT samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "C_P_L1",
        "direction": "negative",
        "proposed_meaning": "L1 reverse power — not declared",
        "parent_profile": "load_e_puse_t1",
        "status": "NOT_DECLARED",
        "evidence_count": 0,
        "reason": "No negative C_P_L1 samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "C_P_L2",
        "direction": "negative",
        "proposed_meaning": "L2 reverse power — not declared",
        "parent_profile": "load_e_puse_t1",
        "status": "NOT_DECLARED",
        "evidence_count": 0,
        "reason": "No negative C_P_L2 samples observed.",
        "production_registry_allowed": False,
    },
    {
        "raw_signal": "E_Puse_t1",
        "direction": "negative",
        "proposed_meaning": "reverse consumption — not declared",
        "parent_profile": "load_e_puse_t1",
        "status": "NOT_DECLARED",
        "evidence_count": 0,
        "reason": "No negative E_Puse_t1 samples observed.",
        "production_registry_allowed": False,
    },
]


# ── Validation helpers (local-only, not exported) ─────────────────────────────


def is_promotable(profile_dict: dict[str, object]) -> bool:
    """Return True iff `profile_dict` can be promoted as a PowerSignProfile.

    Supporting signals and deferred signals carry
    `production_registry_allowed=False`; this helper short-circuits those.
    PowerSignProfile entries must declare `unit="W"`.
    """
    if profile_dict.get("production_registry_allowed") is False:
        return False
    return profile_dict.get("unit") == "W"


def count_supporting_signals_not_promotable() -> int:
    """Return the count of SUPPORTING_SIGNALS with production_registry_allowed=False."""
    return sum(
        1
        for entry in SUPPORTING_SIGNALS.values()
        if entry.get("production_registry_allowed") is False
    )


def count_deferred_signals_not_promotable() -> int:
    """Return the count of DEFERRED_SIGNALS with production_registry_allowed=False."""
    return sum(1 for entry in DEFERRED_SIGNALS if entry.get("production_registry_allowed") is False)


__all__ = [
    "DEFERRED_SIGNALS",
    "EVIDENCE_REF",
    "LEGACY_EVIDENCE_REF",
    "PROFILE_VERSION",
    "SUPPORTING_SIGNALS",
    "UPDATED_PROFILES",
    "build_updated_profiles",
    "count_deferred_signals_not_promotable",
    "count_supporting_signals_not_promotable",
    "is_promotable",
]
