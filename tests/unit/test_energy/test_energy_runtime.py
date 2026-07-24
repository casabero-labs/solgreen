from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pydantic
import pytest

from solgreen.energy.integration import (
    IntegrationMethod,
    IntegrationProfile,
    SampleSemantics,
)
from solgreen.energy.normalization import NormalizationStatus
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerDirection,
    SourceSystem,
)

if TYPE_CHECKING:
    from solgreen.integrations.solarman.energy_runtime import (
        SolarmanEnergyIntegrationContext,
    )


def _make_test_context() -> SolarmanEnergyIntegrationContext:
    from solgreen.integrations.solarman.energy_runtime import (
        EnergyIntegrationMode,
        SolarmanEnergyIntegrationContext,
    )

    return SolarmanEnergyIntegrationContext(
        mode=EnergyIntegrationMode.INSTANTANEOUS,
        profile_version="v1",
        expected_interval=timedelta(minutes=5),
        maximum_authorized_interval=timedelta(minutes=15),
        lookback=timedelta(hours=1),
    )


class TestSolarmanPersistedSignalRow:
    def test_valid_row_with_all_fields(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        row = SolarmanPersistedSignalRow(
            collection_time=ts,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            grid_import_w=500.0,
        )
        assert row.collection_time == ts
        assert row.grid_import_w == 500.0
        assert row.sign_profile_version == "v1"

    def test_naive_timestamp_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            SolarmanPersistedSignalRow(
                collection_time=ts,
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                normalized_status=NormalizationStatus.NORMALIZED,
            )

    def test_nan_power_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="must be finite"):
            SolarmanPersistedSignalRow(
                collection_time=ts,
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                normalized_status=NormalizationStatus.NORMALIZED,
                grid_import_w=float("nan"),
            )

    def test_inf_power_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="must be finite"):
            SolarmanPersistedSignalRow(
                collection_time=ts,
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                normalized_status=NormalizationStatus.NORMALIZED,
                grid_import_w=float("inf"),
            )

    def test_negative_power_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="must be non-negative"):
            SolarmanPersistedSignalRow(
                collection_time=ts,
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                normalized_status=NormalizationStatus.NORMALIZED,
                grid_import_w=-100.0,
            )

    def test_zero_power_accepted(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        row = SolarmanPersistedSignalRow(
            collection_time=ts,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            grid_import_w=0.0,
        )
        assert row.grid_import_w == 0.0

    def test_frozen_model(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
        )

        ts = datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)
        row = SolarmanPersistedSignalRow(
            collection_time=ts,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
        )
        with pytest.raises(pydantic.ValidationError):
            row.grid_import_w = 100.0


