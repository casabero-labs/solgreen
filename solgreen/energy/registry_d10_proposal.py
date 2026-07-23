"""
PROPOSAL: D1.0 SOLARMAN Sign Profile Registry — U2.1b.1 Update

Owner-approved sign conventions for SOLARMAN D1.0 inverter telemetry.

IMPORTANT: This file is a PROPOSAL. It does NOT modify the existing
registry_seeds.py. Owner approval is required before committing changes.

What this proposal does:
    1. Proposes 9 sign-profile entries for D1.0 signals
    2. Documents 4 existing profiles as already correctly registered
    3. Documents 11 deferred signals requiring separate approval
    4. Proposes per-phase canonical fields for future registry extension

Signal mapping (D1.0 → canonical field):
    B_P1     → TELEMETRY_BATTERY   ✓ (power, W)
    B_C1     → TELEMETRY_BATTERY   ✓ (current, A — same direction convention as B_P1)
    T_A_P_O_G → TELEMETRY_GRID    ✓ (import only in this proposal)
    DP1/DP2  → TELEMETRY_PV        ✓
    C_P_PVT  → TELEMETRY_PV        ✓
    E_Puse_t1 → FLOW_CONSUMO      ✓
    C_P_L1   → FLOW_CONSUMO        ✓ (per-phase, same canonical as total)
    C_P_L2   → FLOW_CONSUMO        ✓ (per-phase, same canonical as total)

Proposed new canonical fields (not yet in enum — require separate approval):
    TELEMETRY_GRID_L1  = "telemetry_grid_power_l1_w"
    TELEMETRY_GRID_L2  = "telemetry_grid_power_l2_w"
    TELEMETRY_PV_STRING1 = "telemetry_pv_power_string1_w"
    TELEMETRY_PV_STRING2 = "telemetry_pv_power_string2_w"

Registry changes required (in order):
    Step 1: Extend CanonicalPowerField enum with per-phase and per-string fields
    Step 2: Update normalization.py to recognize new canonical fields
    Step 3: Update registry_seeds.py evidence_refs to U2.1b.1
    Step 4: Add per-phase grid profiles (UAP1/UAP2) after enum extension

Only T_A_P_O_G represents productive grid import in this proposal.
UAP1 and UAP2 are deferred as a family until UAP2 ambiguity is resolved.

Deferred signals (NOT registered — require separate approval):
    T_A_P_O_G positive (export)      — 0 samples, no anchor
    UAP1 positive                    — 0 samples
    UAP1 negative                    — 4 samples, confirmed_one_direction (ap=4),
                                      but deferred as family until UAP2 resolved
    UAP2 positive                   — 2 samples, ambiguous
    UAP2 negative                    — 1 sample, strong_candidate, DEFER
    DP1/DP2/C_P_PVT negative        — 0 samples, NOT_ASSESSED
    C_P_L1/C_P_L2/E_Puse_t1 negative — 0 samples, NOT_DECLARED
    All grid-export directions (T_A_P_O_G+, UAP1+, UAP2+) — DEFERRED
"""

from __future__ import annotations

from datetime import UTC, datetime

from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    PowerDirection,
    ProfileStatus,
    SourceSystem,
)

PROFILE_VERSION = "u2_1b1_d1_0"
VALID_FROM = datetime(2026, 7, 23, tzinfo=UTC)
EVIDENCE_REF = "owner_decision_2026_07_23_u2_1b1"


# ── Existing registry status ────────────────────────────────────────────────────
#
# The following 4 profiles already exist in registry_seeds.py with status CONFIRMED.
# This proposal updates their evidence_refs and notes to reference U2.1b.1.
#
# Name                 Canonical field              Status
# ─────────────────────────────────────────────────────────────────────────────
# Battery B_P1         TELEMETRY_BATTERY            CONFIRMED ✓
# Grid T_A_P_O_G       TELEMETRY_GRID               CONFIRMED ✓ (import only)
# PV DP1/DP2/C_P_PVT  TELEMETRY_PV                 CONFIRMED ✓
# Load E_Puse_t1       FLOW_CONSUMO                 CONFIRMED ✓
#
# All 4 require evidence_ref update from "owner_decision_2026_07_21"
# to EVIDENCE_REF = "owner_decision_2026_07_23_u2_1b1"
#
# ─────────────────────────────────────────────────────────────────────────────


# ── Per-phase grid profiles (DEFERRED — requires enum extension) ───────────────
#
# UAP1 and UAP2 are deferred as a family until UAP2 ambiguity is resolved.
# T_A_P_O_G remains the approved total-grid import signal in this proposal.
#
# UAP1 (L1 phase grid active power):
#   canonical_field = TELEMETRY_GRID_L1  (proposed)
#   negative = L1 grid import (n=4, ap=4) — CONFIRMED_ONE_DIRECTION_PRIVATE
#   positive = DEFERRED — no ST_PG1='Selling energy' anchor confirmed
#
# UAP2 (L2 phase grid active power):
#   canonical_field = TELEMETRY_GRID_L2  (proposed)
#   negative = strong_candidate (n=1, ap=1) — DEFER
#   positive = DEFERRED_AMBIGUOUS (n=2, no anchor)


