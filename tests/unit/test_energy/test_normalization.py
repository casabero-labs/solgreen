from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta, tzinfo

import pytest

from solgreen.energy.normalization import (
    DirectionalPowerResult,
    NormalizationStatus,
    normalize_power_value,
)
from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    PowerDirection,
    PowerSignProfile,
    PowerSignProfileRegistry,
    ProfileStatus,
    SourceSystem,
)

_TS = datetime(2026, 7, 21, 12, 0, 0, tzinfo=UTC)
_VALID_TO = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


def _grid_profile(
    positive: PowerDirection = PowerDirection.GRID_IMPORT,
    negative: PowerDirection = PowerDirection.GRID_EXPORT,
    authority: AuthorityClass = AuthorityClass.OPERATIONAL,
    field: CanonicalPowerField = CanonicalPowerField.FLOW_GRID,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id="casabero",
        canonical_field=field,
        source_system=source,
        authority_class=authority,
        measurement_point="grid_meter",
        unit="W",
        positive_means=positive,
        negative_means=negative,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:grid-01",),
        profile_version="1.0.0",
        valid_from=_TS,
        valid_to=_VALID_TO,
    )


def _grid_profile_inverted(
    field: CanonicalPowerField = CanonicalPowerField.FLOW_GRID,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
) -> PowerSignProfile:
    return _grid_profile(
        positive=PowerDirection.GRID_EXPORT,
        negative=PowerDirection.GRID_IMPORT,
        field=field,
        source=source,
    )


def _battery_profile(
    positive: PowerDirection = PowerDirection.BATTERY_DISCHARGE,
    negative: PowerDirection = PowerDirection.BATTERY_CHARGE,
    field: CanonicalPowerField = CanonicalPowerField.FLOW_BATTERY,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id="casabero",
        canonical_field=field,
        source_system=source,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="battery_terminals",
        unit="W",
        positive_means=positive,
        negative_means=negative,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:battery-01",),
        profile_version="1.0.0",
        valid_from=_TS,
        valid_to=_VALID_TO,
    )


def _battery_profile_inverted(
    field: CanonicalPowerField = CanonicalPowerField.FLOW_BATTERY,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
) -> PowerSignProfile:
    return _battery_profile(
        positive=PowerDirection.BATTERY_CHARGE,
        negative=PowerDirection.BATTERY_DISCHARGE,
        field=field,
        source=source,
    )


def _pv_profile(
    field: CanonicalPowerField = CanonicalPowerField.TELEMETRY_PV,
    source: SourceSystem = SourceSystem.INVERTER_TELEMETRY,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id="casabero",
        canonical_field=field,
        source_system=source,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="mppt",
        unit="W",
        positive_means=PowerDirection.PV_GENERATION,
        negative_means=PowerDirection.UNKNOWN,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:pv-01",),
        profile_version="1.0.0",
        valid_from=_TS,
        valid_to=_VALID_TO,
    )


def _load_profile() -> PowerSignProfile:
    return PowerSignProfile(
        plant_id="casabero",
        canonical_field=CanonicalPowerField.FLOW_CONSUMO,
        source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="load_side",
        unit="W",
        positive_means=PowerDirection.LOAD_CONSUMPTION,
        negative_means=PowerDirection.UNKNOWN,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:load-01",),
        profile_version="1.0.0",
        valid_from=_TS,
        valid_to=_VALID_TO,
    )


def _normalize(
    field: CanonicalPowerField,
    source: SourceSystem,
    raw: float | None,
    registry: PowerSignProfileRegistry,
) -> DirectionalPowerResult:
    return normalize_power_value(
        plant_id="casabero",
        canonical_field=field,
        source_system=source,
        timestamp=_TS,
        raw_power_w=raw,
        registry=registry,
    )


