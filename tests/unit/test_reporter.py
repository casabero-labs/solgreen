import json
from datetime import UTC, datetime, timedelta
from io import StringIO
from pathlib import Path

from solgreen.contracts import ImportStatus, SourceType, ValidityFlags, ValidityReason
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.importer.parsers.solarman_flow import parse_plant_flow
from solgreen.importer.parsers.solarman_telemetry import parse_inverter_telemetry
from solgreen.importer.reporter import (
    _TimelineSummaryForReport,
    _validity_summary,
    build_import_batch,
    summarize_flow,
    summarize_telemetry,
    write_report_json,
    write_report_markdown,
    write_timeline_json,
    write_timeline_markdown,
)
from solgreen.quality import analyze_plant_flow, analyze_telemetry
from solgreen.timeline import CanonicalSample


def test_build_import_batch_uses_real_sha_and_size() -> None:
    path = Path("tests/fixtures/flow_small.csv")
    batch = build_import_batch(
        path, SourceType.SOLARMAN_PLANT_FLOW, "solarman_flow_csv", "casabero"
    )
    assert batch.plant_id == "casabero"
    assert (
        batch.metadata.sha256 == "26cc6a3d1e0c228c58a40268255e063402d63c7cef1221db39286260f498a7b0"
    )
    assert batch.metadata.byte_size == 715
    assert batch.metadata.parser_version == "0.1.0"
    assert batch.status == ImportStatus.PARSING


def test_summarize_flow_counts_rejected() -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    summary = summarize_flow(samples, ("a", "b"))
    assert summary.rows_total == len(samples)
    assert summary.rows_rejected == 0
    assert summary.rows_parsed == len(samples)


def test_validity_summary_ok_only() -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    summary = _validity_summary(samples)
    assert summary == {"ok": len(samples)}


def test_write_report_json_includes_status_and_validity() -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    batch = build_import_batch(
        Path("tests/fixtures/flow_small.csv"),
        SourceType.SOLARMAN_PLANT_FLOW,
        "solarman_flow_csv",
        "casabero",
    )
    summary = summarize_flow(samples, ("a", "b"))
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
    sink = StringIO()
    write_report_json(batch, _validity_summary(samples), sink)
    payload = json.loads(sink.getvalue())
    assert payload["batch"]["plant_id"] == "casabero"
    assert payload["batch"]["quality_summary"]["rows_total"] == len(samples)
    assert payload["validity"]["ok"] == len(samples)
    assert payload["parser_status"] == "ok"


def test_write_report_json_partial_when_rejections() -> None:
    samples = [
        PlantFlowSample(
            timestamp_original=datetime(2026, 7, 17, 12, 35),
            timestamp_utc=datetime(2026, 7, 17, 12, 35, tzinfo=UTC),
            validity=ValidityFlags(),
        ),
        PlantFlowSample(
            timestamp_original=datetime(2026, 7, 17, 12, 40),
            timestamp_utc=datetime(2026, 7, 17, 12, 40, tzinfo=UTC),
            validity=ValidityFlags().with_reason(ValidityReason.PARSE_ERROR),
        ),
    ]
    batch = build_import_batch(
        Path("tests/fixtures/flow_small.csv"),
        SourceType.SOLARMAN_PLANT_FLOW,
        "solarman_flow_csv",
        "casabero",
    )
    summary = summarize_flow(samples, ("a", "b"))
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
    sink = StringIO()
    write_report_json(batch, _validity_summary(samples), sink)
    payload = json.loads(sink.getvalue())
    assert payload["parser_status"] == "partial"
    assert payload["validity"]["ok"] == 1
    assert payload["validity"]["parse_error"] == 1


