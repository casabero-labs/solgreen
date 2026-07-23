"""Tests for SOLARMAN D1.0 sign-evidence regime detection (versioned, no credentials)."""

from __future__ import annotations

from solgreen.integrations.solarman.evidence import (
    TRACKED_KEYS,
)
from solgreen.integrations.solarman.evidence import (
    detect_regimes as _detect_regimes,
)


class TestExtractTracked:
    """Tests for TRACKED_KEYS coverage — synthetic data, no real device fields."""

    def test_all_significant_fields_are_tracked(self):
        significant = {
            "B_P1",
            "B_C1",
            "B_V1",
            "B_left_cap1",
            "B_ST1",
            "BCS1",
            "T_A_P_O_G",
            "UAP1",
            "UAP2",
            "C_P_L1",
            "C_P_L2",
            "E_Puse_t1",
            "DP1",
            "DP2",
            "C_P_PVT",
            "ST_PG1",
            "CSOM",
            "INV_ST1",
            "Et_pu1",
            "t_gc1",
            "Et_use1",
            "Et_ge0",
        }
        assert significant.issubset(TRACKED_KEYS), f"Missing: {significant - TRACKED_KEYS}"


class TestDetectRegimes:
    """Tests for detect_regimes — all synthetic data, no real device IDs or values."""

    def test_no_events_on_first_snapshot(self):
        curr = {
            "B_ST1": {"value": "Discharging"},
            "T_A_P_O_G": {"value": -9},
            "ST_PG1": {"value": "Purchasing energy"},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        _regimes, events = _detect_regimes(curr, prev=None)
        assert events == []

    def test_battery_started_discharging(self):
        prev = {
            "B_ST1": {"value": "Charging"},
            "B_P1": {"value": -500},
            "ST_PG1": {"value": "Purchasing energy"},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charging"},
        }
        curr = {
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 1951},
            "ST_PG1": {"value": "Purchasing energy"},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        _, events = _detect_regimes(curr, prev=prev)
        assert "battery_started_discharging" in events

    def test_battery_started_charging(self):
        prev = {
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 1951},
            "ST_PG1": {"value": "Purchasing energy"},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        curr = {
            "B_ST1": {"value": "Charging"},
            "B_P1": {"value": -500},
            "ST_PG1": {"value": "Purchasing energy"},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charging"},
        }
        _, events = _detect_regimes(curr, prev=prev)
        assert "battery_started_charging" in events

    def test_battery_discharging_regime(self):
        record = {
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 1951},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Purchasing energy"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        regimes, _ = _detect_regimes(record)
        assert "BATTERY_DISCHARGING" in regimes
        assert "PV_GENERATING" not in regimes

    def test_battery_charging_regime(self):
        record = {
            "B_ST1": {"value": "Charging"},
            "B_P1": {"value": -500},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Purchasing energy"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charging"},
        }
        regimes, _ = _detect_regimes(record)
        assert "BATTERY_CHARGING" in regimes

    def test_pv_generating_regime(self):
        record = {
            "B_ST1": {"value": "Standby"},
            "B_P1": {"value": 0},
            "DP1": {"value": 3000},
            "DP2": {"value": 1500},
            "C_P_PVT": {"value": 4500},
            "ST_PG1": {"value": "Standby"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Standby"},
        }
        regimes, _ = _detect_regimes(record)
        assert "PV_GENERATING" in regimes
        assert "BATTERY_DISCHARGING" not in regimes
        assert "BATTERY_CHARGING" not in regimes

    def test_grid_importing_regime(self):
        record = {
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 500},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Purchasing energy"},
            "T_A_P_O_G": {"value": -9},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        regimes, _ = _detect_regimes(record)
        assert "GRID_IMPORTING" in regimes

    def test_grid_exporting_regime_requires_positive_t_a_p_o_g(self):
        record = {
            "B_ST1": {"value": "Standby"},
            "B_P1": {"value": 0},
            "DP1": {"value": 5000},
            "DP2": {"value": 0},
            "T_A_P_O_G": {"value": 500},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Selling energy"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Standby"},
        }
        regimes, _ = _detect_regimes(record)
        assert "GRID_EXPORTING" in regimes

    def test_grid_exporting_requires_semantic_text(self):
        record = {
            "B_ST1": {"value": "Standby"},
            "B_P1": {"value": 0},
            "DP1": {"value": 5000},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Purchasing energy"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Standby"},
        }
        regimes, _ = _detect_regimes(record)
        assert "GRID_EXPORTING" not in regimes

    def test_load_active_regime(self):
        record = {
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 1951},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Purchasing energy"},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        regimes, _ = _detect_regimes(record)
        assert "LOAD_ACTIVE" in regimes

    def test_grid_selling_event(self):
        prev = {
            "ST_PG1": {"value": "Purchasing energy"},
            "B_ST1": {"value": "Discharging"},
            "B_P1": {"value": 1951},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 1774},
            "C_P_L1": {"value": 792},
            "C_P_L2": {"value": 982},
            "BCS1": {"value": "Charge off"},
        }
        curr = {
            "ST_PG1": {"value": "Selling energy"},
            "B_ST1": {"value": "Standby"},
            "B_P1": {"value": 0},
            "DP1": {"value": 5000},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "E_Puse_t1": {"value": 500},
            "C_P_L1": {"value": 300},
            "C_P_L2": {"value": 200},
            "BCS1": {"value": "Standby"},
        }
        _, events = _detect_regimes(curr, prev=prev)
        assert "grid_started_exporting" in events

    def test_load_power_tolerance_configurable(self):
        record = {
            "B_ST1": {"value": "Standby"},
            "B_P1": {"value": 0},
            "DP1": {"value": 0},
            "DP2": {"value": 0},
            "C_P_PVT": {"value": 0},
            "ST_PG1": {"value": "Standby"},
            "E_Puse_t1": {"value": 1000},
            "C_P_L1": {"value": 940},
            "C_P_L2": {"value": 0},
            "BCS1": {"value": "Standby"},
        }
        regimes_default, _ = _detect_regimes(record)
        assert "LOAD_ACTIVE" not in regimes_default

        regimes_tolerant, _ = _detect_regimes(record, load_power_tolerance=0.10)
        assert "LOAD_ACTIVE" in regimes_tolerant
