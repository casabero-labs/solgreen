"""Sign-evidence analysis for SOLARMAN D1.0 inverter data.

This module contains versioned, credential-free regime detection logic
extracted from real D1.0 snapshot analysis. No API keys or secrets.
"""

from __future__ import annotations

from typing import Any

LOAD_POWER_TOLERANCE = 0.05
LOAD_THRESHOLD = 50.0
PV_POWER_THRESHOLD = 10.0

TRACKED_KEYS = frozenset(
    [
        "B_ST1",
        "BCS1",
        "BCT",
        "B_P1",
        "B_C1",
        "B_V1",
        "B_left_cap1",
        "ST_PG1",
        "T_A_P_O_G",
        "UAP1",
        "UAP2",
        "C_P_L1",
        "C_P_L2",
        "E_Puse_t1",
        "C_P_PVT",
        "DP1",
        "DP2",
        "Et_pu1",
        "Etdy_pu1",
        "t_gc1",
        "t_gc_tdy1",
        "Et_use1",
        "Etdy_use1",
        "Et_ge0",
        "Etdy_ge1",
        "t_cg_n1",
        "t_dcg_n1",
        "Etdy_cg1",
        "Etdy_dcg1",
        "CSOM",
        "INV_ST1",
        "SS1",
        "ENV_T0",
        "RT_I",
        "PVRT",
        "AV1",
        "AV2",
        "AC1",
        "AC2",
        "L1_MAIN_V",
        "L2_MAIN_V",
        "L1_MAIN_C",
        "L2_MAIN_C",
    ]
)


def _get_num(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def detect_regimes(
    tracked: dict[str, Any],
    prev: dict[str, Any] | None = None,
    load_power_tolerance: float = LOAD_POWER_TOLERANCE,
) -> tuple[set[str], list[str]]:
    """Detect operational regimes and events from tracked inverter data.

    Regimes returned (mutually non-exclusive):
        - BATTERY_CHARGING  : battery accepting power (B_P1 < 0 + semantic state)
        - BATTERY_DISCHARGING: battery delivering power (B_P1 > 0 + B_ST1=Discharging)
        - GRID_IMPORTING    : drawing from grid (T_A_P_O_G < 0 + ST_PG1=Purchasing energy)
        - GRID_EXPORTING    : selling to grid (T_A_P_O_G > 0 + ST_PG1=Selling energy)
        - PV_GENERATING     : solar production active (DP1/DP2/C_P_PVT > 0)
        - LOAD_ACTIVE       : loads drawing power (E_Puse_t1 > 0, phase sum consistent)

    Events returned:
        - battery_started_discharging
        - battery_started_charging
        - battery_power_became_positive
        - battery_power_became_negative
        - grid_started_purchasing
        - grid_started_exporting
        - grid_stopped_exporting
    """
    regimes: set[str] = set()
    events: list[str] = []

    b_p1 = _get_num(tracked.get("B_P1", {}).get("value"))
    b_st1 = str(tracked.get("B_ST1", {}).get("value", ""))
    bcs1 = str(tracked.get("BCS1", {}).get("value", ""))
    t_a_p_o_g = _get_num(tracked.get("T_A_P_O_G", {}).get("value"))
    st_pg1 = str(tracked.get("ST_PG1", {}).get("value", ""))
    dp1 = _get_num(tracked.get("DP1", {}).get("value"))
    dp2 = _get_num(tracked.get("DP2", {}).get("value"))
    c_p_pvt = _get_num(tracked.get("C_P_PVT", {}).get("value"))
    e_puse_t1 = _get_num(tracked.get("E_Puse_t1", {}).get("value"))

    if dp1 > 0 or dp2 > 0 or c_p_pvt > 0:
        regimes.add("PV_GENERATING")

    charge_states = {"charging", "charge", "charging mode", "charge mode"}
    has_charge_semantic = any(s in b_st1.lower() for s in charge_states) or any(
        s in bcs1.lower() for s in charge_states
    )
    if b_p1 < 0 and has_charge_semantic:
        regimes.add("BATTERY_CHARGING")

    if b_p1 > 0 and "discharging" in b_st1.lower():
        regimes.add("BATTERY_DISCHARGING")

    if t_a_p_o_g < 0 and "purchasing energy" in st_pg1.lower():
        regimes.add("GRID_IMPORTING")

    export_states = {"selling", "feed", "export", "sold"}
    if t_a_p_o_g > 0 and any(s in st_pg1.lower() for s in export_states):
        regimes.add("GRID_EXPORTING")

    if e_puse_t1 > 0:
        c_p_l1 = _get_num(tracked.get("C_P_L1", {}).get("value"))
        c_p_l2 = _get_num(tracked.get("C_P_L2", {}).get("value"))
        if abs((c_p_l1 + c_p_l2) - e_puse_t1) <= e_puse_t1 * load_power_tolerance:
            regimes.add("LOAD_ACTIVE")

    if prev is not None:
        pb_p1 = _get_num(prev.get("B_P1", {}).get("value"))
        pst_pg1 = str(prev.get("ST_PG1", {}).get("value", ""))

        if b_p1 > 0 and pb_p1 <= 0 and "discharging" in b_st1.lower():
            events.append("battery_started_discharging")
        elif b_p1 < 0 and pb_p1 >= 0:
            events.append("battery_started_charging")

        if "purchasing energy" in st_pg1.lower() and "purchasing energy" not in pst_pg1.lower():
            events.append("grid_started_purchasing")

        export_semantic = any(s in st_pg1.lower() for s in export_states)
        pexport_semantic = any(s in pst_pg1.lower() for s in export_states)
        if export_semantic and not pexport_semantic:
            events.append("grid_started_exporting")
        elif not export_semantic and pexport_semantic:
            events.append("grid_stopped_exporting")

    return regimes, events
