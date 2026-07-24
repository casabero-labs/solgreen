from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any

import typer

from solgreen import __version__
from solgreen.contracts import (
    ImportBatch,
    ImportStatus,
    InverterTelemetrySample,
    PlantFlowSample,
    SourceType,
)
from solgreen.db import Repository, get_connection
from solgreen.db.repositories.psycopg2_repo import Psycopg2Repository
from solgreen.diagnostics.llm_input import LLMEpisodeInput
from solgreen.diagnostics.llm_provider import LLMProvider, interpret_episode
from solgreen.diagnostics.rule_catalog import RuleCatalog
from solgreen.diagnostics.rule_evaluation import (
    RuleEvaluationOutcome,
    RuleEvaluatorRegistry,
    eligible_fired_rules,
    evaluate_rule_catalog,
)
from solgreen.importer.detector import detect_format
from solgreen.importer.exceptions import UnsupportedFormatError
from solgreen.importer.normalize import (
    ImportNormalizationContext,
    NormalizationSummary,
    NormalizedSignalResult,
    build_normalization_context,
    normalize_telemetry_signals,
)
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
from solgreen.timeline.duration import parse_iso_duration
from solgreen.timeline.episode import CanonicalEpisode, build_episodes
from solgreen.timeline.join import DEFAULT_TOLERANCE

app = typer.Typer(add_completion=False, help="Solgreen CLI", no_args_is_help=True)
db_app = typer.Typer(add_completion=False, help="Database operations", no_args_is_help=True)
solarman_app = typer.Typer(
    add_completion=False, help="SOLARMAN API operations", no_args_is_help=True
)
app.add_typer(db_app, name="db")
app.add_typer(solarman_app, name="solarman")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"solgreen {__version__}")
        raise typer.Exit()


def _build_repository(db_url: str | None) -> Repository | None:
    if db_url is None:
        return None
    conn = get_connection(db_url)
    return Psycopg2Repository(conn)


def _build_llm_provider(
    provider_name: str | None,
    model: str | None,
    api_key: str | None,
    *,
    fallback_provider_name: str | None = None,
    fallback_model: str | None = None,
    fallback_api_key: str | None = None,
) -> LLMProvider | None:
    if provider_name is None or provider_name == "none":
        return None
    if api_key is None:
        raise typer.BadParameter(f"--llm-api-key required for provider '{provider_name}'")

    from solgreen.diagnostics.llm_provider import FallbackProvider

    provider = _instantiate_provider(provider_name, api_key, model)
    if not fallback_provider_name or fallback_provider_name == "none":
        return provider
    if fallback_api_key is None:
        raise typer.BadParameter(
            f"--llm-fallback-api-key required for fallback provider '{fallback_provider_name}'"
        )
    fallback = _instantiate_provider(fallback_provider_name, fallback_api_key, fallback_model)
    return FallbackProvider(primary=provider, fallback=fallback)


def _instantiate_provider(
    name: str,
    api_key: str,
    model: str | None,
) -> LLMProvider:
    from solgreen.diagnostics.llm_provider import DeepSeekProvider, MiniMaxProvider

    if name == "minimax":
        return MiniMaxProvider(api_key=api_key, model=model)
    if name == "deepseek":
        return DeepSeekProvider(api_key=api_key, model=model)
    raise typer.BadParameter(f"Unknown LLM provider: {name}")


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
    norm_results: tuple[NormalizedSignalResult, ...] = ()
    norm_summary: NormalizationSummary | None = None