# ── Proposed sign-profile entries ─────────────────────────────────────────────
#
# 9 entries. These are PROPOSALS — not yet in registry_seeds.py.
# All are CONFIRMED or CONFIRMED_BIDIRECTIONAL based on U2.1b.1 evidence.


UPDATED_PROFILES = {
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
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "B_P1: confirmed_bidirectional. "
            "positive = battery discharging (B_P1>0 + B_ST1='Discharging', n=2 samples). "
            "negative = battery charging (B_P1<0 + B_ST1='Charging', n=2 samples). "
            "Owner-approved U2.1b.1. Evidence: 4 real snapshots, Jul 2026."
        ),
    },
    "battery_b_c1": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_BATTERY,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:b_c1",
        "unit": "A",
        "positive_means": PowerDirection.BATTERY_DISCHARGE,
        "negative_means": PowerDirection.BATTERY_CHARGE,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 0.5,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "B_C1: confirmed_bidirectional. "
            "Battery current (A). Shares direction convention with B_P1 (W), "
            "but is a different physical measurement — not interchangeable with power. "
            "positive = battery discharging (B_C1>0 aligned with B_P1>0 + B_ST1='Discharging'). "
            "negative = battery charging (B_C1<0 aligned with B_P1<0 + B_ST1='Charging'). "
            "Owner-approved U2.1b.1."
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
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "T_A_P_O_G: confirmed_one_direction (negative/import only). "
            "Only T_A_P_O_G represents productive grid import in this proposal. "
            "negative = grid importing from Afinia (T_A_P_O_G<0 + ST_PG1='Purchasing energy', n=4, ap=4). "
            "positive = DEFERRED — no ST_PG1='Selling energy' anchor confirmed. "
            "Grid export requires natural authorized event. "
            "Owner-approved U2.1b.1. Evidence: 4 real snapshots, Jul 2026."
        ),
    },
    "pv_dp1": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_PV,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:dp1",
        "unit": "W",
        "positive_means": PowerDirection.PV_GENERATION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "DP1: confirmed_one_direction (positive only). "
            "PV string 1 DC power. "
            "positive = PV generation (DP1>0 daytime, n=2 samples). "
            "zero = no generation (nighttime — not evidence of reverse). "
            "negative = NOT_ASSESSED. "
            "Owner-approved U2.1b.1. Evidence: 2 daytime + 2 nighttime snapshots."
        ),
    },
    "pv_dp2": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.TELEMETRY_PV,
        "source_system": SourceSystem.INVERTER_TELEMETRY,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "telemetry:inverter:dp2",
        "unit": "W",
        "positive_means": PowerDirection.PV_GENERATION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "DP2: confirmed_one_direction (positive only). "
            "PV string 2 DC power. Same behavior as DP1. "
            "Owner-approved U2.1b.1. Evidence: 2 daytime + 2 nighttime snapshots."
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
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "C_P_PVT: confirmed_one_direction (positive only). "
            "PV total charging power to battery. "
            "positive = PV generation used for battery charging (C_P_PVT>0, n=2). "
            "zero = no PV charging. "
            "negative = NOT_ASSESSED. "
            "Owner-approved U2.1b.1."
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
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "E_Puse_t1: confirmed_one_direction (positive only). "
            "Total household consumption power. "
            "positive = load consumption (E_Puse_t1>0, n=4). "
            "Identity confirmed: C_P_L1 + C_P_L2 == E_Puse_t1 within 0-0.4% (all 4 samples). "
            "negative = NOT_DECLARED. "
            "Owner-approved U2.1b.1."
        ),
    },
    "load_c_p_l1": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.FLOW_CONSUMO,
        "source_system": SourceSystem.SOLARMAN_PLANT_FLOW,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "flow:plant:c_p_l1",
        "unit": "W",
        "positive_means": PowerDirection.LOAD_CONSUMPTION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "C_P_L1: confirmed_one_direction (positive only). "
            "L1 load consumption. "
            "positive = L1 consumption (C_P_L1>0, n=4). "
            "Validated: C_P_L1 + C_P_L2 == E_Puse_t1 identity. "
            "negative = NOT_DECLARED. "
            "Owner-approved U2.1b.1."
        ),
    },
    "load_c_p_l2": {
        "plant_id": "SOLGREEN",
        "canonical_field": CanonicalPowerField.FLOW_CONSUMO,
        "source_system": SourceSystem.SOLARMAN_PLANT_FLOW,
        "authority_class": AuthorityClass.OPERATIONAL,
        "measurement_point": "flow:plant:c_p_l2",
        "unit": "W",
        "positive_means": PowerDirection.LOAD_CONSUMPTION,
        "negative_means": PowerDirection.UNKNOWN,
        "zero_means": PowerDirection.NO_FLOW,
        "zero_deadband_w": 5.0,
        "status": ProfileStatus.CONFIRMED,
        "evidence_refs": (EVIDENCE_REF,),
        "profile_version": PROFILE_VERSION,
        "valid_from": VALID_FROM,
        "notes": (
            "C_P_L2: confirmed_one_direction (positive only). "
            "L2 load consumption. "
            "positive = L2 consumption (C_P_L2>0, n=4). "
            "Validated: C_P_L1 + C_P_L2 == E_Puse_t1 identity. "
            "negative = NOT_DECLARED. "
            "Owner-approved U2.1b.1."
        ),
    },
}