class TestMapRowToDirectionalPower:
    def _ts(self) -> datetime:
        return datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)

    def test_grid_import(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            grid_import_w=500.0,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.GRID_IMPORT
        assert magnitude == 500.0

    def test_grid_export(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            grid_export_w=300.0,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.GRID_EXPORT
        assert magnitude == 300.0

    def test_battery_charge(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            battery_charge_w=200.0,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.BATTERY_CHARGE
        assert magnitude == 200.0

    def test_battery_discharge(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            battery_discharge_w=150.0,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.BATTERY_DISCHARGE
        assert magnitude == 150.0

    def test_pv_generation(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            pv_generation_w=4000.0,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.PV_GENERATION
        assert magnitude == 4000.0

    def test_no_power_returns_unknown(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            _map_row_to_directional_power,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
        )
        direction, magnitude = _map_row_to_directional_power(row)
        assert direction == PowerDirection.UNKNOWN
        assert magnitude is None


class TestAdaptPersistedRowToObservation:
    def _ts(self) -> datetime:
        return datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC)

    def test_normalized_with_profile_version_grid_import(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            grid_import_w=500.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.GRID_IMPORT)
        assert obs.power_w == 500.0
        assert obs.status == NormalizationStatus.NORMALIZED
        assert obs.profile_version == "v1"
        assert obs.direction == PowerDirection.GRID_IMPORT

    def test_normalized_with_profile_version_grid_export(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            grid_export_w=300.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.GRID_EXPORT)
        assert obs.power_w == 300.0

    def test_normalized_with_profile_version_battery_charge(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            battery_charge_w=200.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.BATTERY_CHARGE)
        assert obs.power_w == 200.0

    def test_normalized_with_profile_version_battery_discharge(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            battery_discharge_w=150.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.BATTERY_DISCHARGE)
        assert obs.power_w == 150.0

    def test_normalized_with_profile_version_pv_generation(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            pv_generation_w=4000.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.PV_GENERATION)
        assert obs.power_w == 4000.0

    def test_normalized_missing_profile_version_produces_profile_not_found(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version=None,
            grid_import_w=500.0,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.GRID_IMPORT)
        assert obs.power_w is None
        assert obs.status == NormalizationStatus.PROFILE_NOT_FOUND
        assert obs.profile_version is None

    def test_normalized_row_direction_mismatch_raises(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.NORMALIZED,
            sign_profile_version="v1",
            grid_import_w=500.0,
        )
        with pytest.raises(ValueError, match="does not match"):
            adapt_persisted_row_to_observation(row, PowerDirection.GRID_EXPORT)

    def test_non_normalized_row_produces_none_power(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanPersistedSignalRow,
            adapt_persisted_row_to_observation,
        )

        row = SolarmanPersistedSignalRow(
            collection_time=self._ts(),
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            normalized_status=NormalizationStatus.PROFILE_NOT_CONFIRMED,
        )
        obs = adapt_persisted_row_to_observation(row, PowerDirection.GRID_IMPORT)
        assert obs.power_w is None
        assert obs.status == NormalizationStatus.PROFILE_NOT_CONFIRMED


class TestSolarmanEnergyIntegrationContext:
    def test_off_default_construction(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        ctx = SolarmanEnergyIntegrationContext(mode=EnergyIntegrationMode.OFF)
        assert ctx.mode is EnergyIntegrationMode.OFF
        assert ctx.profile is None

    def test_off_rejects_profile_version(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="OFF does not accept profile_version"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.OFF,
                profile_version="v1",
            )

    def test_off_rejects_expected_interval(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="OFF does not accept expected_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.OFF,
                expected_interval=timedelta(minutes=5),
            )

    def test_off_rejects_max_interval(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="OFF does not accept maximum_authorized_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.OFF,
                maximum_authorized_interval=timedelta(minutes=15),
            )

    def test_off_rejects_lookback(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="OFF does not accept lookback"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.OFF,
                lookback=timedelta(hours=1),
            )

    def test_off_rejects_profile(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="OFF does not accept a profile"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.OFF,
                profile=IntegrationProfile(
                    profile_version="v1",
                    sample_semantics=SampleSemantics.INSTANTANEOUS,
                    integration_method=IntegrationMethod.TRAPEZOIDAL,
                    expected_interval=timedelta(minutes=5),
                    maximum_authorized_interval=timedelta(minutes=15),
                ),
            )

    def test_instantaneous_requires_profile_version(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="requires profile_version"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                expected_interval=timedelta(minutes=5),
                maximum_authorized_interval=timedelta(minutes=15),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_requires_expected_interval(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="requires expected_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                maximum_authorized_interval=timedelta(minutes=15),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_requires_max_interval(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="requires maximum_authorized_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(minutes=5),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_requires_lookback(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="requires lookback"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(minutes=5),
                maximum_authorized_interval=timedelta(minutes=15),
            )

    def test_instantaneous_zero_expected_interval_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="strictly positive"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(0),
                maximum_authorized_interval=timedelta(minutes=15),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_negative_expected_interval_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="strictly positive"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(seconds=-1),
                maximum_authorized_interval=timedelta(minutes=15),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_max_less_than_expected_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="must be >= expected_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(minutes=15),
                maximum_authorized_interval=timedelta(minutes=5),
                lookback=timedelta(hours=1),
            )

    def test_instantaneous_lookback_less_than_max_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        with pytest.raises(ValueError, match="must be >= maximum_authorized_interval"):
            SolarmanEnergyIntegrationContext(
                mode=EnergyIntegrationMode.INSTANTANEOUS,
                profile_version="v1",
                expected_interval=timedelta(minutes=5),
                maximum_authorized_interval=timedelta(minutes=15),
                lookback=timedelta(minutes=10),
            )

    def test_instantaneous_valid_config(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        ctx = SolarmanEnergyIntegrationContext(
            mode=EnergyIntegrationMode.INSTANTANEOUS,
            profile_version="v1",
            expected_interval=timedelta(minutes=5),
            maximum_authorized_interval=timedelta(minutes=15),
            lookback=timedelta(hours=1),
        )
        assert ctx.mode is EnergyIntegrationMode.INSTANTANEOUS
        assert ctx.profile_version == "v1"
        assert ctx.profile is not None
        assert ctx.profile.sample_semantics == SampleSemantics.INSTANTANEOUS
        assert ctx.profile.integration_method == IntegrationMethod.TRAPEZOIDAL

    def test_instantaneous_lookback_equal_to_max_accepted(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        ctx = SolarmanEnergyIntegrationContext(
            mode=EnergyIntegrationMode.INSTANTANEOUS,
            profile_version="v1",
            expected_interval=timedelta(minutes=5),
            maximum_authorized_interval=timedelta(minutes=15),
            lookback=timedelta(minutes=15),
        )
        assert ctx.lookback == timedelta(minutes=15)

    def test_instantaneous_max_equal_to_expected_accepted(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
        )

        ctx = SolarmanEnergyIntegrationContext(
            mode=EnergyIntegrationMode.INSTANTANEOUS,
            profile_version="v1",
            expected_interval=timedelta(minutes=5),
            maximum_authorized_interval=timedelta(minutes=5),
            lookback=timedelta(hours=1),
        )
        assert ctx.maximum_authorized_interval == ctx.expected_interval


class TestSolarmanEnergyRuntimeResult:
    def test_frozen(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            SolarmanEnergyRuntimeResult,
        )

        result = SolarmanEnergyRuntimeResult(enabled=True, profile_version="v1")
        with pytest.raises(pydantic.ValidationError):
            result.profile_version = "v2"


class TestBuildEnergyContext:
    def test_off_by_default(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            build_energy_context,
        )

        ctx = build_energy_context()
        assert ctx.mode is EnergyIntegrationMode.OFF

    def test_cli_mode_overrides_env(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            build_energy_context,
        )

        ctx = build_energy_context(
            cli_mode="instantaneous",
            env_mode="off",
            cli_profile_version="v2",
            env_profile_version="v1",
            cli_expected_interval="PT5M",
            env_expected_interval="PT10M",
            cli_max_interval="PT15M",
            env_max_interval="PT30M",
            cli_lookback="PT1H",
            env_lookback="PT2H",
        )
        assert ctx.mode is EnergyIntegrationMode.INSTANTANEOUS
        assert ctx.profile_version == "v2"
        assert ctx.expected_interval == timedelta(minutes=5)
        assert ctx.maximum_authorized_interval == timedelta(minutes=15)
        assert ctx.lookback == timedelta(hours=1)

    def test_env_values_used_when_cli_absent(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            build_energy_context,
        )

        ctx = build_energy_context(
            env_mode="instantaneous",
            env_profile_version="v1",
            env_expected_interval="PT5M",
            env_max_interval="PT15M",
            env_lookback="PT1H",
        )
        assert ctx.mode is EnergyIntegrationMode.INSTANTANEOUS
        assert ctx.profile_version == "v1"
        assert ctx.expected_interval == timedelta(minutes=5)

    def test_invalid_mode_raises(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            build_energy_context,
        )

        with pytest.raises(ValueError, match="Unknown energy integration mode"):
            build_energy_context(cli_mode="basic")

    def test_iso_duration_parsing(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            build_energy_context,
        )

        ctx = build_energy_context(
            cli_mode="instantaneous",
            cli_profile_version="v1",
            cli_expected_interval="PT5M",
            cli_max_interval="PT15M",
            cli_lookback="PT1H",
        )
        assert ctx.expected_interval == timedelta(minutes=5)
        assert ctx.maximum_authorized_interval == timedelta(minutes=15)
        assert ctx.lookback == timedelta(hours=1)


class TestLoadPersistedSignalRows:
    def test_naive_period_start_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            load_persisted_signal_rows,
        )

        conn = MagicMock()
        with pytest.raises(ValueError, match="period_start must be timezone-aware"):
            load_persisted_signal_rows(
                conn=conn,
                plant_id="P1",
                station_id="S1",
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                period_start=datetime(2025, 7, 24, 9, 0, 0),
                period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
            )

    def test_naive_period_end_rejected(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            load_persisted_signal_rows,
        )

        conn = MagicMock()
        with pytest.raises(ValueError, match="period_end must be timezone-aware"):
            load_persisted_signal_rows(
                conn=conn,
                plant_id="P1",
                station_id="S1",
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
                period_end=datetime(2025, 7, 24, 10, 0, 0),
            )


class TestRunEnergyIntegration:
    def test_off_mode_returns_disabled(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            EnergyIntegrationMode,
            SolarmanEnergyIntegrationContext,
            run_energy_integration,
        )

        ctx = SolarmanEnergyIntegrationContext(mode=EnergyIntegrationMode.OFF)
        conn = MagicMock()
        result = run_energy_integration(
            conn=conn,
            plant_id="P1",
            station_id="S1",
            context=ctx,
            period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
        )
        assert result.enabled is False

    def test_five_series_attempted(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            run_energy_integration,
        )

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        cur.fetchall.return_value = []

        result = run_energy_integration(
            conn=conn,
            plant_id="P1",
            station_id="S1",
            context=_make_test_context(),
            period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
        )
        assert result.series_attempted == 5
        assert result.series_succeeded == 5
        assert result.series_failed == 0
        assert result.enabled is True

    def test_results_not_persisted(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            run_energy_integration,
        )

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        cur.fetchall.return_value = []

        result = run_energy_integration(
            conn=conn,
            plant_id="P1",
            station_id="S1",
            context=_make_test_context(),
            period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
        )
        assert result.results_persisted is False

    def test_empty_rows_per_series_produces_valid_result(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            run_energy_integration,
        )

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        cur.fetchall.return_value = []

        result = run_energy_integration(
            conn=conn,
            plant_id="P1",
            station_id="S1",
            context=_make_test_context(),
            period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
        )
        assert len(result.per_series_results) == 5
        assert len(result.per_series_errors) == 0

    def test_partial_success_when_series_fails(self) -> None:
        from solgreen.integrations.solarman.energy_runtime import (
            run_energy_integration,
        )

        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        cur.fetchall.side_effect = [
            [],
            Exception("db error"),
            [],
            [],
            [],
        ]

        result = run_energy_integration(
            conn=conn,
            plant_id="P1",
            station_id="S1",
            context=_make_test_context(),
            period_start=datetime(2025, 7, 24, 9, 0, 0, tzinfo=UTC),
            period_end=datetime(2025, 7, 24, 10, 0, 0, tzinfo=UTC),
        )
        assert result.series_attempted == 5
        assert result.series_succeeded == 4
        assert result.series_failed == 1
        assert len(result.per_series_errors) == 1
        assert "db error" in result.per_series_errors[0][1]