class TestNormalizationProfileResolution:
    def test_profile_absent_returns_not_found(self) -> None:
        reg = PowerSignProfileRegistry()
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.status is NormalizationStatus.PROFILE_NOT_FOUND
        assert result.profile_version is None
        assert result.profile_status is None

    def test_provisional_returns_not_confirmed(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _grid_profile()
        p = PowerSignProfile(
            plant_id=p.plant_id,
            canonical_field=p.canonical_field,
            source_system=p.source_system,
            authority_class=p.authority_class,
            measurement_point=p.measurement_point,
            unit=p.unit,
            positive_means=p.positive_means,
            negative_means=p.negative_means,
            status=ProfileStatus.PROVISIONAL,
            evidence_refs=(),
            profile_version=p.profile_version,
            valid_from=p.valid_from,
            valid_to=p.valid_to,
        )
        reg.register(p)
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        assert result.profile_status is ProfileStatus.PROVISIONAL

    def test_unknown_returns_not_confirmed(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _grid_profile()
        p = PowerSignProfile(
            plant_id=p.plant_id,
            canonical_field=p.canonical_field,
            source_system=p.source_system,
            authority_class=p.authority_class,
            measurement_point=p.measurement_point,
            unit=p.unit,
            positive_means=PowerDirection.UNKNOWN,
            negative_means=PowerDirection.UNKNOWN,
            status=ProfileStatus.UNKNOWN,
            evidence_refs=(),
            profile_version=p.profile_version,
            valid_from=p.valid_from,
            valid_to=p.valid_to,
        )
        reg.register(p)
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        assert result.profile_status is ProfileStatus.UNKNOWN

    def test_none_returns_missing_value(self) -> None:
        reg = PowerSignProfileRegistry()
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            None,
            reg,
        )
        assert result.status is NormalizationStatus.MISSING_VALUE
        assert result.raw_power_w is None

    def test_nan_returns_nonfinite(self) -> None:
        reg = PowerSignProfileRegistry()
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            float("nan"),
            reg,
        )
        assert result.status is NormalizationStatus.NONFINITE_VALUE
        assert math.isnan(result.raw_power_w)

    def test_inf_returns_nonfinite(self) -> None:
        reg = PowerSignProfileRegistry()
        result_pos = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            float("inf"),
            reg,
        )
        result_neg = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            float("-inf"),
            reg,
        )
        assert result_pos.status is NormalizationStatus.NONFINITE_VALUE
        assert result_neg.status is NormalizationStatus.NONFINITE_VALUE


