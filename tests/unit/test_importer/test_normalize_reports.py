from __future__ import annotations

import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

from solgreen.contracts import ImportStatus, SourceType
from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.importer.normalize import (
    MAX_INLINE_NORMALIZATION_RESULTS,
    MAX_MD_WARNING_DETAILS,
    NormalizationSummary,
    NormalizedSignalResult,
    build_normalization_context,
    normalize_telemetry_signals,
)
from solgreen.importer.reporter import (
    build_import_batch,
    summarize_telemetry,
    write_report_json,
    write_report_markdown,
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


class TestRegressionOff:
    def test_off_mode_json_no_normalization_key(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_json(batch, {}, buf, norm_summary=summary, norm_results=results)
        payload = json.loads(buf.getvalue())

        assert "normalization" not in payload

    def test_off_mode_markdown_no_normalization_section(self) -> None:
        ctx = build_normalization_context(plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_markdown(batch, {}, buf, norm_summary=summary, norm_results=results)
        text = buf.getvalue()

        assert "Sign Normalization" not in text

    def test_legacy_mode_json_has_normalization_key(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_json(batch, {}, buf, norm_summary=summary, norm_results=results)
        payload = json.loads(buf.getvalue())

        assert "normalization" in payload
        assert "summary" in payload["normalization"]
        assert "results" in payload["normalization"]
        assert payload["normalization"]["results_artifact"] is None
        assert len(payload["normalization"]["results"]) == 1

    def test_legacy_mode_markdown_has_normalization_section(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [_sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0)]
        results, summary = normalize_telemetry_signals(samples, ctx)

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_markdown(batch, {}, buf, norm_summary=summary, norm_results=results)
        text = buf.getvalue()

        assert "Sign Normalization" in text
        assert "Eligible:" in text
        assert "Normalized:" in text

    def test_markdown_includes_warning_details(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=3.0),
            _sample(
                datetime(2026, 7, 21, 10, 5, tzinfo=UTC),
                battery=1200.0,
                grid=300.0,
                pv=-100.0,
            ),
        ]
        results, summary = normalize_telemetry_signals(samples, ctx)

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_markdown(batch, {}, buf, norm_summary=summary, norm_results=results)
        text = buf.getvalue()

        assert "Warning details" in text

    def test_markdown_respects_max_warning_details(self) -> None:
        ctx = build_normalization_context(
            cli_mode="d10",
            cli_effective_from="2026-08-01T00:00:00Z",
            plant_id="SOLGREEN",
        )
        over_limit = MAX_MD_WARNING_DETAILS + 5
        samples = [
            _sample(
                datetime(2026, 8, 2, 10, 0, tzinfo=UTC)
                + __import__("datetime").timedelta(minutes=i),
                grid=300.0,
            )
            for i in range(over_limit)
        ]
        results, summary = normalize_telemetry_signals(samples, ctx)
        assert summary.not_confirmed_count == over_limit

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_markdown(batch, {}, buf, norm_summary=summary, norm_results=results)
        text = buf.getvalue()

        not_confirmed_count = text.count("profile_not_confirmed")
        assert not_confirmed_count <= MAX_MD_WARNING_DETAILS

    def test_external_artifact_when_results_exceed_limit(self) -> None:
        from solgreen.energy.normalization import (
            DirectionalPowerResult,
            NormalizationStatus,
        )
        from solgreen.energy.sign_profiles import (
            AuthorityClass,
            CanonicalPowerField,
            ProfileStatus,
            SourceSystem,
        )

        ctx = build_normalization_context(plant_id="SOLGREEN")
        samples = [
            _sample(
                datetime(2026, 7, 21, 10, 0, tzinfo=UTC)
                + __import__("datetime").timedelta(seconds=300 * i),
                battery=100.0,
            )
            for i in range(2)
        ]
        _results, _summary = normalize_telemetry_signals(samples, ctx)

        over_limit = MAX_INLINE_NORMALIZATION_RESULTS + 1
        fake_result = NormalizedSignalResult(
            canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
            source_system=SourceSystem.INVERTER_TELEMETRY,
            timestamp_utc=datetime(2026, 7, 21, 10, 0, tzinfo=UTC),
            raw_signal_name="potencia_de_bateria_w",
            normalization=DirectionalPowerResult(
                canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
                source_system=SourceSystem.INVERTER_TELEMETRY,
                authority_class=AuthorityClass.OPERATIONAL,
                raw_power_w=100.0,
                status=NormalizationStatus.NORMALIZED,
                profile_version="v1",
                profile_status=ProfileStatus.CONFIRMED,
                battery_discharge_w=100.0,
            ),
        )
        fake_results = tuple(fake_result for _ in range(over_limit))
        fake_summary = NormalizationSummary(
            eligible_count=over_limit,
            missing_count=0,
            result_count=over_limit,
            normalized_count=over_limit,
            not_confirmed_count=0,
            not_found_count=0,
            error_count=0,
            warning_count=0,
        )

        batch = build_import_batch(
            Path("tests/fixtures/telemetry_small.csv"),
            SourceType.SOLARMAN_INVERTER_TELEMETRY,
            "test",
            "SOLGREEN",
        )
        qs = summarize_telemetry(samples, ())
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": qs})

        buf = StringIO()
        write_report_json(batch, {}, buf, norm_summary=fake_summary, norm_results=fake_results)
        payload = json.loads(buf.getvalue())

        assert "normalization" in payload
        assert payload["normalization"]["results"] == []
        assert payload["normalization"]["results_artifact"] is not None

    def test_deadband_warning_counted_in_summary(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=3.0),
            _sample(datetime(2026, 7, 21, 10, 5, tzinfo=UTC), battery=2.0),
        ]
        _, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 2
        assert summary.warning_count == 2

    def test_normalized_without_warnings_not_counted_as_warning(self) -> None:
        ctx = build_normalization_context(cli_mode="legacy", plant_id="SOLGREEN")
        samples = [
            _sample(datetime(2026, 7, 21, 10, 0, tzinfo=UTC), battery=1200.0),
        ]
        _, summary = normalize_telemetry_signals(samples, ctx)

        assert summary.normalized_count == 1
        assert summary.warning_count == 0
