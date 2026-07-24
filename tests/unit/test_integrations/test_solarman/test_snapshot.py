from __future__ import annotations

from solgreen.integrations.solarman.snapshot import (
    API_KEY_TO_CANONICAL_FIELD,
    API_KEY_TO_CANONICAL_SIGNAL,
    SYNC_AUTHORIZED_KEYS,
    parse_current_data_to_snapshot,
)


class TestSnapshotParsing:
    def test_parse_current_data_creates_snapshot(self) -> None:
        data_list = [
            {"key": "B_P1", "value": 2427.0, "unit": "W", "name": "Battery power"},
            {"key": "T_A_P_O_G", "value": -2049.2, "unit": "W", "name": "Grid power"},
            {"key": "C_P_PVT", "value": 4115.0, "unit": "W", "name": "PV power"},
            {"key": "B_C1", "value": 100.0, "unit": "A", "name": "Current"},
        ]
        snapshot = parse_current_data_to_snapshot(
            data_list=data_list,
            device_sn="SR-12345",
            device_type="INVERTER",
            device_state=1,
            collection_time_unix=1784628000,
            station_id="ST-001",
            plant_id="SOLGREEN",
        )

        assert snapshot.device_sn == "SR-12345"
        assert snapshot.device_type == "INVERTER"
        assert snapshot.station_id == "ST-001"
        assert len(snapshot.signals) == 4

        b_p1 = snapshot.signals["B_P1"]
        assert b_p1.value == 2427.0
        assert b_p1.unit == "W"

    def test_collection_time_is_utc_aware(self) -> None:
        data_list = [{"key": "B_P1", "value": 100.0, "unit": "W"}]
        snapshot = parse_current_data_to_snapshot(
            data_list=data_list,
            device_sn="SR-1",
            device_type=None,
            device_state=None,
            collection_time_unix=1784628000,
            station_id="ST-001",
            plant_id="SOLGREEN",
        )
        assert snapshot.collection_time.tzinfo is not None

    def test_non_numeric_values_become_none(self) -> None:
        data_list = [{"key": "ST_PG1", "value": "Purchasing energy", "unit": ""}]
        snapshot = parse_current_data_to_snapshot(
            data_list=data_list,
            device_sn="SR-1",
            device_type=None,
            device_state=None,
            collection_time_unix=1784628000,
            station_id="ST-001",
            plant_id="SOLGREEN",
        )
        assert snapshot.signals["ST_PG1"].value is None

    def test_empty_data_list_produces_empty_signals(self) -> None:
        snapshot = parse_current_data_to_snapshot(
            data_list=[],
            device_sn="SR-1",
            device_type=None,
            device_state=None,
            collection_time_unix=1784628000,
            station_id="ST-001",
            plant_id="SOLGREEN",
        )
        assert len(snapshot.signals) == 0


class TestApiKeyMapping:
    def test_only_three_authorized_keys(self) -> None:
        assert frozenset({"B_P1", "T_A_P_O_G", "C_P_PVT"}) == SYNC_AUTHORIZED_KEYS

    def test_all_authorized_keys_have_canonical_field(self) -> None:
        for key in SYNC_AUTHORIZED_KEYS:
            assert key in API_KEY_TO_CANONICAL_FIELD

    def test_all_canonical_fields_are_telemetry(self) -> None:
        from solgreen.energy.sign_profiles import _TELEMETRY_FIELDS

        for key, field in API_KEY_TO_CANONICAL_FIELD.items():
            assert field in _TELEMETRY_FIELDS, f"{key} -> {field} not in TELEMETRY_FIELDS"

    def test_battery_mapping(self) -> None:
        assert API_KEY_TO_CANONICAL_SIGNAL["B_P1"] == "potencia_de_bateria_w"
        from solgreen.energy.sign_profiles import CanonicalPowerField

        assert API_KEY_TO_CANONICAL_FIELD["B_P1"] == CanonicalPowerField.TELEMETRY_BATTERY

    def test_grid_mapping(self) -> None:
        from solgreen.energy.sign_profiles import CanonicalPowerField

        assert API_KEY_TO_CANONICAL_FIELD["T_A_P_O_G"] == CanonicalPowerField.TELEMETRY_GRID

    def test_pv_mapping(self) -> None:
        from solgreen.energy.sign_profiles import CanonicalPowerField

        assert API_KEY_TO_CANONICAL_FIELD["C_P_PVT"] == CanonicalPowerField.TELEMETRY_PV
