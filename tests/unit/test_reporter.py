import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

from solgreen.contracts import ImportStatus, SourceType, ValidityFlags, ValidityReason
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.importer.parsers.solarman_flow import parse_plant_flow
from solgreen.importer.parsers.solarman_telemetry import parse_inverter_telemetry
from solgreen.importer.reporter import (
    _validity_summary,
    build_import_batch,
    summarize_flow,
    summarize_telemetry,
    write_report_json,
    write_report_markdown,
)
from solgreen.quality import analyze_plant_flow, analyze_telemetry


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
    summary = summarize_flow(
        samples, ("a", "b"), quality_result=quality_result
    )
    assert summary.quality_result is quality_result
    assert summary.quality_result is not None
    assert summary.quality_result.quality_score == 1.0


def test_summarize_telemetry_with_quality_result() -> None:
    samples = parse_inverter_telemetry(Path("tests/fixtures/telemetry_small.csv"))
    quality_result = analyze_telemetry(samples, SourceType.SOLARMAN_INVERTER_TELEMETRY)
    summary = summarize_telemetry(
        samples, ("a", "b"), quality_result=quality_result
    )
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
    batch = batch.model_copy(
        update={"status": ImportStatus.PARSED, "quality_summary": summary}
    )
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
    batch = batch.model_copy(
        update={"status": ImportStatus.PARSED, "quality_summary": summary}
    )
    md_path = tmp_path / "report.md"
    write_report_markdown(batch, _validity_summary(samples), md_path)
    text = md_path.read_text(encoding="utf-8")
    assert "Quality score:" in text
    assert "Ordered:" in text
    assert "Strict (no duplicates):" in text