def _parse_single_file(
    file: Path,
    plant_id: str,
    repo: Repository | None = None,
    norm_ctx: ImportNormalizationContext | None = None,
) -> _ParsedFile:
    source_type = detect_format(file)
    if source_type == SourceType.UNKNOWN:
        raise typer.BadParameter(
            f"Could not detect format for {file.name}"
        ) from UnsupportedFormatError(path=file, observed_columns=())

    if source_type == SourceType.SOLARMAN_PLANT_FLOW:
        flow_samples: list[PlantFlowSample] = parse_plant_flow(file)
        quality_result = analyze_plant_flow(flow_samples, source_type)
        summary = summarize_flow(flow_samples, PLANT_FLOW_COLUMNS, quality_result=quality_result)
        parser_id = f"solarman_flow_{file.suffix.lstrip('.').lower()}"
        batch = build_import_batch(file, source_type, parser_id, plant_id)
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
        if repo is not None:
            repo.save_import_batch(batch)
        validity = _validity_summary(flow_samples)
        return _ParsedFile(
            samples=flow_samples, source_type=source_type, batch=batch, validity=validity
        )

    elif source_type == SourceType.SOLARMAN_INVERTER_TELEMETRY:
        tel_samples: list[InverterTelemetrySample] = parse_inverter_telemetry(file)
        from solgreen.contracts import ORIGINAL_ES_TO_CANONICAL

        quality_result = analyze_telemetry(tel_samples, source_type)
        summary = summarize_telemetry(
            tel_samples, tuple(ORIGINAL_ES_TO_CANONICAL.keys()), quality_result=quality_result
        )
        parser_id = f"solarman_telemetry_{file.suffix.lstrip('.').lower()}"
        batch = build_import_batch(file, source_type, parser_id, plant_id)
        batch = batch.model_copy(update={"status": ImportStatus.PARSED, "quality_summary": summary})
        if repo is not None:
            repo.save_import_batch(batch)
        validity = _validity_summary(tel_samples)

        norm_results: tuple[NormalizedSignalResult, ...] = ()
        norm_summary: NormalizationSummary | None = None
        if norm_ctx is not None:
            norm_results, norm_summary = normalize_telemetry_signals(tel_samples, norm_ctx)

        return _ParsedFile(
            samples=tel_samples,
            source_type=source_type,
            batch=batch,
            validity=validity,
            norm_results=norm_results,
            norm_summary=norm_summary,
        )

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
    db_url: Annotated[
        str | None,
        typer.Option(
            "--db-url",
            envvar="SOLGREEN_DATABASE_URL",
            help="PostgreSQL connection URL. If omitted, persistence is skipped.",
        ),
    ] = None,
    no_db: Annotated[
        bool,
        typer.Option(
            "--no-db",
            help="Explicitly skip database persistence even if SOLGREEN_DATABASE_URL is set.",
        ),
    ] = False,
    llm_provider_name: Annotated[
        str | None,
        typer.Option(
            "--llm-provider",
            envvar="SOLGREEN_LLM_PROVIDER",
            help="LLM provider name (e.g. 'deepseek'). If omitted or 'none', LLM is skipped.",
        ),
    ] = None,
    llm_model: Annotated[
        str | None,
        typer.Option(
            "--llm-model",
            envvar="SOLGREEN_LLM_MODEL",
            help="LLM model override (provider-specific).",
        ),
    ] = None,
    llm_api_key: Annotated[
        str | None,
        typer.Option(
            "--llm-api-key",
            envvar="SOLGREEN_LLM_API_KEY",
            help="LLM API key. Required when --llm-provider is set.",
        ),
    ] = None,
    llm_fallback_provider: Annotated[
        str | None,
        typer.Option(
            "--llm-fallback-provider",
            envvar="SOLGREEN_LLM_FALLBACK_PROVIDER",
            help="Fallback LLM provider if primary fails (e.g. 'deepseek').",
        ),
    ] = None,
    llm_fallback_model: Annotated[
        str | None,
        typer.Option(
            "--llm-fallback-model",
            envvar="SOLGREEN_LLM_FALLBACK_MODEL",
            help="Fallback LLM model override.",
        ),
    ] = None,
    llm_fallback_api_key: Annotated[
        str | None,
        typer.Option(
            "--llm-fallback-api-key",
            envvar="SOLGREEN_LLM_FALLBACK_API_KEY",
            help="Fallback LLM API key.",
        ),
    ] = None,
    sign_normalization_mode: Annotated[
        str | None,
        typer.Option(
            "--sign-normalization-mode",
            envvar="SOLGREEN_SIGN_NORMALIZATION_MODE",
            help="Sign normalization mode: off, legacy, or d10. Default: off.",
        ),
    ] = None,
    sign_registry_effective_from: Annotated[
        str | None,
        typer.Option(
            "--sign-registry-effective-from",
            envvar="SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM",
            help="ISO 8601 cutover timestamp for d10 mode (e.g. 2026-08-01T00:00:00Z).",
        ),
    ] = None,
) -> None:
    if align_with is not None:
        if tolerance is None:
            _tol = DEFAULT_TOLERANCE
        else:
            try:
                _tol = parse_iso_duration(tolerance)
            except ValueError as exc:
                raise typer.BadParameter(f"Invalid --tolerance value {tolerance!r}: {exc}") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    repo = None if no_db else _build_repository(db_url)
    provider = _build_llm_provider(
        llm_provider_name,
        llm_model,
        llm_api_key,
        fallback_provider_name=llm_fallback_provider,
        fallback_model=llm_fallback_model,
        fallback_api_key=llm_fallback_api_key,
    )

    norm_ctx = build_normalization_context(
        cli_mode=sign_normalization_mode,
        cli_effective_from=sign_registry_effective_from,
        plant_id=plant_id,
    )

    if align_with is not None:
        _import_with_align(file, align_with, plant_id, output_dir, _tol, repo, provider, norm_ctx)
        return

    source_type = format_override or detect_format(file)
    if source_type == SourceType.UNKNOWN:
        raise typer.BadParameter(
            f"Could not detect format for {file.name}"
        ) from UnsupportedFormatError(path=file, observed_columns=())

    parsed = _parse_single_file(file, plant_id, repo, norm_ctx)
    json_path = output_dir / f"{file.stem}.import.json"
    md_path = output_dir / f"{file.stem}.import.md"
    write_report_json(
        parsed.batch,
        parsed.validity,
        json_path,
        norm_summary=parsed.norm_summary,
        norm_results=parsed.norm_results,
    )
    write_report_markdown(
        parsed.batch,
        parsed.validity,
        md_path,
        norm_summary=parsed.norm_summary,
        norm_results=parsed.norm_results,
    )

    qs = parsed.batch.quality_summary
    total_rows = qs.rows_total if qs else 0
    parsed_rows = qs.rows_parsed if qs else 0
    typer.echo(f"Parsed {parsed_rows}/{total_rows} rows from {file.name}")
    if repo is not None:
        typer.echo(f"Persisted batch {parsed.batch.id}")
    typer.echo(f"Report: {json_path}")
    typer.echo(f"Report: {md_path}")