class TestGridNormalization:
    def test_grid_positive_import(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            1500.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.grid_import_w == 1500.0
        assert result.grid_export_w is None

    def test_grid_negative_export(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            -800.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.grid_export_w == 800.0
        assert result.grid_import_w is None

    def test_grid_inverted_profile(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile_inverted())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            1500.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.grid_export_w == 1500.0
        assert result.grid_import_w is None

    def test_grid_zero_preserves_both_zeros(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            0.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.raw_power_w == 0.0
        assert result.grid_import_w == 0.0
        assert result.grid_export_w == 0.0

    def test_telemetry_grid_works(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(
            _grid_profile(
                field=CanonicalPowerField.TELEMETRY_GRID,
                source=SourceSystem.INVERTER_TELEMETRY,
            )
        )
        result = _normalize(
            CanonicalPowerField.TELEMETRY_GRID,
            SourceSystem.INVERTER_TELEMETRY,
            500.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.grid_import_w == 500.0


class TestBatteryNormalization:
    def test_battery_positive_discharge(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_battery_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_BATTERY,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            2000.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.battery_discharge_w == 2000.0
        assert result.battery_charge_w is None

    def test_battery_negative_charge(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_battery_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_BATTERY,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            -1500.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.battery_charge_w == 1500.0
        assert result.battery_discharge_w is None

    def test_battery_inverted_profile(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_battery_profile_inverted())
        result = _normalize(
            CanonicalPowerField.FLOW_BATTERY,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            2000.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.battery_charge_w == 2000.0
        assert result.battery_discharge_w is None

    def test_battery_zero_preserves_both_zeros(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_battery_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_BATTERY,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            0.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.raw_power_w == 0.0
        assert result.battery_charge_w == 0.0
        assert result.battery_discharge_w == 0.0


class TestUnsignedNormalization:
    def test_pv_positive_generation(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_pv_profile())
        result = _normalize(
            CanonicalPowerField.TELEMETRY_PV,
            SourceSystem.INVERTER_TELEMETRY,
            3500.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.pv_generation_w == 3500.0

    def test_load_positive_consumption(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_load_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_CONSUMO,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            1200.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.load_consumption_w == 1200.0

    def test_pv_negative_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_pv_profile())
        result = _normalize(
            CanonicalPowerField.TELEMETRY_PV,
            SourceSystem.INVERTER_TELEMETRY,
            -100.0,
            reg,
        )
        assert result.status is NormalizationStatus.INVALID_UNSIGNED_NEGATIVE
        assert result.pv_generation_w is None

    def test_load_negative_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_load_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_CONSUMO,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            -50.0,
            reg,
        )
        assert result.status is NormalizationStatus.INVALID_UNSIGNED_NEGATIVE
        assert result.load_consumption_w is None

    def test_pv_zero_preserves_zero(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_pv_profile())
        result = _normalize(
            CanonicalPowerField.TELEMETRY_PV,
            SourceSystem.INVERTER_TELEMETRY,
            0.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.raw_power_w == 0.0
        assert result.pv_generation_w == 0.0


class TestNormalizationInvariants:
    def test_non_normalized_does_not_populate_directions(self) -> None:
        reg = PowerSignProfileRegistry()
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.status is NormalizationStatus.PROFILE_NOT_FOUND
        assert result.grid_import_w is None
        assert result.grid_export_w is None

    def test_authority_operational_remains_operational(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile(authority=AuthorityClass.OPERATIONAL))
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.authority_class is AuthorityClass.OPERATIONAL
        assert result.status is NormalizationStatus.NORMALIZED

    def test_repeat_input_produces_identical_output(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        r1 = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        r2 = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert r1.model_dump() == r2.model_dump()

    def test_model_dump_and_json_stable(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        dumped = result.model_dump()
        json_str = result.model_dump_json()
        assert dumped["status"] == "normalized"
        assert "grid_import_w" in json_str
        assert "grid_export_w" in json_str


class TestNormalizationPrecedence:
    def test_field_mismatch_takes_precedence_over_none(self) -> None:
        reg = PowerSignProfileRegistry()
        result = normalize_power_value(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TS,
            raw_power_w=None,
            registry=reg,
        )
        assert result.status is NormalizationStatus.FIELD_MISMATCH

    def test_field_mismatch_takes_precedence_over_nan(self) -> None:
        reg = PowerSignProfileRegistry()
        result = normalize_power_value(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TS,
            raw_power_w=float("nan"),
            registry=reg,
        )
        assert result.status is NormalizationStatus.FIELD_MISMATCH

    def test_field_mismatch_takes_precedence_over_finite(self) -> None:
        reg = PowerSignProfileRegistry()
        result = normalize_power_value(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TS,
            raw_power_w=1500.0,
            registry=reg,
        )
        assert result.status is NormalizationStatus.FIELD_MISMATCH


class TestDirectionalPowerResultDomainInvariants:
    def test_grid_result_with_battery_field_rejected(self) -> None:
        with pytest.raises(ValueError, match="battery_charge_w must be None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=100.0,
                battery_charge_w=50.0,
            )

    def test_grid_result_with_pv_field_rejected(self) -> None:
        with pytest.raises(ValueError, match="pv_generation_w must be None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=100.0,
                pv_generation_w=50.0,
            )

    def test_battery_result_with_grid_field_rejected(self) -> None:
        with pytest.raises(ValueError, match="grid_import_w must be None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_BATTERY,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                battery_discharge_w=100.0,
                grid_import_w=50.0,
            )

    def test_pv_result_with_load_field_rejected(self) -> None:
        with pytest.raises(ValueError, match="load_consumption_w must be None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.TELEMETRY_PV,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=3500.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                pv_generation_w=3500.0,
                load_consumption_w=100.0,
            )

    def test_load_result_with_pv_field_rejected(self) -> None:
        with pytest.raises(ValueError, match="pv_generation_w must be None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_CONSUMO,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=1200.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                load_consumption_w=1200.0,
                pv_generation_w=100.0,
            )

    def test_normalized_result_without_domain_magnitude_rejected(self) -> None:
        with pytest.raises(ValueError, match="must populate either grid_import_w or grid_export_w"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
            )

    def test_valid_zero_grid_accepted(self) -> None:
        result = DirectionalPowerResult(
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version="1.0.0",
            profile_status=ProfileStatus.CONFIRMED,
            grid_import_w=0.0,
            grid_export_w=0.0,
        )
        assert result.grid_import_w == 0.0
        assert result.grid_export_w == 0.0

    def test_valid_zero_battery_accepted(self) -> None:
        result = DirectionalPowerResult(
            canonical_field=CanonicalPowerField.FLOW_BATTERY,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version="1.0.0",
            profile_status=ProfileStatus.CONFIRMED,
            battery_charge_w=0.0,
            battery_discharge_w=0.0,
        )
        assert result.battery_charge_w == 0.0
        assert result.battery_discharge_w == 0.0

    def test_valid_zero_pv_accepted(self) -> None:
        result = DirectionalPowerResult(
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version="1.0.0",
            profile_status=ProfileStatus.CONFIRMED,
            pv_generation_w=0.0,
        )
        assert result.pv_generation_w == 0.0

    def test_valid_zero_load_accepted(self) -> None:
        result = DirectionalPowerResult(
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=0.0,
            status=NormalizationStatus.NORMALIZED,
            profile_version="1.0.0",
            profile_status=ProfileStatus.CONFIRMED,
            load_consumption_w=0.0,
        )
        assert result.load_consumption_w == 0.0


class _NoUtcoffsetTzInfo(tzinfo):
    """Synthetic tzinfo that exists but utcoffset() returns None."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "no-utcoffset"


class TestNormalizeTimestampAware:
    def test_normalize_naive_timestamp_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        naive_ts = datetime(2026, 7, 21, 12, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            normalize_power_value(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                timestamp=naive_ts,
                raw_power_w=100.0,
                registry=reg,
            )

    def test_normalize_no_utcoffset_tzinfo_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        tz = _NoUtcoffsetTzInfo()
        with pytest.raises(ValueError, match="timezone-aware"):
            normalize_power_value(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                timestamp=datetime(2026, 7, 21, 12, 0, 0, tzinfo=tz),
                raw_power_w=100.0,
                registry=reg,
            )

    def test_field_mismatch_keeps_precedence_over_naive_timestamp(self) -> None:
        reg = PowerSignProfileRegistry()
        naive_ts = datetime(2026, 7, 21, 12, 0, 0)
        result = normalize_power_value(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=naive_ts,
            raw_power_w=100.0,
            registry=reg,
        )
        assert result.status is NormalizationStatus.FIELD_MISMATCH


class TestDirectionalPowerResultAuthorityAndSource:
    def test_normalized_grid_fiscal_authority_rejected(self) -> None:
        with pytest.raises(ValueError, match="authority_class=operational"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.FISCAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=100.0,
            )

    def test_profile_not_found_fiscal_authority_rejected(self) -> None:
        with pytest.raises(ValueError, match="authority_class=operational"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.FISCAL,
                raw_power_w=100.0,
                status=NormalizationStatus.PROFILE_NOT_FOUND,
            )

    def test_field_mismatch_fiscal_authority_rejected(self) -> None:
        with pytest.raises(ValueError, match="authority_class=operational"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.FISCAL,
                raw_power_w=100.0,
                status=NormalizationStatus.FIELD_MISMATCH,
            )

    def test_normalized_field_source_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="incompatible"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=100.0,
            )

    def test_missing_field_source_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="incompatible"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=None,
                status=NormalizationStatus.MISSING_VALUE,
            )

    def test_field_mismatch_on_compatible_pair_rejected(self) -> None:
        with pytest.raises(ValueError, match="FIELD_MISMATCH status requires"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.FIELD_MISMATCH,
            )

    def test_field_mismatch_real_accepted(self) -> None:
        result = DirectionalPowerResult(
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            raw_power_w=100.0,
            status=NormalizationStatus.FIELD_MISMATCH,
        )
        assert result.status is NormalizationStatus.FIELD_MISMATCH


class TestDirectionalPowerResultZeroInvariants:
    def test_grid_zero_without_magnitudes_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"zero grid result requires grid_import_w=0.0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=None,
                grid_export_w=0.0,
            )

    def test_grid_zero_with_only_one_magnitude_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"zero grid result requires grid_export_w=0.0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=0.0,
                grid_export_w=None,
            )

    def test_battery_zero_without_magnitudes_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"zero battery result requires battery_charge_w=0.0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_BATTERY,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                battery_charge_w=None,
                battery_discharge_w=0.0,
            )

    def test_pv_zero_without_magnitude_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"zero pv result requires pv_generation_w=0.0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.TELEMETRY_PV,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                pv_generation_w=None,
            )

    def test_load_zero_without_magnitude_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"zero load result requires load_consumption_w=0.0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_CONSUMO,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                load_consumption_w=None,
            )

    def test_four_valid_zeros_accepted(self) -> None:
        for field, source, kwargs in [
            (
                CanonicalPowerField.FLOW_GRID,
                SourceSystem.SOLARMAN_PLANT_FLOW,
                {"grid_import_w": 0.0, "grid_export_w": 0.0},
            ),
            (
                CanonicalPowerField.FLOW_BATTERY,
                SourceSystem.SOLARMAN_PLANT_FLOW,
                {"battery_charge_w": 0.0, "battery_discharge_w": 0.0},
            ),
            (
                CanonicalPowerField.TELEMETRY_PV,
                SourceSystem.INVERTER_TELEMETRY,
                {"pv_generation_w": 0.0},
            ),
            (
                CanonicalPowerField.FLOW_CONSUMO,
                SourceSystem.SOLARMAN_PLANT_FLOW,
                {"load_consumption_w": 0.0},
            ),
        ]:
            result = DirectionalPowerResult(
                canonical_field=field,
                source_system=source,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=0.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                **kwargs,
            )
            assert result.status is NormalizationStatus.NORMALIZED


class TestDirectionalPowerResultMagnitudeConservation:
    def test_grid_magnitude_different_from_raw_rejected(self) -> None:
        with pytest.raises(ValueError, match="must equal abs"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=1.0,
            )

    def test_grid_nonzero_with_both_magnitudes_rejected(self) -> None:
        with pytest.raises(ValueError, match="cannot both be populated"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                grid_import_w=100.0,
                grid_export_w=100.0,
            )

    def test_battery_magnitude_different_rejected(self) -> None:
        with pytest.raises(ValueError, match="must equal abs"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_BATTERY,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=-500.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                battery_charge_w=499.0,
            )

    def test_pv_magnitude_different_rejected(self) -> None:
        with pytest.raises(ValueError, match="must equal raw_power_w"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.TELEMETRY_PV,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=700.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                pv_generation_w=701.0,
            )

    def test_load_magnitude_different_rejected(self) -> None:
        with pytest.raises(ValueError, match="must equal raw_power_w"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_CONSUMO,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=800.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
                load_consumption_w=799.0,
            )

    def test_normalize_results_pass_invariants(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_grid_profile())
        result = _normalize(
            CanonicalPowerField.FLOW_GRID,
            SourceSystem.SOLARMAN_PLANT_FLOW,
            100.0,
            reg,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.grid_import_w == 100.0


class TestDirectionalPowerResultStatusInvariants:
    def test_profile_not_found_with_profile_version_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"profile_not_found.*profile_version=None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.PROFILE_NOT_FOUND,
                profile_version="1.0.0",
            )

    def test_missing_value_with_raw_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"missing_value.*raw_power_w=None"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.MISSING_VALUE,
            )

    def test_nonfinite_value_with_finite_raw_rejected(self) -> None:
        with pytest.raises(ValueError, match="nonfinite_value"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NONFINITE_VALUE,
            )

    def test_invalid_unsigned_negative_with_positive_raw_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"invalid_unsigned_negative.*raw_power_w < 0"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.TELEMETRY_PV,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.INVALID_UNSIGNED_NEGATIVE,
                profile_version="1.0.0",
                profile_status=ProfileStatus.CONFIRMED,
            )

    def test_profile_not_confirmed_without_metadata_rejected(self) -> None:
        with pytest.raises(ValueError, match="profile_not_confirmed"):
            DirectionalPowerResult(
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.PROFILE_NOT_CONFIRMED,
            )
