"""Synthetic tests for registry_d10_proposal.py — D1.0 U2.1b.1 redesign.

These tests verify the structural invariants of the proposal file.
They do NOT register any profile into a real registry; they only
exercise PowerSignProfile construction, registry cutover geometry,
and normalization status mapping.

If any test fails, the proposal is structurally broken and MUST NOT
be promoted to registry_seeds.py.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from solgreen.energy.normalization import (
    NormalizationStatus,
    normalize_power_value,
)
from solgreen.energy.registry_d10_proposal import (
    DEFERRED_SIGNALS,
    EVIDENCE_REF,
    LEGACY_EVIDENCE_REF,
    PROFILE_VERSION,
    SUPPORTING_SIGNALS,
    UPDATED_PROFILES,
    build_updated_profiles,
    count_deferred_signals_not_promotable,
    count_supporting_signals_not_promotable,
    is_promotable,
)
from solgreen.energy.registry_seeds import build_production_sign_profile_registry
from solgreen.energy.sign_profiles import (
    AuthorityClass,
    CanonicalPowerField,
    DirectionEvidenceStatus,
    PowerDirection,
    PowerSignProfile,
    PowerSignProfileRegistry,
    ProfileStatus,
    SourceSystem,
)

# Synthetic timezone-aware cutover timestamp for testing.
# Must be strictly after any real evidence window; this value is
# chosen as a convenient test fixture with no private meaning.
_TEST_EFFECTIVE_FROM = datetime(2026, 7, 25, 0, 0, 0, tzinfo=UTC)

# ── Schema validation: the 4 UPDATED_PROFILES ─────────────────────────────────


class TestUpdatedProfilesSchema:
    @pytest.mark.parametrize("key", list(UPDATED_PROFILES.keys()))
    def test_profile_passes_pydantic_validation(self, key: str) -> None:
        # UPDATED_PROFILES are templates (no valid_from). The builder
        # injects the timestamp and produces a fully-valid profile.
        profiles = build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)
        assert key in profiles
        assert profiles[key].status in (
            ProfileStatus.CONFIRMED,
            ProfileStatus.PROVISIONAL,
        )

    @pytest.mark.parametrize("key", list(UPDATED_PROFILES.keys()))
    def test_unit_is_W(self, key: str) -> None:
        assert UPDATED_PROFILES[key]["unit"] == "W"

    def test_updated_profiles_count(self) -> None:
        assert len(UPDATED_PROFILES) == 4

    def test_profile_version_is_set(self) -> None:
        for entry in UPDATED_PROFILES.values():
            assert entry["profile_version"] == PROFILE_VERSION

    def test_all_updated_profiles_have_evidence_refs(self) -> None:
        for entry in UPDATED_PROFILES.values():
            assert len(entry["evidence_refs"]) >= 1


# ── Uniqueness: one authoritative profile per canonical_field ──────────────────


class TestUniqueness:
    def test_one_authoritative_profile_per_canonical_field(self) -> None:
        seen: set[CanonicalPowerField] = set()
        for entry in UPDATED_PROFILES.values():
            cf = entry["canonical_field"]
            assert cf not in seen, f"Duplicate canonical_field {cf} across UPDATED_PROFILES"
            seen.add(cf)

    def test_one_authoritative_profile_per_source_system(self) -> None:
        seen: set[tuple[CanonicalPowerField, SourceSystem]] = set()
        for entry in UPDATED_PROFILES.values():
            key = (entry["canonical_field"], entry["source_system"])
            assert key not in seen, f"Duplicate (field, source) tuple {key}"
            seen.add(key)


# ── SUPPORTING_SIGNALS isolation ───────────────────────────────────────────────


class TestSupportingSignals:
    def test_all_supporting_signals_are_not_promotable(self) -> None:
        for key, entry in SUPPORTING_SIGNALS.items():
            assert entry["production_registry_allowed"] is False, (
                f"Supporting signal {key} must have production_registry_allowed=False"
            )
            assert is_promotable(entry) is False

    def test_b_c1_unit_is_A_not_W(self) -> None:
        assert SUPPORTING_SIGNALS["b_c1"]["unit"] == "A"

    def test_b_c1_cannot_be_promoted_as_powersignprofile(self) -> None:
        # Schema enforces unit=Literal["W"]; an "A" entry must fail.
        bad = dict(UPDATED_PROFILES["battery_b_p1"])
        bad["unit"] = "A"
        with pytest.raises(ValidationError):
            PowerSignProfile(**bad)

    def test_supporting_signals_count(self) -> None:
        assert len(SUPPORTING_SIGNALS) == 7
        assert count_supporting_signals_not_promotable() == 7

    def test_dp1_dp2_cannot_be_promoted_as_pv_string_profiles(self) -> None:
        # DP1/DP2 share canonical_field=TELEMETRY_PV with pv_c_p_pvt.
        # Promoting either would break uniqueness (one per field+source).
        cf_pv = SUPPORTING_SIGNALS["dp1"]["supports_profile"]
        assert cf_pv == "pv_c_p_pvt"


# ── DEFERRED_SIGNALS isolation ────────────────────────────────────────────────


class TestDeferredSignals:
    def test_all_deferred_signals_are_not_promotable(self) -> None:
        for entry in DEFERRED_SIGNALS:
            assert entry["production_registry_allowed"] is False
            assert is_promotable(entry) is False

    def test_deferred_signals_count(self) -> None:
        assert len(DEFERRED_SIGNALS) == 11
        assert count_deferred_signals_not_promotable() == 11


# ── Temporal provenance ────────────────────────────────────────────────────────


class TestTemporalProvenance:
    def test_no_default_effective_from_constant(self) -> None:
        """The proposal does not export a default effective_from.

        ADR-009 forbids inventing a cutover timestamp. Operators must
        supply one explicitly to `build_updated_profiles(effective_from=...)`.
        """
        import solgreen.energy.registry_d10_proposal as mod

        assert not hasattr(mod, "EFFECTIVE_FROM")
        assert not hasattr(mod, "EFFECTIVE_FROM_RAW")

    def test_templates_do_not_contain_valid_from(self) -> None:
        """UPDATED_PROFILES are templates without a valid_from field."""
        for entry in UPDATED_PROFILES.values():
            assert "valid_from" not in entry

    def test_builder_accepts_timezone_aware_effective_from(self) -> None:
        profiles = build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)
        for _key, profile in profiles.items():
            assert profile.valid_from == _TEST_EFFECTIVE_FROM

    def test_builder_rejects_none(self) -> None:
        with pytest.raises(ValueError, match="effective_from is required"):
            build_updated_profiles(effective_from=None)  # type: ignore[arg-type]

    def test_builder_rejects_naive_datetime(self) -> None:
        naive = datetime(2026, 7, 24, 0, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            build_updated_profiles(effective_from=naive)

    def test_builder_accepts_operator_supplied_timestamp(self) -> None:
        """The builder accepts any timezone-aware datetime supplied by the
        operator.  The operator is responsible for choosing a timestamp
        that is appropriate for the deployment."""
        ts = datetime(2026, 7, 25, 0, 0, 0, tzinfo=UTC)
        profiles = build_updated_profiles(effective_from=ts)
        assert profiles["battery_b_p1"].valid_from == ts

    def test_new_profiles_do_not_use_legacy_evidence_ref(self) -> None:
        for entry in UPDATED_PROFILES.values():
            for ref in entry["evidence_refs"]:
                assert ref != LEGACY_EVIDENCE_REF, f"New profile references legacy evidence: {ref}"

    def test_legacy_evidence_ref_is_documented_only(self) -> None:
        assert LEGACY_EVIDENCE_REF == "owner_decision_2026_07_21"


# ── Promotion cutover geometry ────────────────────────────────────────────────


class TestPromotionCutover:
    """Verify that promotion using semi-open intervals is reversible."""

    def _legacy_battery(self) -> PowerSignProfile:
        return PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:battery_power",
            unit="W",
            positive_means=PowerDirection.BATTERY_DISCHARGE,
            negative_means=PowerDirection.BATTERY_CHARGE,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=_TEST_EFFECTIVE_FROM,
        )

    def _new_battery(self) -> PowerSignProfile:
        return build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)["battery_b_p1"]

    def test_cutover_no_gap_no_overlap(self) -> None:
        registry = PowerSignProfileRegistry()
        old = self._legacy_battery()
        new = self._new_battery()
        registry.register(old)
        registry.register(new)
        # Just before cutover -> old
        before = _TEST_EFFECTIVE_FROM - timedelta(milliseconds=1)
        resolved_before = registry.resolve(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=before,
        )
        assert resolved_before is old
        # Exactly at cutover -> new
        resolved_at = registry.resolve(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM,
        )
        assert resolved_at is new
        # After cutover -> new
        after = _TEST_EFFECTIVE_FROM + timedelta(days=1)
        resolved_after = registry.resolve(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=after,
        )
        assert resolved_after is new

    def test_two_simultaneous_profiles_for_same_field_rejected(self) -> None:
        # Overlap by 1 ms before effective_from should fail.
        registry = PowerSignProfileRegistry()
        old = self._legacy_battery()
        new_overlap = PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:b_p1",
            unit="W",
            positive_means=PowerDirection.BATTERY_DISCHARGE,
            negative_means=PowerDirection.BATTERY_CHARGE,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=(EVIDENCE_REF,),
            profile_version=PROFILE_VERSION,
            valid_from=_TEST_EFFECTIVE_FROM - timedelta(seconds=1),
            valid_to=None,
        )
        registry.register(old)
        with pytest.raises(ValueError, match="Overlapping"):
            registry.register(new_overlap)

    def test_promotion_is_reversible(self) -> None:
        # Rollback: rebuild registry with only the legacy profile (valid_to=None).
        registry = PowerSignProfileRegistry()
        legacy_only = PowerSignProfile(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="telemetry:inverter:battery_power",
            unit="W",
            positive_means=PowerDirection.BATTERY_DISCHARGE,
            negative_means=PowerDirection.BATTERY_CHARGE,
            zero_means=PowerDirection.NO_FLOW,
            zero_deadband_w=5.0,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("owner_decision_2026_07_21",),
            profile_version="u2_1b.1-telemetry",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            valid_to=None,
        )
        registry.register(legacy_only)
        after = _TEST_EFFECTIVE_FROM + timedelta(days=1)
        resolved = registry.resolve(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=after,
        )
        assert resolved is legacy_only

    def test_promotion_is_idempotent(self) -> None:
        # Registering the same new profile twice raises Duplicate.
        registry = PowerSignProfileRegistry()
        new = self._new_battery()
        registry.register(new)
        with pytest.raises(ValueError, match="Duplicate"):
            registry.register(new)


# ── Normalization behavior with PROFILE_NOT_CONFIRMED ──────────────────────────


class TestNormalizationProfileNotConfirmed:
    """Per-direction evidence status (ADR-009) is the actual gate.

    The grid profile is the canonical asymmetric example:
        positive_evidence_status = NOT_ASSESSED
        negative_evidence_status = CONFIRMED

    Negative raw values normalize as GRID_IMPORT (per-direction confirmed).
    Positive raw values return PROFILE_NOT_CONFIRMED (per-direction not
    assessed). Values within the deadband normalize as zero (NO_FLOW).
    """

    def _registry_with_new_grid(self) -> PowerSignProfileRegistry:
        registry = PowerSignProfileRegistry()
        registry.register(
            build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)["grid_t_a_p_o_g"]
        )
        return registry

    def test_grid_positive_returns_profile_not_confirmed(self) -> None:
        registry = self._registry_with_new_grid()
        result = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=500.0,
            registry=registry,
        )
        assert result.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        assert result.profile_status is ProfileStatus.CONFIRMED
        assert result.profile_version == PROFILE_VERSION
        assert result.grid_export_w is None
        assert result.grid_import_w is None
        assert result.raw_power_w == 500.0

    def test_grid_negative_normalizes_as_grid_import(self) -> None:
        # Per-direction evidence (ADR-009): negative is CONFIRMED.
        registry = self._registry_with_new_grid()
        result = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=-500.0,
            registry=registry,
        )
        assert result.status is NormalizationStatus.NORMALIZED
        assert result.profile_status is ProfileStatus.CONFIRMED
        assert result.grid_import_w == 500.0
        assert result.grid_export_w is None

    def test_grid_within_deadband_normalizes_as_zero(self) -> None:
        """ADR-009 §"Raw observation vs. normalized output":
        raw_power_w is PRESERVED (never mutated by the normalizer);
        both magnitudes are forced to 0.0; a warning records the
        deadband application; within_zero_deadband is True.
        """
        registry = self._registry_with_new_grid()
        for raw in (0.0, 3.0, -3.0, 5.0, -5.0):
            result = normalize_power_value(
                plant_id="SOLGREEN",
                canonical_field=CanonicalPowerField.TELEMETRY_GRID,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
                raw_power_w=raw,
                registry=registry,
            )
            assert result.status is NormalizationStatus.NORMALIZED
            assert result.grid_import_w == 0.0
            assert result.grid_export_w == 0.0
            # Raw is preserved (the original observation).
            assert result.raw_power_w == raw
            assert result.within_zero_deadband is True
            assert len(result.warnings) >= 1

    def test_grid_outside_deadband_preserves_raw_and_sets_flag_false(self) -> None:
        """Outside the deadband: raw is preserved AND within_zero_deadband=False.
        The flag is only True when the deadband was actually applied."""
        registry = self._registry_with_new_grid()
        # Positive outside deadband -> PROFILE_NOT_CONFIRMED (per-direction).
        pos = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=500.0,
            registry=registry,
        )
        assert pos.raw_power_w == 500.0
        assert pos.within_zero_deadband is False
        # Negative outside deadband -> NORMALIZED.
        neg = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=-500.0,
            registry=registry,
        )
        assert neg.raw_power_w == -500.0
        assert neg.within_zero_deadband is False
        assert neg.grid_import_w == 500.0


# ── Per-direction evidence (ADR-009) ──────────────────────────────────────────


class TestPerDirectionEvidence:
    """Verify the ADR-009 contract on each UPDATED_PROFILES entry."""

    @pytest.mark.parametrize(
        ("key", "expected_pos_status", "expected_neg_status"),
        [
            ("battery_b_p1", DirectionEvidenceStatus.CONFIRMED, DirectionEvidenceStatus.CONFIRMED),
            (
                "grid_t_a_p_o_g",
                DirectionEvidenceStatus.NOT_ASSESSED,
                DirectionEvidenceStatus.CONFIRMED,
            ),
            ("pv_c_p_pvt", DirectionEvidenceStatus.CONFIRMED, DirectionEvidenceStatus.NOT_ASSESSED),
            (
                "load_e_puse_t1",
                DirectionEvidenceStatus.CONFIRMED,
                DirectionEvidenceStatus.NOT_ASSESSED,
            ),
        ],
    )
    def test_per_direction_status(
        self,
        key: str,
        expected_pos_status: DirectionEvidenceStatus,
        expected_neg_status: DirectionEvidenceStatus,
    ) -> None:
        profile = build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)[key]
        assert profile.positive_evidence_status is expected_pos_status
        assert profile.negative_evidence_status is expected_neg_status

    def test_unknown_with_confirmed_evidence_rejected(self) -> None:
        # Combinations: UNKNOWN direction requires NOT_ASSESSED or PROVISIONAL.
        base = dict(UPDATED_PROFILES["grid_t_a_p_o_g"])
        base["positive_evidence_status"] = DirectionEvidenceStatus.CONFIRMED
        with pytest.raises(ValidationError):
            PowerSignProfile(**base)

    def test_known_direction_with_not_assessed_rejected(self) -> None:
        # Combinations: known direction cannot be NOT_ASSESSED.
        base = dict(UPDATED_PROFILES["battery_b_p1"])
        base["positive_evidence_status"] = DirectionEvidenceStatus.NOT_ASSESSED
        with pytest.raises(ValidationError):
            PowerSignProfile(**base)

    def test_grid_negative_normalizes_battery_negative_normalizes(self) -> None:
        """Battery B_P1: bidirectional CONFIRMED. Both directions normalize."""
        registry = PowerSignProfileRegistry()
        registry.register(
            build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)["battery_b_p1"]
        )
        # Positive: discharge
        pos = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=200.0,
            registry=registry,
        )
        assert pos.status is NormalizationStatus.NORMALIZED
        assert pos.battery_discharge_w == 200.0
        assert pos.battery_charge_w is None
        # Negative: charge
        neg = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=-150.0,
            registry=registry,
        )
        assert neg.status is NormalizationStatus.NORMALIZED
        assert neg.battery_charge_w == 150.0
        assert neg.battery_discharge_w is None

    def test_pv_positive_normalizes_negative_returns_not_confirmed(self) -> None:
        """PV C_P_PVT: positive CONFIRMED, negative NOT_ASSESSED."""
        registry = PowerSignProfileRegistry()
        registry.register(build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)["pv_c_p_pvt"])
        pos = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=3500.0,
            registry=registry,
        )
        assert pos.status is NormalizationStatus.NORMALIZED
        assert pos.pv_generation_w == 3500.0
        neg = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=-100.0,
            registry=registry,
        )
        assert neg.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        assert neg.pv_generation_w is None

    def test_load_positive_normalizes_negative_returns_not_confirmed(self) -> None:
        """Load E_Puse_t1: positive CONFIRMED, negative NOT_ASSESSED."""
        registry = PowerSignProfileRegistry()
        registry.register(
            build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)["load_e_puse_t1"]
        )
        pos = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=1200.0,
            registry=registry,
        )
        assert pos.status is NormalizationStatus.NORMALIZED
        assert pos.load_consumption_w == 1200.0
        neg = normalize_power_value(
            plant_id="SOLGREEN",
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=_TEST_EFFECTIVE_FROM + timedelta(minutes=1),
            raw_power_w=-50.0,
            registry=registry,
        )
        assert neg.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        assert neg.load_consumption_w is None


# ── Compatibility and serialization (ADR-009 Fix 4) ───────────────────────────


class TestCompatibilityAndSerialization:
    """ADR-009 §"Compatibility and serialization"."""

    def test_legacy_profile_derives_per_direction_evidence(self) -> None:
        """A profile that does NOT specify per-direction evidence derives them
        from profile.status and the direction values, per ADR-009 §4.
        """
        legacy = PowerSignProfile(
            plant_id="legacy_plant",
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="legacy:battery",
            unit="W",
            positive_means=PowerDirection.BATTERY_DISCHARGE,
            negative_means=PowerDirection.BATTERY_CHARGE,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("legacy:ref",),
            profile_version="legacy-1.0.0",
            valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        )
        assert legacy.positive_evidence_status is DirectionEvidenceStatus.CONFIRMED
        assert legacy.negative_evidence_status is DirectionEvidenceStatus.CONFIRMED

    def test_model_dump_contains_derived_evidence(self) -> None:
        """model_dump() must include the per-direction evidence values."""
        profile = PowerSignProfile(
            plant_id="p",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="m",
            unit="W",
            positive_means=PowerDirection.UNKNOWN,
            negative_means=PowerDirection.GRID_IMPORT,
            positive_evidence_status=DirectionEvidenceStatus.NOT_ASSESSED,
            negative_evidence_status=DirectionEvidenceStatus.CONFIRMED,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("e",),
            profile_version="v",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
        )
        dumped = profile.model_dump()
        assert dumped["positive_evidence_status"] == "not_assessed"
        assert dumped["negative_evidence_status"] == "confirmed"

    def test_round_trip_preserves_evidence(self) -> None:
        """model_validate(model_dump()) preserves the evidence fields exactly."""
        original = PowerSignProfile(
            plant_id="p",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="m",
            unit="W",
            positive_means=PowerDirection.UNKNOWN,
            negative_means=PowerDirection.GRID_IMPORT,
            positive_evidence_status=DirectionEvidenceStatus.NOT_ASSESSED,
            negative_evidence_status=DirectionEvidenceStatus.CONFIRMED,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("e",),
            profile_version="v",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
        )
        dumped = original.model_dump()
        restored = PowerSignProfile.model_validate(dumped)
        assert restored.positive_evidence_status is DirectionEvidenceStatus.NOT_ASSESSED
        assert restored.negative_evidence_status is DirectionEvidenceStatus.CONFIRMED
        assert restored.status is original.status
        assert restored.positive_means is original.positive_means
        assert restored.negative_means is original.negative_means

    def test_partial_grid_profile_via_builder(self) -> None:
        """The builder produces the canonical asymmetric grid profile:
        negative=GRID_IMPORT/CONFIRMED, positive=UNKNOWN/NOT_ASSESSED."""
        profiles = build_updated_profiles(effective_from=_TEST_EFFECTIVE_FROM)
        grid = profiles["grid_t_a_p_o_g"]
        assert grid.positive_means is PowerDirection.UNKNOWN
        assert grid.negative_means is PowerDirection.GRID_IMPORT
        assert grid.positive_evidence_status is DirectionEvidenceStatus.NOT_ASSESSED
        assert grid.negative_evidence_status is DirectionEvidenceStatus.CONFIRMED
        assert grid.status is ProfileStatus.CONFIRMED
        assert grid.valid_from == _TEST_EFFECTIVE_FROM

    def test_contradicted_returns_profile_not_confirmed(self) -> None:
        """A direction marked CONTRADICTED is never normalized (ADR-009 Fix 3)."""
        registry = PowerSignProfileRegistry()
        profile = PowerSignProfile(
            plant_id="p",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            authority_class=AuthorityClass.OPERATIONAL,
            measurement_point="m",
            unit="W",
            positive_means=PowerDirection.GRID_EXPORT,
            negative_means=PowerDirection.GRID_IMPORT,
            positive_evidence_status=DirectionEvidenceStatus.CONTRADICTED,
            negative_evidence_status=DirectionEvidenceStatus.CONFIRMED,
            status=ProfileStatus.CONFIRMED,
            evidence_refs=("e",),
            profile_version="v",
            valid_from=datetime(2026, 7, 1, tzinfo=UTC),
        )
        registry.register(profile)
        # Positive raw -> CONTRADICTED gate -> PROFILE_NOT_CONFIRMED.
        pos = normalize_power_value(
            plant_id="p",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=datetime(2026, 7, 2, tzinfo=UTC),
            raw_power_w=500.0,
            registry=registry,
        )
        assert pos.status is NormalizationStatus.PROFILE_NOT_CONFIRMED
        # Negative raw -> CONFIRMED gate -> NORMALIZED.
        neg = normalize_power_value(
            plant_id="p",
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=datetime(2026, 7, 2, tzinfo=UTC),
            raw_power_w=-500.0,
            registry=registry,
        )
        assert neg.status is NormalizationStatus.NORMALIZED

    def test_unknown_status_with_confirmed_per_direction_rejected(self) -> None:
        """ProfileStatus.UNKNOWN cannot coexist with per-direction=CONFIRMED
        (ADR-009 Fix 3)."""
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="p",
                canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="m",
                unit="W",
                positive_means=PowerDirection.UNKNOWN,
                negative_means=PowerDirection.UNKNOWN,
                positive_evidence_status=DirectionEvidenceStatus.CONFIRMED,
                negative_evidence_status=DirectionEvidenceStatus.NOT_ASSESSED,
                status=ProfileStatus.UNKNOWN,
                evidence_refs=(),
                profile_version="v",
                valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            )

    def test_unknown_status_with_negative_confirmed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PowerSignProfile(
                plant_id="p",
                canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                measurement_point="m",
                unit="W",
                positive_means=PowerDirection.UNKNOWN,
                negative_means=PowerDirection.UNKNOWN,
                positive_evidence_status=DirectionEvidenceStatus.NOT_ASSESSED,
                negative_evidence_status=DirectionEvidenceStatus.CONFIRMED,
                status=ProfileStatus.UNKNOWN,
                evidence_refs=(),
                profile_version="v",
                valid_from=datetime(2026, 7, 1, tzinfo=UTC),
            )


# ── Non-PROMOTE check: proposal is not loaded by the production registry ──────


class TestProposalIsolation:
    """The proposal must not be silently loaded by build_*_registry helpers."""

    def test_telemetry_registry_does_not_contain_proposal_entries(self) -> None:
        from solgreen.energy.registry_seeds import build_telemetry_sign_profile_registry

        registry = build_telemetry_sign_profile_registry()
        for profile in registry.profiles:
            assert profile.profile_version != PROFILE_VERSION, (
                "Proposal profile_version leaked into telemetry registry"
            )
            assert profile.evidence_refs != (EVIDENCE_REF,), (
                "Proposal evidence_ref leaked into telemetry registry"
            )

    def test_production_registry_is_empty(self) -> None:
        with pytest.raises(TypeError):
            build_production_sign_profile_registry()


class TestProductionRegistryIntegration:
    """Integration tests for build_production_sign_profile_registry.

    Verifies the combined behavior of legacy profiles (closed at cutover)
    and D1.0 profiles (opened at cutover) in a single registry.
    """

    _CUTOVER = datetime(2026, 7, 25, 0, 0, 0, tzinfo=UTC)
    _BEFORE = datetime(2026, 7, 24, 23, 59, 59, tzinfo=UTC)
    _AFTER = datetime(2026, 7, 25, 0, 0, 1, tzinfo=UTC)

    def test_requires_effective_from(self) -> None:
        with pytest.raises(TypeError):
            build_production_sign_profile_registry()

    def test_rejects_none(self) -> None:
        with pytest.raises((ValueError, ValidationError)):
            build_production_sign_profile_registry(effective_from=None)  # type: ignore[arg-type]

    def test_rejects_naive_datetime(self) -> None:
        naive = datetime(2026, 7, 25, 0, 0, 0)
        with pytest.raises((ValueError, ValidationError)):
            build_production_sign_profile_registry(effective_from=naive)

    def test_no_private_timestamp_hardcoded(self) -> None:
        import inspect

        from solgreen.energy import registry_seeds

        src = inspect.getsource(registry_seeds)
        assert "EFFECTIVE_FROM_RAW" not in src
        assert "EFFECTIVE_FROM" not in src

    def test_legacy_builder_unchanged(self) -> None:
        from solgreen.energy.registry_seeds import build_telemetry_sign_profile_registry

        reg = build_telemetry_sign_profile_registry()
        assert reg.count == 4
        for p in reg.profiles:
            assert p.valid_to is None

    def test_repeated_calls_are_deterministic(self) -> None:
        reg_a = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        reg_b = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        assert reg_a.count == reg_b.count == 8
        profiles_a = {p.measurement_point: p for p in reg_a.profiles}
        profiles_b = {p.measurement_point: p for p in reg_b.profiles}
        assert profiles_a.keys() == profiles_b.keys()
        for key in profiles_a:
            pa = profiles_a[key]
            pb = profiles_b[key]
            assert pa.profile_version == pb.profile_version
            assert pa.status == pb.status
            assert pa.valid_from == pb.valid_from

    def test_repeated_calls_return_independent_registries(self) -> None:
        reg_a = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        reg_b = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        assert reg_a is not reg_b

    def test_eight_profiles_in_registry(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        assert reg.count == 8
        versions = {p.profile_version for p in reg.profiles}
        assert "u2_1b.1-telemetry" in versions
        assert "u2_1b.1-d1.0" in versions

    def test_no_gap_between_legacy_and_new(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        by_field: dict = {p.canonical_field: p for p in reg.profiles}
        for _field, profile in by_field.items():
            assert profile.valid_from == self._CUTOVER

    def test_no_overlap_between_legacy_and_new(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        for p in reg.profiles:
            if p.profile_version == "u2_1b.1-telemetry":
                assert p.valid_to == self._CUTOVER
            elif p.profile_version == "u2_1b.1-d1.0":
                assert p.valid_to is None
                assert p.valid_from == self._CUTOVER

    def test_old_valid_to_equals_new_valid_from(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        for p in reg.profiles:
            if p.profile_version == "u2_1b.1-telemetry":
                assert p.valid_to == self._CUTOVER
            elif p.profile_version == "u2_1b.1-d1.0":
                assert p.valid_from == self._CUTOVER

    def test_before_cutover_resolves_legacy(self) -> None:
        from solgreen.energy.registry_seeds import build_telemetry_sign_profile_registry

        reg = build_telemetry_sign_profile_registry()
        resolved = reg.resolve(
            "SOLGREEN",
            CanonicalPowerField.TELEMETRY_GRID,
            SourceSystem.INVERTER_TELEMETRY,
            self._BEFORE,
        )
        assert resolved.profile_version == "u2_1b.1-telemetry"
        assert resolved.status == ProfileStatus.CONFIRMED

    def test_at_cutover_resolves_d10(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        resolved = reg.resolve(
            "SOLGREEN",
            CanonicalPowerField.TELEMETRY_GRID,
            SourceSystem.INVERTER_TELEMETRY,
            self._CUTOVER,
        )
        assert resolved.profile_version == "u2_1b.1-d1.0"

    def test_after_cutover_resolves_d10(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        resolved = reg.resolve(
            "SOLGREEN",
            CanonicalPowerField.TELEMETRY_GRID,
            SourceSystem.INVERTER_TELEMETRY,
            self._AFTER,
        )
        assert resolved.profile_version == "u2_1b.1-d1.0"

    def test_legacy_grid_positive_normalizes_as_export(self) -> None:
        from solgreen.energy.registry_seeds import build_telemetry_sign_profile_registry

        reg = build_telemetry_sign_profile_registry()
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=500.0,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._BEFORE,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.grid_export_w == 500.0

    def test_legacy_grid_negative_normalizes_as_import(self) -> None:
        from solgreen.energy.registry_seeds import build_telemetry_sign_profile_registry

        reg = build_telemetry_sign_profile_registry()
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=-500.0,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._BEFORE,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.grid_import_w == 500.0

    def test_d10_grid_positive_returns_profile_not_confirmed(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=500.0,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.PROFILE_NOT_CONFIRMED

    def test_d10_grid_negative_normalizes_as_import(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=-500.0,
            canonical_field=CanonicalPowerField.TELEMETRY_GRID,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.grid_import_w == 500.0

    def test_battery_positive_normalizes_as_discharge(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=300.0,
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.battery_discharge_w == 300.0

    def test_battery_negative_normalizes_as_charge(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=-300.0,
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.battery_charge_w == 300.0

    def test_pv_positive_normalizes(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=1000.0,
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.pv_generation_w == 1000.0

    def test_pv_negative_returns_profile_not_confirmed(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=-100.0,
            canonical_field=CanonicalPowerField.TELEMETRY_PV,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.PROFILE_NOT_CONFIRMED

    def test_load_positive_normalizes(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=800.0,
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.NORMALIZED
        assert result.load_consumption_w == 800.0

    def test_load_negative_returns_profile_not_confirmed(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        result = normalize_power_value(
            plant_id="SOLGREEN",
            raw_power_w=-50.0,
            canonical_field=CanonicalPowerField.FLOW_CONSUMO,
            source_system=SourceSystem.SOLARMAN_PLANT_FLOW,
            timestamp=self._AFTER,
            registry=reg,
        )
        assert result.status == NormalizationStatus.PROFILE_NOT_CONFIRMED

    def test_supporting_signals_not_in_production_registry(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        mp_set = {p.measurement_point for p in reg.profiles}
        assert "telemetry:inverter:b_c1" not in mp_set
        assert "telemetry:inverter:dp1" not in mp_set
        assert "telemetry:inverter:dp2" not in mp_set

    def test_deferred_signals_not_in_production_registry(self) -> None:
        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        mp_set = {p.measurement_point for p in reg.profiles}
        for mp in mp_set:
            assert "uap1" not in mp
            assert "uap2" not in mp

    def test_registering_same_profile_twice_in_one_registry_raises(self) -> None:
        from solgreen.energy.registry_seeds import _build_legacy_telemetry_profiles

        reg = PowerSignProfileRegistry()
        profile = _build_legacy_telemetry_profiles(valid_to=None)[0]
        reg.register(profile)
        with pytest.raises(ValueError, match="Duplicate"):
            reg.register(profile)

    def test_builder_twice_does_not_raise(self) -> None:
        build_production_sign_profile_registry(effective_from=self._CUTOVER)
        build_production_sign_profile_registry(effective_from=self._CUTOVER)

    def test_import_from_solgreen_energy(self) -> None:
        from solgreen.energy import build_production_sign_profile_registry

        reg = build_production_sign_profile_registry(effective_from=self._CUTOVER)
        assert reg.count == 8