# ── Deferred signals documentation ─────────────────────────────────────────────
#
# 11 entries. None are registered in this proposal.
# production_registry_allowed = False for all.


DEFERRED_SIGNALS = [
    {
        "signal": "T_A_P_O_G",
        "direction": "positive",
        "proposed_meaning": "grid exporting (selling to Afinia)",
        "canonical_field": "TELEMETRY_GRID",
        "status": "DEFERRED",
        "reason": (
            "No ST_PG1='Selling energy' anchor confirmed. "
            "No positive T_A_P_O_G samples observed (n=0). "
            "Requires natural authorized export event with semantic anchor."
        ),
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "UAP1",
        "direction": "positive",
        "proposed_meaning": "L1 phase exporting to grid",
        "canonical_field": "TELEMETRY_GRID_L1 (proposed)",
        "status": "DEFERRED",
        "reason": (
            "No positive UAP1 samples observed (n=0). "
            "Requires positive UAP1 with ST_PG1='Selling energy' anchor."
        ),
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "UAP1",
        "direction": "negative",
        "proposed_meaning": "L1_GRID_IMPORT",
        "canonical_field": "TELEMETRY_GRID_L1 (proposed)",
        "status": "CONFIRMED_ONE_DIRECTION_PRIVATE",
        "reason": (
            "UAP1 negative aligned with ST_PG1='Purchasing energy' (n=4, ap=4). "
            "Confirmed one-direction in private evidence. "
            "DEFERRED as family — UAP2 ambiguity must be resolved first. "
            "T_A_P_O_G remains the approved total-grid import signal."
        ),
        "evidence_count": 4,
        "production_registry_allowed": False,
    },
    {
        "signal": "UAP2",
        "direction": "positive",
        "proposed_meaning": "L2 phase exporting to grid",
        "canonical_field": "TELEMETRY_GRID_L2 (proposed)",
        "status": "DEFERRED_AMBIGUOUS",
        "reason": (
            "2 positive UAP2 samples at night during GRID_IMPORTING regime. "
            "No ST_PG1='Selling energy' anchor. Per-phase without phase-specific anchor. "
            "Status: ambiguous."
        ),
        "evidence_count": 2,
        "production_registry_allowed": False,
    },
    {
        "signal": "UAP2",
        "direction": "negative",
        "proposed_meaning": "L2_GRID_IMPORT",
        "canonical_field": "TELEMETRY_GRID_L2 (proposed)",
        "status": "DEFERRED_STRONG_CANDIDATE",
        "reason": (
            "1 negative UAP2 sample aligned with ST_PG1='Purchasing energy' (n=1, ap=1). "
            "Single observation insufficient for confirmed_one_direction. "
            "Need multiple negative samples with anchor confirmation."
        ),
        "evidence_count": 1,
        "production_registry_allowed": False,
    },
    {
        "signal": "DP1",
        "direction": "negative",
        "proposed_meaning": "reverse DC power — anomaly",
        "canonical_field": "TELEMETRY_PV",
        "status": "NOT_ASSESSED",
        "reason": "No negative DP1 samples observed. Requires investigation.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "DP2",
        "direction": "negative",
        "proposed_meaning": "reverse DC power — anomaly",
        "canonical_field": "TELEMETRY_PV",
        "status": "NOT_ASSESSED",
        "reason": "No negative DP2 samples observed. Requires investigation.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "C_P_PVT",
        "direction": "negative",
        "proposed_meaning": "reverse PV charging — anomaly",
        "canonical_field": "TELEMETRY_PV",
        "status": "NOT_ASSESSED",
        "reason": "No negative C_P_PVT samples observed.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "C_P_L1",
        "direction": "negative",
        "proposed_meaning": "L1 reverse power — not declared",
        "canonical_field": "FLOW_CONSUMO",
        "status": "NOT_DECLARED",
        "reason": "No negative C_P_L1 samples observed.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "C_P_L2",
        "direction": "negative",
        "proposed_meaning": "L2 reverse power — not declared",
        "canonical_field": "FLOW_CONSUMO",
        "status": "NOT_DECLARED",
        "reason": "No negative C_P_L2 samples observed.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
    {
        "signal": "E_Puse_t1",
        "direction": "negative",
        "proposed_meaning": "reverse consumption — not declared",
        "canonical_field": "FLOW_CONSUMO",
        "status": "NOT_DECLARED",
        "reason": "No negative E_Puse_t1 samples observed.",
        "evidence_count": 0,
        "production_registry_allowed": False,
    },
]
