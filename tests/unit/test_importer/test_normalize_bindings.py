from __future__ import annotations

from solgreen.contracts.inverter_telemetry import CANONICAL_NAME_TO_INDEX
from solgreen.energy.sign_profiles import (
    _TELEMETRY_FIELDS,
    CanonicalPowerField,
    SourceSystem,
    is_power_field_source_compatible,
)
from solgreen.importer.normalize import TELEMETRY_SIGNAL_BINDINGS


class TestMapping:
    def test_only_three_signals_in_bindings(self) -> None:
        assert len(TELEMETRY_SIGNAL_BINDINGS) == 3

    def test_all_declare_unit_w(self) -> None:
        for b in TELEMETRY_SIGNAL_BINDINGS:
            assert b.expected_unit == "W"

    def test_all_canonical_fields_are_telemetry(self) -> None:
        for b in TELEMETRY_SIGNAL_BINDINGS:
            assert b.canonical_field in _TELEMETRY_FIELDS

    def test_all_source_systems_are_inverter_telemetry(self) -> None:
        for b in TELEMETRY_SIGNAL_BINDINGS:
            assert b.source_system is SourceSystem.INVERTER_TELEMETRY

    def test_all_raw_signal_names_exist_in_specs(self) -> None:
        for b in TELEMETRY_SIGNAL_BINDINGS:
            assert b.raw_signal_name in CANONICAL_NAME_TO_INDEX

    def test_all_bindings_are_source_field_compatible(self) -> None:
        for b in TELEMETRY_SIGNAL_BINDINGS:
            assert is_power_field_source_compatible(b.canonical_field, b.source_system)

    def test_battery_signal_mapped_correctly(self) -> None:
        battery = next(
            b for b in TELEMETRY_SIGNAL_BINDINGS if b.raw_signal_name == "potencia_de_bateria_w"
        )
        assert battery.canonical_field == CanonicalPowerField.TELEMETRY_BATTERY

    def test_grid_signal_mapped_correctly(self) -> None:
        grid = next(
            b
            for b in TELEMETRY_SIGNAL_BINDINGS
            if b.raw_signal_name == "total_active_power_of_the_grid_w"
        )
        assert grid.canonical_field == CanonicalPowerField.TELEMETRY_GRID

    def test_pv_signal_mapped_correctly(self) -> None:
        pv = next(
            b for b in TELEMETRY_SIGNAL_BINDINGS if b.raw_signal_name == "pv_total_charging_power_w"
        )
        assert pv.canonical_field == CanonicalPowerField.TELEMETRY_PV

    def test_flow_consumo_not_in_bindings(self) -> None:
        fields = {b.canonical_field for b in TELEMETRY_SIGNAL_BINDINGS}
        assert CanonicalPowerField.FLOW_CONSUMO not in fields
        assert CanonicalPowerField.FLOW_PRODUCCION not in fields
        assert CanonicalPowerField.FLOW_GRID not in fields
        assert CanonicalPowerField.FLOW_BATTERY not in fields

    def test_no_extra_signals_mapped(self) -> None:
        expected = {
            "potencia_de_bateria_w",
            "total_active_power_of_the_grid_w",
            "pv_total_charging_power_w",
        }
        actual = {b.raw_signal_name for b in TELEMETRY_SIGNAL_BINDINGS}
        assert actual == expected