def test_write_report_markdown_includes_quality_block(tmp_path: Path) -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    batch = build_import_batch(
        Path("tests/fixtures/flow_small.csv"),
        SourceType.SOLARMAN_PLANT_FLOW,
        "solarman_flow_csv",
        "casabero",
    )
    summary = summarize_flow(samples, ("a", "b"))
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
    md_path = tmp_path / "report.md"
    write_report_markdown(batch, _validity_summary(samples), md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "# Solgreen import report" in text
    assert "Plant: `casabero`" in text
    assert "## Quality" in text


def test_summarize_telemetry_uses_canonical_columns() -> None:
    samples = parse_inverter_telemetry(Path("tests/fixtures/telemetry_small.csv"))
    from solgreen.contracts import ORIGINAL_ES_TO_CANONICAL

    summary = summarize_telemetry(samples, tuple(ORIGINAL_ES_TO_CANONICAL.keys()))
    assert summary.rows_total == 3
    assert summary.detected_columns == tuple(ORIGINAL_ES_TO_CANONICAL.keys())


def test_summarize_flow_with_quality_result() -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    quality_result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
    summary = summarize_flow(samples, ("a", "b"), quality_result=quality_result)
    assert summary.quality_result is quality_result
    assert summary.quality_result is not None
    assert summary.quality_result.quality_score == 1.0


def test_summarize_telemetry_with_quality_result() -> None:
    samples = parse_inverter_telemetry(Path("tests/fixtures/telemetry_small.csv"))
    quality_result = analyze_telemetry(samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
    summary = summarize_telemetry(samples, ("a", "b"), quality_result=quality_result)
    assert summary.quality_result is not None
    assert summary.quality_result.quality_score == 1.0


def test_write_report_json_includes_quality_analysis_when_present() -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    quality_result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
    summary = summarize_flow(samples, ("a", "b"), quality_result=quality_result)
    batch = build_import_batch(
        Path("tests/fixtures/flow_small.csv"),
        SourceType.SOLARMAN_PLANT_FLOW,
        "solarman_flow_csv",
        "casabero",
    )
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
    sink = StringIO()
    write_report_json(batch, _validity_summary(samples), sink)
    payload = json.loads(sink.getvalue())
    assert "quality_analysis" in payload
    assert payload["quality_analysis"]["quality_score"] == 1.0
    assert payload["quality_analysis"]["total_rows"] == len(samples)


def test_write_report_markdown_includes_quality_score(tmp_path: Path) -> None:
    samples = parse_plant_flow(Path("tests/fixtures/flow_small.csv"))
    quality_result = analyze_plant_flow(samples, SourceType.SOLARMAN_PLANT_FLOW)
    summary = summarize_flow(samples, ("a", "b"), quality_result=quality_result)
    batch = build_import_batch(
        Path("tests/fixtures/flow_small.csv"),
        SourceType.SOLARMAN_PLANT_FLOW,
        "solarman_flow_csv",
        "casabero",
    )
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
    md_path = tmp_path / "report.md"
    write_report_markdown(batch, _validity_summary(samples), md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "Quality score:" in text
    assert "Ordered:" in text
    assert "Strict (no duplicates):" in text


def test_write_timeline_json_produces_valid_payload(tmp_path: Path) -> None:
    ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    samples = [
        CanonicalSample(
            timestamp_axis=ts,
            source="merged",
            time_delta=None,
            flow_potencia_produccion_w=5000.0,
            flow_potencia_consumo_w=1000.0,
            flow_grid_w=4000.0,
            flow_soc_pct=None,
            flow_battery_w=None,
            telemetry_pv_power_w=4900.0,
            telemetry_grid_power_w=4100.0,
            telemetry_battery_power_w=0.0,
            telemetry_soc_pct=80.0,
            telemetry_inverter_state="producing",
            quality_level="measured",
            confidence=0.95,
        ),
    ]
    summary = _TimelineSummaryForReport(
        total_samples=1,
        merged_count=1,
        flow_only_count=0,
        telemetry_only_count=0,
        coverage_pct=100.0,
    )
    json_path = tmp_path / "timeline.json"
    write_timeline_json(samples, summary, json_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_samples"] == 1
    assert payload["summary"]["merged_count"] == 1
    assert payload["summary"]["coverage_pct"] == 100.0
    assert len(payload["timeline"]) == 1
    assert payload["timeline"][0]["source"] == "merged"


def test_write_timeline_markdown_produces_summary(tmp_path: Path) -> None:
    summary = _TimelineSummaryForReport(
        total_samples=10,
        merged_count=6,
        flow_only_count=2,
        telemetry_only_count=2,
        coverage_pct=60.0,
    )
    md_path = tmp_path / "timeline.md"
    write_timeline_markdown(summary, timedelta(minutes=2, seconds=30), md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "# Solgreen timeline alignment report" in text
    assert "Tolerance: 0:02:30" in text
    assert "Total canonical samples: 10" in text
    assert "Merged (flow + telemetry): 6" in text
    assert "Coverage: 60.0%" in text
