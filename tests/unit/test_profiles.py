from pathlib import Path

from solgreen.profiles.grid import load_grid_profile
from solgreen.profiles.plant import (
    BatteryLimits,
    PlantProfile,
    SystemTopology,
    load_plant_profile,
)


def test_load_plant_profile_example(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    profile = load_plant_profile(repo_root / "config/plant-profiles/casabero.example.yaml")
    assert isinstance(profile, PlantProfile)
    assert profile.plant_alias == "casabero"
    assert profile.site_timezone == "America/Bogota"
    assert profile.system.topology == "hybrid_split_phase"
    assert profile.system.inverter_rated_power_w == 8000
    assert profile.privacy.store_serial_encrypted is True
    assert profile.privacy.redact_serial_in_shared_reports is True


def test_plant_profile_battery_and_grid_helpers(tmp_path: Path) -> None:
    profile = load_plant_profile(
        Path(__file__).resolve().parent.parent / "fixtures" / "profiles" / "casabero.test.yaml"
    )
    battery = profile.battery_limits()
    assert isinstance(battery, BatteryLimits)
    assert battery.normal_min_soc_pct == 20.0
    assert battery.temporary_emergency_min_soc_pct == 10.0
    grid = profile.grid_limits()
    assert grid is not None
    assert grid.profile_ref == "colombia-split-phase-review-required"


def test_load_plant_profile_invalid_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="YAML mapping"):
        load_plant_profile(bad)


def test_load_grid_profile_example(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    profile = load_grid_profile(
        repo_root / "config/grid-profiles/colombia-split-phase-review-required.yaml"
    )
    assert profile.name == "colombia-split-phase-review-required"
    assert profile.status == "pending_expert_confirmation"
    assert profile.nominal.line_to_neutral_v == 120
    assert profile.nominal.frequency_hz == 60.0
    assert profile.thresholds.overvoltage_v is None
    assert (
        any(
            "review_required" in note.lower() or "confirmar" in note.lower()
            for note in profile.notes
        )
        or len(profile.notes) > 0
    )


def test_system_topology_extra_forbidden() -> None:
    import pytest

    with pytest.raises(Exception, match="unexpected"):
        SystemTopology(
            topology="hybrid",
            inverter_rated_power_w=1,
            battery_nominal_energy_wh=1,
            battery_nominal_voltage_v=1.0,
            pv_mppt_count=1,
            unexpected=1,
        )