def _import_with_align(
    file1: Path,
    file2: Path,
    plant_id: str,
    output_dir: Path,
    tol: timedelta,
    repo: Repository | None = None,
    provider: LLMProvider | None = None,
    norm_ctx: ImportNormalizationContext | None = None,
) -> None:
    parsed1 = _parse_single_file(file1, plant_id, repo, norm_ctx)
    parsed2 = _parse_single_file(file2, plant_id, repo, norm_ctx)

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

    episodes_built = build_episodes(timeline)

    rule_evaluations: dict[int, tuple[RuleEvaluationOutcome, ...]] = {}
    if repo is not None:
        repo.save_canonical_samples(parsed1.batch.id, timeline)
        catalog = RuleCatalog()
        registry = RuleEvaluatorRegistry()
        for ep in episodes_built:
            episode_id = repo.save_canonical_episode(parsed1.batch.id, ep)
            outcomes = evaluate_rule_catalog(catalog, ep, registry)
            rule_evaluations[episode_id] = outcomes
            for outcome in outcomes:
                if outcome.execution is not None:
                    repo.save_rule_execution(episode_id, outcome.execution)
            if provider is not None:
                _run_llm_interpretation(
                    provider,
                    plant_id,
                    ep,
                    outcomes,
                    episode_id,
                    repo,
                )

    json_path = output_dir / f"{file1.stem}__{file2.stem}.timeline.json"
    md_path = output_dir / f"{file1.stem}__{file2.stem}.timeline.md"
    write_timeline_json(timeline, timeline_summary, json_path)
    write_timeline_markdown(timeline_summary, tol, md_path)

    typer.echo(f"Timeline: {len(timeline)} canonical samples")
    typer.echo(f"  merged: {timeline_summary.merged_count}")
    typer.echo(f"  flow only: {timeline_summary.flow_only_count}")
    typer.echo(f"  telemetry only: {timeline_summary.telemetry_only_count}")
    typer.echo(f"  coverage: {timeline_summary.coverage_pct:.1f}%")
    typer.echo(f"  episodes: {len(episodes_built)}")
    if rule_evaluations:
        evaluated = sum(
            len([o for o in outcomes if o.execution is not None])
            for outcomes in rule_evaluations.values()
        )
        not_evaluable = sum(
            len([o for o in outcomes if o.execution is None])
            for outcomes in rule_evaluations.values()
        )
        typer.echo(f"  Rules: {evaluated} evaluated, {not_evaluable} not evaluable")
    if repo is not None:
        typer.echo("  persisted to database")
    if provider is not None:
        typer.echo(f"  LLM provider: {provider.provider_name}")
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


