from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo

import pytest
from pydantic import ValidationError

from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    DirectionEvidenceStatus,
    PowerDirection,
    PowerSignProfile,
    PowerSignProfileRegistry,
    ProfileStatus,
    SourceSystem,
    build_production_sign_profile_registry,
)

_BASE_TS = datetime(2026, 7, 21, 12, 0, 0, tzinfo=UTC)
_VALID_TO = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


def _make_grid_confirmed(
    plant_id: str = "casabero",
    positive: PowerDirection = PowerDirection.GRID_IMPORT,
    negative: PowerDirection = PowerDirection.GRID_EXPORT,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
    field: CanonicalPowerField = CanonicalPowerField.FLOW_GRID,
    valid_from: datetime = _BASE_TS,
    valid_to: datetime | None = _VALID_TO,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id=plant_id,
        canonical_field=field,
        source_system=source,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="grid_meter",
        unit="W",
        positive_means=positive,
        negative_means=negative,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:grid-night-01",),
        profile_version="1.0.0",
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _make_battery_confirmed(
    plant_id: str = "casabero",
    positive: PowerDirection = PowerDirection.BATTERY_DISCHARGE,
    negative: PowerDirection = PowerDirection.BATTERY_CHARGE,
    source: SourceSystem = SourceSystem.SOLARMAN_PLANT_FLOW,
    field: CanonicalPowerField = CanonicalPowerField.FLOW_BATTERY,
    valid_from: datetime = _BASE_TS,
    valid_to: datetime | None = _VALID_TO,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id=plant_id,
        canonical_field=field,
        source_system=source,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="battery_terminals",
        unit="W",
        positive_means=positive,
        negative_means=negative,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:battery-charge-01",),
        profile_version="1.0.0",
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _make_pv_confirmed(
    plant_id: str = "casabero",
    field: CanonicalPowerField = CanonicalPowerField.TELEMETRY_PV,
    valid_from: datetime = _BASE_TS,
    valid_to: datetime | None = _VALID_TO,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id=plant_id,
        canonical_field=field,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="mppt_input",
        unit="W",
        positive_means=PowerDirection.PV_GENERATION,
        negative_means=PowerDirection.UNKNOWN,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:pv-positive-01",),
        profile_version="1.0.0",
        valid_from=valid_from,
        valid_to=valid_to,
    )


def _make_load_confirmed(
    plant_id: str = "casabero",
    valid_from: datetime = _BASE_TS,
    valid_to: datetime | None = _VALID_TO,
) -> PowerSignProfile:
    return PowerSignProfile(
        plant_id=plant_id,
        canonical_field=CanonicalPowerField.FLOW_CONSUMO,
        source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
        authority_class=AuthorityClass.OPERATIONAL,
        measurement_point="load_side",
        unit="W",
        positive_means=PowerDirection.LOAD_CONSUMPTION,
        negative_means=PowerDirection.UNKNOWN,
        status=ProfileStatus.CONFIRMED,
        evidence_refs=("obs:load-positive-01",),
        profile_version="1.0.0",
        valid_from=valid_from,
        valid_to=valid_to,
    )


class TestPowerSignProfile:
    def test_valid_and_serializable(self) -> None:
        p = _make_grid_confirmed()
        assert p.canonical_field is CanonicalPowerField.FLOW_GRID
        assert p.status is ProfileStatus.CONFIRMED
        dumped = p.model_dump()
        assert dumped["canonical_field"] == "flow_grid_w"
        assert dumped["status"] == "confirmed"

    def test_model_frozen(self) -> None:
        p = _make_grid_confirmed()
        with pytest.raises((ValidationError, TypeError)):
            p.plant_id = "other"

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
                extra_field="bad",
            )

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=datetime(2026, 7, 21, 12, 0, 0),
                valid_to=_VALID_TO,
            )

    def test_valid_to_not_after_valid_from_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_VALID_TO,
                valid_to=_BASE_TS,
            )

    def test_confirmed_without_evidence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=(),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_confirmed_with_unknown_direction_rejected(self) -> None:
        """ADR-009: UNKNOWN direction + CONFIRMED evidence_status is rejected.

        Previously this test asserted the old contract (CONFIRMED profile
        status with positive_means=UNKNOWN was rejected). The new per-
        direction evidence model allows CONFIRMED + UNKNOWN when the
        UNKNOWN direction carries NOT_ASSESSED or PROVISIONAL evidence.
        This test now pins the explicit cross-product rejection.
        """
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.UNKNOWN,
                negative_means=PowerDirection.GRID_EXPORT,
                positive_evidence_status=DirectionEvidenceStatus.CONFIRMED,
                negative_evidence_status=DirectionEvidenceStatus.CONFIRMED,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_unknown_with_known_direction_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.UNKNOWN,
                evidence_refs=(),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_grid_profile_with_battery_directions_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.BATTERY_CHARGE,
                negative_means=PowerDirection.BATTERY_DISCHARGE,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_battery_profile_with_grid_directions_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_BATTERY,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="battery_terminals",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:battery-charge-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_grid_confirmed_equal_directions_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_IMPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_battery_confirmed_equal_directions_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_BATTERY,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="battery_terminals",
                unit="W",
                positive_means=PowerDirection.BATTERY_CHARGE,
                negative_means=PowerDirection.BATTERY_CHARGE,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:battery-charge-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_field_source_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:grid-night-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_fiscal_meter_over_operational_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.FISCAL_METER,
                authority_class=AuthorityClass.FISCAL,
                measurement_point="fiscal_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:fiscal-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_solarman_fiscal_authority_rejected(self) -> None:
        with pytest.raises(ValidationError, match="requires authority_class=operational"):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.FISCAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:solarman-fiscal-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_telemetry_fiscal_authority_rejected(self) -> None:
        with pytest.raises(ValidationError, match="requires authority_class=operational"):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.FISCAL,
                measurement_point="inverter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:telemetry-fiscal-01",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=_VALID_TO,
            )

    def test_operational_authority_accepted_for_solarman(self) -> None:
        p = PowerSignProfile(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="grid_meter",
            unit="W",
            positive_means=PowerDirection.GRID_IMPORT,
            negative_means=PowerDirection.GRID_EXPORT,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("obs:grid-01",),
            profile_version="1.0.0",
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        assert p.authority_class is AuthorityClass.OPERATIONAL

    def test_operational_authority_accepted_for_telemetry(self) -> None:
        p = PowerSignProfile(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="inverter",
            unit="W",
            positive_means=PowerDirection.GRID_IMPORT,
            negative_means=PowerDirection.GRID_EXPORT,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("obs:grid-02",),
            profile_version="1.0.0",
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        assert p.authority_class is AuthorityClass.OPERATIONAL

    def test_confirmed_profile_preserves_operational_authority(self) -> None:
        p = _make_grid_confirmed()
        assert p.authority_class is AuthorityClass.OPERATIONAL


class TestPowerSignProfileRegistry:
    def test_registry_empty_initially(self) -> None:
        reg = PowerSignProfileRegistry()
        assert reg.count == 0
        assert reg.profiles == ()

    def test_production_registry_empty(self) -> None:
        reg = build_production_sign_profile_registry()
        assert reg.count == 0

    def test_register_and_resolve_exact(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed()
        reg.register(p)
        assert reg.count == 1
        resolved = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_BASE_TS,
        )
        assert resolved is p

    def test_resolve_before_valid_from_returns_none(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed()
        reg.register(p)
        before = _BASE_TS - timedelta(hours=1)
        result = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=before,
        )
        assert result is None

    def test_resolve_after_valid_to_returns_none(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed()
        reg.register(p)
        after = _VALID_TO + timedelta(seconds=1)
        result = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=after,
        )
        assert result is None

    def test_adjacent_intervals_allowed(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(valid_from=_BASE_TS, valid_to=_VALID_TO)
        reg.register(p1)
        p2 = _make_grid_confirmed(valid_from=_VALID_TO, valid_to=None)
        reg.register(p2)
        assert reg.count == 2
        assert (
            reg.resolve(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                timestamp=_VALID_TO,
            )
            is p2
        )

    def test_overlapping_intervals_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(valid_from=_BASE_TS, valid_to=_VALID_TO)
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_BASE_TS + timedelta(days=5),
            valid_to=_VALID_TO + timedelta(days=5),
        )
        with pytest.raises(ValueError, match="Overlapping"):
            reg.register(p2)

    def test_duplicate_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed()
        reg.register(p1)
        p2 = _make_grid_confirmed()
        with pytest.raises(ValueError, match="Duplicate"):
            reg.register(p2)

    def test_no_fallback_between_plants(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed(plant_id="casabero")
        reg.register(p)
        result = reg.resolve(
            plant_id="other_plant",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_BASE_TS,
        )
        assert result is None

    def test_no_fallback_between_sources(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed(source=SourceSystem.SOLARMAN_PLANT_FLOW)
        reg.register(p)
        result = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_BASE_TS,
        )
        assert result is None

    def test_resolution_deterministic(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed()
        reg.register(p)
        r1 = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_BASE_TS,
        )
        r2 = reg.resolve(
            plant_id="casabero",
            canonical_field=CanonicalPowerField.FLOW_GRID,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_BASE_TS,
        )
        assert r1 is r2

    def test_naive_timestamp_rejected_in_resolve(self) -> None:
        reg = PowerSignProfileRegistry()
        p = _make_grid_confirmed()
        reg.register(p)
        naive_ts = datetime(2026, 7, 21, 12, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            reg.resolve(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                timestamp=naive_ts,
            )

    def test_open_interval_overlapping_finite_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_BASE_TS + timedelta(days=5),
            valid_to=None,
        )
        with pytest.raises(ValueError, match="Overlapping"):
            reg.register(p2)

    def test_open_interval_adjacent_to_finite_accepted(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_VALID_TO,
            valid_to=None,
        )
        reg.register(p2)

    def test_historical_finite_before_open_accepted(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_BASE_TS - timedelta(days=10),
            valid_to=_BASE_TS - timedelta(days=1),
        )
        reg.register(p2)

    def test_finite_crossing_open_start_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            valid_from=_BASE_TS,
            valid_to=None,
        )
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_BASE_TS - timedelta(days=5),
            valid_to=_BASE_TS + timedelta(days=5),
        )
        with pytest.raises(ValueError, match="Overlapping"):
            reg.register(p2)

    def test_open_versus_open_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            valid_from=_BASE_TS,
            valid_to=None,
        )
        reg.register(p1)
        p2 = _make_grid_confirmed(
            valid_from=_BASE_TS + timedelta(days=1),
            valid_to=None,
        )
        with pytest.raises(ValueError, match="Overlapping"):
            reg.register(p2)

    def test_reverse_registration_order_yields_same_decision(self) -> None:
        reg1 = PowerSignProfileRegistry()
        p1 = _make_grid_confirmed(
            plant_id="plant1",
            valid_from=_BASE_TS,
            valid_to=_VALID_TO,
        )
        p2 = _make_grid_confirmed(
            plant_id="plant1",
            valid_from=_VALID_TO,
            valid_to=None,
        )
        reg1.register(p1)
        reg1.register(p2)

        reg2 = PowerSignProfileRegistry()
        reg2.register(p2)
        reg2.register(p1)

        assert reg1.count == 2
        assert reg2.count == 2


