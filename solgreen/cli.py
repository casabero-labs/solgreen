from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Annotated

import typer

from solgreen import __version__
from solgreen.contracts import (
    ImportBatch,
    ImportStatus,
    InverterTelemetrySample,
    PlantFlowSample,
    SourceType,
)
from solgreen.importer.detector import detect_format
from solgreen.importer.exceptions import UnsupportedFormatError
from solgreen.importer.parsers.base import PLANT_FLOW_COLUMNS
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
from solgreen.timeline import CanonicalSample, join_by_tolerance

app = typer.Typer(add_completion=False, help="Solgreen CLI", no_args_is_help=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"solgreen {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    return None


@dataclass
class _ParsedFile:
    samples: list[PlantFlowSample] | list[InverterTelemetrySample]
    source_type: SourceType
    batch: ImportBatch
    validity: dict[str, int]


def _parse_single_file(file: Path, plant_id: str) -> _ParsedFile:
    source_type = detect_format(file)
    if source_type == SourceType.UNKNOWN:
        raise typer.BadParameter(
            f"Could not detect format for {file.name}"
        ) from UnsupportedFormatError(path=file, observed_columns=())

    if source_type == SourceType.SOLARMAN_PLANT_FLOW:
        flow_samples: list[PlantFlowSample] = parse_plant_flow(file)
        quality_result = analyze_plant_flow(flow_samples, source_type)
        summary = summarize_flow(
            flow_samples, PLANT_FLOW_COLUMNS, quality_result=quality_result
        )
        parser_id = f"solarman_flow_{file.suffix.lstrip('.').lower()}"
        batch = build_import_batch(file, source_type, parser_id, plant_id)
        batch = batch.model_copy(
            update={"status": ImportStatus.PARSED, "quality_summary": summary}
        )
        validity = _validity_summary(flow_samples)
        return _ParsedFile(samples=flow_samples, source_type=source_type, batch=batch, validity=validity)

    elif source_type == SourceType.SOLARMAN_INVERTER_TELEMETRY:
        tel_samples: list[InverterTelemetrySample] = parse_inverter_telemetry(file)
        from solgreen.contracts import ORIGINAL_ES_TO_CANONICAL

        quality_result = analyze_telemetry(tel_samples, source_type)
        summary = summarize_telemetry(
            tel_samples, tuple(ORIGINAL_ES_TO_CANONICAL.keys()), quality_result=quality_result
        )
        parser_id = f"solarman_telemetry_{file.suffix.lstrip('.').lower()}"
        batch = build_import_batch(file, source_type, parser_id, plant_id)
        batch = batch.model_copy(
            update={"status": ImportStatus.PARSED, "quality_summary": summary}
        )
        validity = _validity_summary(tel_samples)
        return _ParsedFile(samples=tel_samples, source_type=source_type, batch=batch, validity=validity)

    else:
        raise typer.BadParameter(f"Unsupported source type: {source_type}")


@app.command("import")
def import_file(
    file: Annotated[
        Path,
        typer.Option("--file", "-f", help="Path to SolarMAN export (CSV or XLSX)."),
    ],
    plant_id: Annotated[
        str,
        typer.Option("--plant-id", help="Plant identifier (e.g. casabero)."),
    ] = "casabero",
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Where to write reports."),
    ] = Path("./out"),
    format_override: Annotated[
        SourceType | None,
        typer.Option("--format", help="Skip detector, force a source type."),
    ] = None,
    align_with: Annotated[
        Path | None,
        typer.Option(
            "--align-with",
            help="Second file to align with the first (flow with telemetry). Generates timeline report.",
        ),
    ] = None,
    tolerance: Annotated[
        str | None,
        typer.Option(
            "--tolerance",
            help="Join tolerance as ISO timedelta (e.g. 'PT2M30S' for 2m30s). Default: 2m30s.",
        ),
    ] = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if align_with is not None:
        _import_with_align(file, align_with, plant_id, output_dir, tolerance)
        return

    source_type = format_override or detect_format(file)
    if source_type == SourceType.UNKNOWN:
        raise typer.BadParameter(
            f"Could not detect format for {file.name}"
        ) from UnsupportedFormatError(path=file, observed_columns=())

    parsed = _parse_single_file(file, plant_id)
    json_path = output_dir / f"{file.stem}.import.json"
    md_path = output_dir / f"{file.stem}.import.md"
    write_report_json(parsed.batch, parsed.validity, json_path)
    write_report_markdown(parsed.batch, parsed.validity, md_path)

    qs = parsed.batch.quality_summary
    total_rows = qs.rows_total if qs else 0
    parsed_rows = qs.rows_parsed if qs else 0
    typer.echo(f"Parsed {parsed_rows}/{total_rows} rows from {file.name}")
    typer.echo(f"Report: {json_path}")
    typer.echo(f"Report: {md_path}")


def _import_with_align(
    file1: Path,
    file2: Path,
    plant_id: str,
    output_dir: Path,
    tolerance_str: str | None,
) -> None:
    tol: timedelta
    if tolerance_str is not None:
        tol = timedelta(seconds=_parse_iso_duration(tolerance_str))
    else:
        tol = timedelta(minutes=2, seconds=30)

    parsed1 = _parse_single_file(file1, plant_id)
    parsed2 = _parse_single_file(file2, plant_id)

    if parsed1.source_type == parsed2.source_type:
        raise typer.BadParameter(
            "--align-with requires two files of different types (flow + telemetry)"
        )

    if parsed1.source_type == SourceType.SOLARMAN_PLANT_FLOW:
        flow_samples: list[PlantFlowSample] = parsed1.samples  # type: ignore[assignment]
        tel_samples: list[InverterTelemetrySample] = parsed2.samples  # type: ignore[assignment]
    else:
        flow_samples = parsed2.samples  # type: ignore[assignment]
        tel_samples = parsed1.samples  # type: ignore[assignment]

    timeline = join_by_tolerance(flow_samples, tel_samples, tolerance=tol)
    timeline_summary = _summarize_timeline(timeline)

    json_path = output_dir / f"{file1.stem}__{file2.stem}.timeline.json"
    md_path = output_dir / f"{file1.stem}__{file2.stem}.timeline.md"
    write_timeline_json(timeline, timeline_summary, json_path)
    write_timeline_markdown(timeline_summary, tol, md_path)

    typer.echo(f"Timeline: {len(timeline)} canonical samples")
    typer.echo(f"  merged: {timeline_summary.merged_count}")
    typer.echo(f"  flow only: {timeline_summary.flow_only_count}")
    typer.echo(f"  telemetry only: {timeline_summary.telemetry_only_count}")
    typer.echo(f"  coverage: {timeline_summary.coverage_pct:.1f}%")
    typer.echo(f"Report: {json_path}")
    typer.echo(f"Report: {md_path}")


def _summarize_timeline(
    timeline: list[CanonicalSample],
) -> _TimelineSummaryForReport:
    merged_count = sum(1 for s in timeline if s.source == "merged")
    flow_only = sum(1 for s in timeline if s.source == "flow")
    tel_only = sum(1 for s in timeline if s.source == "telemetry")
    total = len(timeline)
    coverage_pct = (merged_count / total * 100) if total > 0 else 0.0
    return _TimelineSummaryForReport(
        total_samples=total,
        merged_count=merged_count,
        flow_only_count=flow_only,
        telemetry_only_count=tel_only,
        coverage_pct=coverage_pct,
    )


def _parse_iso_duration(iso: str) -> float:
    from datetime import timedelta
    from dateutil.parser import isoparser

    td: timedelta = isoparser().parse_timedelta(iso)
    return td.total_seconds()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