def _run_llm_interpretation(
    provider: LLMProvider,
    plant_id: str,
    episode: CanonicalEpisode,
    outcomes: tuple[RuleEvaluationOutcome, ...],
    episode_id: int,
    repo: Repository,
) -> None:
    real_executions = tuple(o.execution for o in outcomes if o.execution is not None)
    eligible = eligible_fired_rules(real_executions)

    if not eligible:
        typer.echo("    LLM skipped: no validated fired-rule evidence")
        return

    input_data = LLMEpisodeInput(
        plant_id=plant_id,
        episode=episode,
        fired_rules=eligible,
        data_quality_summary=(f"Episode {episode.episode_type}, {episode.sample_count} samples."),
    )
    try:
        interpretation = interpret_episode(provider, input_data)
        repo.save_llm_interpretation(episode_id, interpretation)
        typer.echo(f"    LLM: {interpretation.summary[:80]}...")
    except Exception as exc:
        typer.echo(f"    LLM error: {exc}")


@app.command("deploy-schema")
def deploy_schema(
    db_url: Annotated[
        str | None,
        typer.Option(
            "--db-url",
            envvar="SOLGREEN_DATABASE_URL",
            help="PostgreSQL connection URL.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print SQL without executing."),
    ] = False,
) -> None:
    if db_url is None:
        raise typer.BadParameter("--db-url required or set SOLGREEN_DATABASE_URL")
    from pathlib import Path as _Path

    migration_path = _Path(__file__).parent / "db" / "migrations" / "001_initial.sql"
    sql = migration_path.read_text(encoding="utf-8")
    if dry_run:
        typer.echo(sql)
        return
    conn = get_connection(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        typer.echo("Schema deployed successfully.")
    finally:
        conn.close()


@db_app.command("status")
def db_status(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", envvar="SOLGREEN_DATABASE_URL", help="PostgreSQL connection URL."),
    ] = None,
    migrations_dir: Annotated[
        Path | None,
        typer.Option("--migrations-dir", help="Path to migrations directory."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Machine-readable JSON output."),
    ] = False,
) -> None:
    import json

    if db_url is None:
        if json_output:
            typer.echo('{"ok": false, "error": "no database URL"}')
            raise typer.Exit(code=1)
        raise typer.BadParameter("--db-url required or set SOLGREEN_DATABASE_URL")

    from solgreen.db.connection import get_connection
    from solgreen.db.migrations.runner import get_migration_runner

    conn = get_connection(db_url)
    try:
        runner = get_migration_runner(conn)
        if migrations_dir is None:
            migrations_dir = Path(__file__).parent / "db" / "migrations"
        status_result = runner.status(migrations_dir)
        applied = status_result[0]
        pending = status_result[1]

        if json_output:
            output = {
                "ok": True,
                "applied": [
                    {"version": m.version, "name": m.name, "checksum": m.checksum} for m in applied
                ],
                "pending": [{"version": m.version, "name": m.name} for m in pending],
            }
            typer.echo(json.dumps(output))
        else:
            if not applied:
                typer.echo("No migrations applied.")
            else:
                typer.echo(f"{len(applied)} migration(s) applied:")
                for m in applied:
                    typer.echo(f"  {m.version}: {m.name} ({m.checksum[:8]}...) at {m.applied_at}")
            if pending:
                typer.echo(f"\n{len(pending)} migration(s) pending:")
                for p in pending:
                    typer.echo(f"  {p.version}: {p.name}")
            else:
                typer.echo("\nAll migrations applied.")
    finally:
        conn.close()


@db_app.command("migrate")
def db_migrate(
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", envvar="SOLGREEN_DATABASE_URL", help="PostgreSQL connection URL."),
    ] = None,
    migrations_dir: Annotated[
        Path | None,
        typer.Option("--migrations-dir", help="Path to migrations directory."),
    ] = None,
    target_version: Annotated[
        int | None,
        typer.Option("--to", help="Apply up to and including this version."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be applied without applying."),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Machine-readable JSON output."),
    ] = False,
) -> None:
    import json

    if db_url is None:
        if json_output:
            typer.echo('{"ok": false, "error": "no database URL"}')
            raise typer.Exit(code=1)
        raise typer.BadParameter("--db-url required or set SOLGREEN_DATABASE_URL")

    from solgreen.db.connection import get_connection
    from solgreen.db.migrations.runner import MigrationFile, get_migration_runner

    conn = get_connection(db_url)
    try:
        runner = get_migration_runner(conn)
        if migrations_dir is None:
            migrations_dir = Path(__file__).parent / "db" / "migrations"

        if dry_run:
            status_result = runner.status(migrations_dir)
            pending_dr: list[MigrationFile] = status_result[1]
            if target_version is not None:
                pending_to_apply = [m for m in pending_dr if m.version <= target_version]
            else:
                pending_to_apply = pending_dr
            if json_output:
                typer.echo(
                    json.dumps(
                        {
                            "ok": True,
                            "dry_run": True,
                            "would_apply": [
                                {"version": m.version, "name": m.name} for m in pending_to_apply
                            ],
                        }
                    )
                )
            else:
                if not pending_to_apply:
                    typer.echo("No migrations to apply.")
                else:
                    typer.echo(f"Would apply {len(pending_to_apply)} migration(s):")
                    for m in pending_to_apply:
                        typer.echo(f"  {m.version}: {m.name}")
            return

        applied_migrations: list[MigrationFile] = runner.apply(migrations_dir, target_version)
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "ok": True,
                        "applied": [
                            {"version": m.version, "name": m.name} for m in applied_migrations
                        ],
                    }
                )
            )
        else:
            if not applied_migrations:
                typer.echo("No new migrations to apply.")
            else:
                typer.echo(f"Applied {len(applied_migrations)} migration(s):")
                for m in applied_migrations:
                    typer.echo(f"  {m.version}: {m.name}")
    except RuntimeError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}))
        raise typer.Exit(code=1) from None
    finally:
        conn.close()


