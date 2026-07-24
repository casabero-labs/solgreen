from __future__ import annotations

from datetime import UTC, datetime

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.energy.normalization import NormalizationStatus
from solgreen.importer.normalize import (
    build_normalization_context,
    normalize_telemetry_signals,
)


def _sample(
    timestamp_utc: datetime,
    battery: float | None = None,
    grid: float | None = None,
    pv: float | None = None,
) -> InverterTelemetrySample:
    signals: dict[str, float] = {}
    if battery is not None:
        signals["potencia_de_bateria_w"] = battery
    if grid is not None:
        signals["total_active_power_of_the_grid_w"] = grid
    if pv is not None:
        signals["pv_total_charging_power_w"] = pv

    return InverterTelemetrySample(
        timestamp_original=timestamp_utc,
        timestamp_utc=timestamp_utc,
        signals=signals,
    )


class TestPipelineBattery:
    def test_battery_positive_discharge_legacy(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "potencia_de_bateria_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.battery_discharge_w == 1200.0
        assert r.normalization.battery_charge_w is None

    def test_battery_negative_charge_legacy(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=-800.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "potencia_de_bateria_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.battery_charge_w == 800.0
        assert r.normalization.battery_discharge_w is None


class TestPipelineGrid:
    def test_legacy_grid_negative_import(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), grid=-500.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "total_active_power_of_the_grid_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.grid_import_w == 500.0

    def test_legacy_grid_positive_export(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), grid=300.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "total_active_power_of_the_grid_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.grid_export_w == 300.0

    def test_d10_grid_negative_is_normalized_import(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        samples = [_sample(datetime(2026, 8, 2, 10, 0, tzinfo=UTC), grid=-500.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "total_active_power_of_the_grid_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.grid_import_w == 500.0

    def test_d10_grid_positive_is_not_confirmed(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        samples = [_sample(datetime(2026, 8, 2, 10, 0, tzinfo=UTC), grid=300.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.not_confirmed_count == 1
        r = next(r for r in results if r.raw_signal_name == "total_active_power_of_the_grid_w")
        assert r.normalization.status == NormalizationStatus.PROFILE_NOT_CONFIRMED


class TestPipelinePV:
    def test_pv_positive_generation_legacy(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 12, 0, tzinfo=UTC), pv=3500.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        r = next(r for r in results if r.raw_signal_name == "pv_total_charging_power_w")
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.pv_generation_w == 3500.0

    def test_pv_negative_not_confirmed_legacy(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 12, 0, tzinfo=UTC), pv=-100.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.not_confirmed_count == 1
        r = next(r for r in results if r.raw_signal_name == "pv_total_charging_power_w")
        assert r.normalization.status == NormalizationStatus.PROFILE_NOT_CONFIRMED


class TestPipelineMixed:
    def test_mixed_samples_before_and_after_cutover(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        before = _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)
        after = _sample(datetime(2026, 8, 2, 10, 0, tzinfo=UTC), battery=1200.0)
        results, _summary = normalize_telemetry_signals([before, after], ctx)

        assert results[0].timestamp_utc == before.timestamp_utc
        assert results[1].timestamp_utc == after.timestamp_utc
        assert results[0].normalization.status == NormalizationStatus.NORMALIZED
        assert results[1].normalization.status == NormalizationStatus.NORMALIZED

    def test_each_sample_uses_own_timestamp(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        s1 = _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=100.0)
        s2 = _sample(datetime(2026, 7, 21, 10, 5, tzinfo=UTC), battery=200.0)
        results, _summary = normalize_telemetry_signals([s1, s2], ctx)

        assert results[0].timestamp_utc == s1.timestamp_utc
        assert results[1].timestamp_utc == s2.timestamp_utc


class TestPipelineDeadband:
    def test_deadband_produces_normalized_with_warning(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=3.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        assert summary.warning_count == 1
        r = results[0]
        assert r.normalization.status == NormalizationStatus.NORMALIZED
        assert r.normalization.within_zero_deadband is True
        assert len(r.normalization.warnings) > 0

    def test_deadband_preserves_raw_power_w(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=3.0)]
        results, _ = normalize_telemetry_signals(samples, ctx)

        assert results[0].normalization.raw_power_w == 3.0


class TestPipelineMissing:
    def test_missing_values_increment_missing_count(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=None)]
        _results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.missing_count == 3
        assert summary.result_count == 0
        assert len(_results) == 0

    def test_partial_signals_mixed_missing(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(
                datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
                battery=100.0,
                grid=None,
                pv=500.0,
            )
        ]
        _results, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.missing_count == 1
        assert summary.result_count == 2
        assert summary.normalized_count == 2


class TestPipelineSummaryInvariants:
    def test_summary_invariants_hold(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(
                datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
                battery=1200.0,
                grid=-500.0,
                pv=3500.0,
            ),
            _sample(
                datetime(2026, 7, 21, 10, 5, tzinfo=UTC),
                battery=None,
                grid=300.0,
                pv=-100.0,
            ),
        ]
        _, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.eligible_count == 6
        total = (
            summary.missing_count
            + summary.normalized_count
            + summary.not_confirmed_count
            + summary.not_found_count
            + summary.error_count
        )
        assert summary.eligible_count == total
        assert summary.result_count == summary.eligible_count - summary.missing_count
        assert summary.warning_count <= summary.result_count

    def test_eligible_count_matches_samples_times_bindings(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=100.0),
            _sample(datetime(2026, 7, 21, 10, 5, tzinfo=UTC), battery=200.0),
            _sample(datetime(2026, 7, 21, 10, 10, tzinfo=UTC), battery=300.0),
        ]
        _, summary = normalize_telemetry_signals(samples, ctx)
        assert summary.eligible_count == 3 * 3

    def test_result_count_equals_eligible_minus_missing(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=100.0, grid=100.0, pv=100.0),
        ]
        _, summary = normalize_telemetry_signals(samples, ctx)
        assert summary.result_count == 3
        assert summary.eligible_count == 3
        assert summary.missing_count == 0


class TestPipelineRawPowerPreserved:
    def test_raw_power_w_preserved_in_normalized_results(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1234.5),
        ]
        results, _ = normalize_telemetry_signals(samples, ctx)
        assert results[0].normalization.raw_power_w == 1234.5

    def test_raw_power_w_preserved_in_not_confirmed(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        samples = [
            _sample(datetime(2026, 8, 2, 10, 0, tzinfo=UTC), grid=300.0),
        ]
        results, _ = normalize_telemetry_signals(samples, ctx)
        assert results[0].normalization.raw_power_w == 300.0
