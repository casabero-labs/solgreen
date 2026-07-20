from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from solgreen import __version__
from solgreen.contracts import ImportStatus, InverterTelemetrySample, PlantFlowSample, SourceType
from solgreen.importer.detector import detect_format
from solgreen.importer.exceptions import UnsupportedFormatError
from solgreen.importer.parsers.base import PLANT_FLOW_COLUMNS
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
) -> None:
    source_type = format_override or detect_format(file)
    if source_type == SourceType.UNKNOWN:
        raise typer.BadParameter(
            f"Could not detect format for {file.name}"
        ) from UnsupportedFormatError(path=file, observed_columns=())

    output_dir.mkdir(parents=True, exist_ok=True)

    samples: list[PlantFlowSample] | list[InverterTelemetrySample]
    if source_type == SourceType.SOLARMAN_PLANT_FLOW:
        samples = parse_plant_flow(file)
        summary = summarize_flow(samples, PLANT_FLOW_COLUMNS)
        parser_id = f"solarman_flow_{file.suffix.lstrip('.').lower()}"
    elif source_type == SourceType.SOLARMAN_INVERTER_TELEMETRY:
        samples = parse_inverter_telemetry(file)
        from solgreen.contracts import ORIGINAL_ES_TO_CANONICAL

        summary = summarize_telemetry(samples, tuple(ORIGINAL_ES_TO_CANONICAL.keys()))
        parser_id = f"solarman_telemetry_{file.suffix.lstrip('.').lower()}"
    else:
        raise typer.BadParameter(f"Unsupported source type: {source_type}")

    batch = build_import_batch(file, source_type, parser_id, plant_id)
    batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})

    validity = _validity_summary(samples)
    json_path = output_dir / f"{file.stem}.import.json"
    md_path = output_dir / f"{file.stem}.import.md"
    write_report_json(batch, validity, json_path)
    write_report_markdown(batch, validity, md_path)

    typer.echo(f"Parsed {summary.rows_parsed}/{summary.rows_total} rows from {file.name}")
    typer.echo(f"Report: {json_path}")
    typer.echo(f"Report: {md_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