@app.command("health-check")
def health_check(
    db_url: Annotated[
        str | None,
        typer.Option(
            "--db-url",
            envvar="SOLGREEN_DATABASE_URL",
            help="PostgreSQL connection URL.",
        ),
    ] = None,
    check_llm: Annotated[
        bool,
        typer.Option("--check-llm", help="Also verify LLM provider connectivity."),
    ] = False,
    llm_provider_name: Annotated[
        str | None,
        typer.Option("--llm-provider", envvar="SOLGREEN_LLM_PROVIDER"),
    ] = None,
    llm_api_key: Annotated[
        str | None,
        typer.Option("--llm-api-key", envvar="SOLGREEN_LLM_API_KEY"),
    ] = None,
) -> None:
    ok = True

    if db_url is not None:
        try:
            conn = get_connection(db_url)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
            conn.close()
            if result == (1,):
                typer.echo("DB: OK")
            else:
                typer.echo("DB: UNEXPECTED response")
                ok = False
        except Exception as exc:
            typer.echo(f"DB: FAILED ({exc})")
            ok = False
    else:
        typer.echo("DB: SKIPPED (no --db-url)")

    if check_llm:
        provider = _build_llm_provider(llm_provider_name, None, llm_api_key)
        if provider is None:
            typer.echo("LLM: SKIPPED (no provider)")
        else:
            try:
                response = provider.complete("Say 'ok' in one word.", max_tokens=10)
                if response.strip():
                    typer.echo(f"LLM: OK ({provider.provider_name})")
                else:
                    typer.echo("LLM: EMPTY response")
                    ok = False
            except Exception as exc:
                typer.echo(f"LLM: FAILED ({exc})")
                ok = False

    if not ok:
        raise typer.Exit(code=1)