class _NoUtcoffsetTzInfo(tzinfo):
    """Synthetic tzinfo that exists but utcoffset() returns None."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "no-utcoffset"


class TestTimezoneAwareEnforcement:
    def test_valid_from_with_no_utcoffset_tzinfo_rejected(self) -> None:
        tz = _NoUtcoffsetTzInfo()
        with pytest.raises(ValidationError, match="timezone-aware"):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:tz-01",),
                profile_version="1.0.0",
                valid_from=datetime(2026, 7, 21, 12, 0, 0, tzinfo=tz),
                valid_to=_VALID_TO,
            )

    def test_valid_to_with_no_utcoffset_tzinfo_rejected(self) -> None:
        tz = _NoUtcoffsetTzInfo()
        with pytest.raises(ValidationError, match="timezone-aware"):
            PowerSignProfile(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="grid_meter",
                unit="W",
                positive_means=PowerDirection.GRID_IMPORT,
                negative_means=PowerDirection.GRID_EXPORT,
                status=ProfileStatus.CONFIRMED,
                evidence_refs=("obs:tz-02",),
                profile_version="1.0.0",
                valid_from=_BASE_TS,
                valid_to=datetime(2026, 8, 1, 12, 0, 0, tzinfo=tz),
            )

    def test_resolve_with_no_utcoffset_tzinfo_rejected(self) -> None:
        reg = PowerSignProfileRegistry()
        reg.register(_make_grid_confirmed())
        tz = _NoUtcoffsetTzInfo()
        with pytest.raises(ValueError, match="timezone-aware"):
            reg.resolve(
                plant_id="casabero",
                canonical_field=CanonicalPowerField.FLOW_GRID,
                source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
                timestamp=datetime(2026, 7, 21, 12, 0, 0, tzinfo=tz),
            )