@solarman_app.command("doctor")
def solarman_doctor(
    station_id: Annotated[
        str | None,
        typer.Option("--station-id", help="Specific station ID to diagnose."),
    ] = None,
    db_url: Annotated[
        str | None,
        typer.Option("--db-url", envvar="SOLGREEN_DATABASE_URL"),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Machine-readable JSON output."),
    ] = False,
) -> None:
    """Run SOLARMAN API operational diagnostics without persisting data."""
    import json

    from solgreen.integrations.solarman.doctor import run_doctor
    from solgreen.integrations.solarman.settings import build_settings_from_env

    try:
        settings = build_settings_from_env()
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": f"Configuration error: {exc}"}))
        else:
            typer.echo(f"[FAIL] Configuration error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    try:
        result = run_doctor(settings=settings, station_id=station_id, db_url=db_url)
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": f"Doctor check failed: {exc}"}))
        else:
            typer.echo(f"[FAIL] Doctor check failed: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if json_output:
        output = {"ok": True, **result.to_dict()}
        typer.echo(json.dumps(output, indent=2))
    else:
        summary = result.to_dict()["summary"]
        typer.echo(
            f"\nSOLARMAN Doctor — {summary['total']} checks, {summary['pass']} PASS, {summary['warn']} WARN, {summary['fail']} FAIL\n"
        )
        for check in result.checks:
            icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[check.status.value]
            typer.echo(f"  {icon} [{check.status.value}] {check.name}")
            if check.detail:
                typer.echo(f"      {check.detail}")
        typer.echo()
        if not result.ready:
            typer.echo("NOT READY — fix failures before syncing.", err=True)
            raise typer.Exit(code=1)


@solarman_app.command("sync")
def solarman_sync(
    plant_id: Annotated[
        str,
        typer.Option("--plant-id", help="Plant identifier (e.g. casabero)."),
    ] = "casabero",
    station_id: Annotated[
        str | None,
        typer.Option("--station-id", help="SOLARMAN station ID."),
    ] = None,
    db_url: Annotated[
        str | None,
        typer.Option(
            "--db-url",
            envvar="SOLGREEN_DATABASE_URL",
            help="PostgreSQL connection URL. If omitted, persistence is skipped.",
        ),
    ] = None,
    no_db: Annotated[
        bool,
        typer.Option(
            "--no-db",
            help="Skip database persistence even if SOLGREEN_DATABASE_URL is set.",
        ),
    ] = False,
    sign_normalization_mode: Annotated[
        str | None,
        typer.Option(
            "--sign-normalization-mode",
            envvar="SOLGREEN_SIGN_NORMALIZATION_MODE",
            help="Sign normalization mode: off, legacy, or d10. Default: off.",
        ),
    ] = None,
    sign_registry_effective_from: Annotated[
        str | None,
        typer.Option(
            "--sign-registry-effective-from",
            envvar="SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM",
            help="ISO 8601 cutover timestamp for d10 mode.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Machine-readable JSON output."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate and show plan without syncing."),
    ] = False,
) -> None:
    from solgreen.db.advisory_lock import LockStatus, acquire_sync_lock
    from solgreen.db.connection import get_connection
    from solgreen.integrations.solarman.client import SolarmanClient
    from solgreen.integrations.solarman.settings import build_settings_from_env
    from solgreen.integrations.solarman.station_resolver import (
        StationResolutionError,
        get_station_from_env,
        mask_station_id,
        resolve_station,
    )
    from solgreen.integrations.solarman.sync import sync_solarman_station

    start_ms = int(time.time() * 1000)
    settings = build_settings_from_env()
    client = SolarmanClient(settings)

    try:
        resolved = resolve_station(
            client,
            explicit_station_id=station_id,
            env_station_id=get_station_from_env(),
        )
        resolved_id = resolved.station_id
        masked_id = resolved.masked_id
    except StationResolutionError as exc:
        _sync_error(
            status="FAILED",
            status_detail=str(exc),
            plant_id=plant_id,
            masked_id=mask_station_id(station_id or ""),
            json_output=json_output,
            start_ms=start_ms,
        )
        raise typer.Exit(code=1) from None

    norm_ctx = build_normalization_context(
        cli_mode=sign_normalization_mode,
        cli_effective_from=sign_registry_effective_from,
        plant_id=plant_id,
    )

    conn = None
    lock = None
    lock_status: LockStatus | None = None
    persist = db_url and not no_db

    if persist:
        conn = get_connection(db_url)
        lock, lock_status = acquire_sync_lock(conn, plant_id, resolved_id)
        if lock_status == LockStatus.BUSY:
            _sync_skipped_locked(
                plant_id=plant_id,
                masked_id=masked_id,
                json_output=json_output,
                start_ms=start_ms,
            )
            if conn:
                conn.close()
            raise typer.Exit(code=0)
        if lock_status == LockStatus.ERROR:
            _sync_error(
                status="FAILED",
                status_detail="Failed to acquire advisory lock",
                plant_id=plant_id,
                masked_id=masked_id,
                json_output=json_output,
                start_ms=start_ms,
            )
            if conn:
                conn.close()
            raise typer.Exit(code=1) from None

    dry_conn = None if dry_run else conn

    try:
        result = sync_solarman_station(
            client=client,
            station_id=resolved_id,
            plant_id=plant_id,
            norm_ctx=norm_ctx,
            conn=dry_conn,
        )
    except Exception as exc:
        _sync_error(
            status="FAILED",
            status_detail=str(exc),
            plant_id=plant_id,
            masked_id=masked_id,
            json_output=json_output,
            start_ms=start_ms,
        )
        raise typer.Exit(code=1) from None
    finally:
        if lock is not None:
            released = lock.release()
            if released == LockStatus.ERROR:
                result.errors.append("advisory_lock_release_failed")
        if conn is not None:
            conn.close()

    duration_ms = int(time.time() * 1000) - start_ms

    if dry_run:
        _sync_success(
            status="DRY_RUN_SUCCESS",
            plant_id=plant_id,
            masked_id=masked_id,
            result=result,
            json_output=json_output,
            dry_run=True,
            duration_ms=duration_ms,
        )
        raise typer.Exit(code=0)

    if result.devices_queried == 0 or result.devices_succeeded == 0:
        status = "FAILED"
        exit_code = 1
    elif result.errors or result.not_confirmed_count > 0:
        status = "PARTIAL_SUCCESS"
        exit_code = 0
    else:
        status = "SUCCESS"
        exit_code = 0

    _sync_success(
        status=status,
        plant_id=plant_id,
        masked_id=masked_id,
        result=result,
        json_output=json_output,
        dry_run=False,
        duration_ms=duration_ms,
        warnings=["distributed_lock_disabled"] if not persist else None,
    )
    raise typer.Exit(code=exit_code)


def _sync_success(
    status: str,
    plant_id: str,
    masked_id: str,
    result: Any,
    json_output: bool,
    dry_run: bool,
    duration_ms: int,
    warnings: list[str] | None = None,
) -> None:
    output = {
        "ok": status in ("SUCCESS", "PARTIAL_SUCCESS", "DRY_RUN_SUCCESS"),
        "status": status,
        "station_id_masked": masked_id,
        "plant_id": plant_id,
        "devices_queried": result.devices_queried,
        "devices_succeeded": result.devices_succeeded,
        "snapshots_inserted": result.snapshots_inserted if not dry_run else 0,
        "snapshots_skipped": result.snapshots_skipped if not dry_run else 0,
        "duration_ms": duration_ms,
    }
    if result.normalized_count:
        output["normalized_count"] = result.normalized_count
        output["not_confirmed_count"] = result.not_confirmed_count
        output["not_found_count"] = result.not_found_count
    if result.errors:
        output["error_count"] = len(result.errors)
        output["errors"] = result.errors[:10]
    if warnings:
        output["warnings"] = warnings
    if json_output:
        typer.echo(json.dumps(output))
    else:
        typer.echo(f"Status: {status}")
        typer.echo(f"Station: {masked_id}")
        typer.echo(f"Devices queried: {result.devices_queried}")
        typer.echo(f"Devices succeeded: {result.devices_succeeded}")
        if not dry_run:
            typer.echo(f"Snapshots inserted: {result.snapshots_inserted}")
            typer.echo(f"Snapshots skipped: {result.snapshots_skipped}")
        if result.normalized_count:
            typer.echo(f"Normalized signals: {result.normalized_count}")
            typer.echo(f"Not confirmed: {result.not_confirmed_count}")
            typer.echo(f"Not found: {result.not_found_count}")
        if result.errors:
            typer.echo(f"Errors: {len(result.errors)}")
            for err in result.errors[:5]:
                typer.echo(f"  - {err}")
        if warnings:
            for w in warnings:
                typer.echo(f"  Warning: {w}")
        typer.echo(f"Duration: {duration_ms}ms")


def _sync_skipped_locked(
    plant_id: str,
    masked_id: str,
    json_output: bool,
    start_ms: int,
) -> None:
    duration_ms = int(time.time() * 1000) - start_ms
    output = {
        "ok": True,
        "status": "SKIPPED_LOCKED",
        "skipped_locked": True,
        "station_id_masked": masked_id,
        "plant_id": plant_id,
        "warning": "Another sync is running for this station; no API call made.",
        "duration_ms": duration_ms,
    }
    if json_output:
        typer.echo(json.dumps(output))
    else:
        typer.echo(f"[SKIPPED_LOCKED] Station: {masked_id}", err=True)
        typer.echo("Another sync is running for this station; no API call made.", err=True)


def _sync_error(
    status: str,
    status_detail: str,
    plant_id: str,
    masked_id: str,
    json_output: bool,
    start_ms: int,
) -> None:
    duration_ms = int(time.time() * 1000) - start_ms
    output = {
        "ok": False,
        "status": status,
        "station_id_masked": masked_id,
        "plant_id": plant_id,
        "errors": [status_detail],
        "duration_ms": duration_ms,
    }
    if json_output:
        typer.echo(json.dumps(output))
    else:
        typer.echo(f"[{status}] {status_detail}", err=True)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
