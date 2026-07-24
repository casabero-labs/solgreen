from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO

from solgreen.contracts import (
    ImportBatch,
    ImportMetadata,
    ImportStatus,
    InverterTelemetrySample,
    ParserStatus,
    PlantFlowSample,
    QualitySummary,
    SourceType,
)
from solgreen.contracts.validity import ValidityFlags, ValidityReason
from solgreen.importer.normalize import (
    MAX_INLINE_NORMALIZATION_RESULTS,
    MAX_MD_WARNING_DETAILS,
    NormalizationSummary,
    NormalizedSignalResult,
)
from solgreen.quality._types import QualityResult
from solgreen.timeline import CanonicalSample

PARSER_VERSION = "0.1.0"


def build_import_batch(
    path: Path,
    source_type: SourceType,
    parser_id: str,
    plant_id: str,
) -> ImportBatch:
    from solgreen.core.hashing import compute_sha256

    sha256_hex = compute_sha256(path)
    metadata = ImportMetadata(
        source_type=source_type,
        original_filename=path.name,
        sha256=sha256_hex,
        byte_size=path.stat().st_size,
        parser_id=parser_id,
        parser_version=PARSER_VERSION,
        imported_at=datetime.now(UTC),
    )
    return ImportBatch(
        plant_id=plant_id,
        metadata=metadata,
        status=ImportStatus.PARSING,
    )


def summarize_flow(
    samples: list[PlantFlowSample],
    expected_columns: tuple[str, ...],
    quality_result: QualityResult | None = None,
) -> QualitySummary:
    rows_total = len(samples)
    rows_rejected = sum(1 for s in samples if not s.validity.is_valid)
    return QualitySummary(
        rows_total=rows_total,
        rows_parsed=rows_total - rows_rejected,
        rows_rejected=rows_rejected,
        detected_columns=expected_columns,
        missing_canonical_columns=(),
        quality_result=quality_result,
    )


def summarize_telemetry(
    samples: list[InverterTelemetrySample],
    expected_columns: tuple[str, ...],
    quality_result: QualityResult | None = None,
) -> QualitySummary:
    rows_total = len(samples)
    rows_rejected = sum(1 for s in samples if not s.validity.is_valid)
    return QualitySummary(
        rows_total=rows_total,
        rows_parsed=rows_total - rows_rejected,
        rows_rejected=rows_rejected,
        detected_columns=expected_columns,
        missing_canonical_columns=(),
        quality_result=quality_result,
    )


def _validity_summary(
    samples: list[PlantFlowSample] | list[InverterTelemetrySample],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for s in samples:
        for reason in s.validity.reasons:
            counter[reason.value] += 1
        if s.validity.is_valid and not s.validity.reasons:
            counter["ok"] += 1
    return dict(counter)


def write_report_json(
    batch: ImportBatch,
    validity: dict[str, int],
    output: IO[str] | Path,
    *,
    norm_summary: NormalizationSummary | None = None,
    norm_results: tuple[NormalizedSignalResult, ...] = (),
) -> None:
    payload: dict[str, object] = {
        "batch": batch.model_dump(mode="json"),
        "validity": validity,
        "parser_status": ParserStatus.OK.value
        if batch.quality_summary and batch.quality_summary.rows_rejected == 0
        else ParserStatus.PARTIAL.value,
    }
    if batch.quality_summary is not None and batch.quality_summary.quality_result is not None:
        payload["quality_analysis"] = batch.quality_summary.quality_result.model_dump(mode="json")

    if norm_summary is not None and norm_summary.eligible_count > 0:
        norm_payload: dict[str, object] = {
            "summary": norm_summary.model_dump(mode="json"),
        }
        if norm_summary.eligible_count > 0:
            if len(norm_results) <= MAX_INLINE_NORMALIZATION_RESULTS:
                norm_payload["results"] = [r.model_dump(mode="json") for r in norm_results]
                norm_payload["results_artifact"] = None
            else:
                norm_payload["results"] = []
                norm_payload["results_artifact"] = _write_normalization_artifact(
                    output, norm_results
                )
        else:
            norm_payload["results"] = []
            norm_payload["results_artifact"] = None
        payload["normalization"] = norm_payload

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if isinstance(output, Path):
        output.write_text(text, encoding="utf-8")
    else:
        output.write(text)


def write_report_markdown(
    batch: ImportBatch,
    validity: dict[str, int],
    output: IO[str] | Path,
    *,
    norm_summary: NormalizationSummary | None = None,
    norm_results: tuple[NormalizedSignalResult, ...] = (),
) -> None:
    md_lines = [
        "# Solgreen import report",
        "",
        f"- Batch ID: `{batch.id}`",
        f"- Plant: `{batch.plant_id}`",
        f"- File: `{batch.metadata.original_filename}`",
        f"- Source type: `{batch.metadata.source_type.value}`",
        f"- Parser: `{batch.metadata.parser_id}` v{batch.metadata.parser_version}",
        f"- SHA-256: `{batch.metadata.sha256}`",
        f"- Size: {batch.metadata.byte_size} bytes",
        f"- Imported at: {batch.metadata.imported_at.isoformat()}",
        f"- Status: {batch.status.value}",
    ]
    if batch.quality_summary is not None:
        qs = batch.quality_summary
        md_lines.append("")
        md_lines.append("## Quality")
        md_lines.append("")
        md_lines.append(f"- Rows total: {qs.rows_total}")
        md_lines.append(f"- Rows parsed: {qs.rows_parsed}")
        md_lines.append(f"- Rows rejected: {qs.rows_rejected}")
        if qs.quality_result is not None:
            qr = qs.quality_result
            md_lines.append(f"- Quality score: {qr.quality_score:.2f}")
            md_lines.append(f"- Ordered: {qr.ordering.was_ordered}")
            md_lines.append(f"- Strict (no duplicates): {qr.ordering.was_strict}")
            if qr.duplicates:
                md_lines.append(f"- Duplicate groups: {len(qr.duplicates)}")
            if qr.gaps:
                md_lines.append(f"- Temporal gaps: {len(qr.gaps)}")
        md_lines.append("")
        md_lines.append("## Validity reasons")
        md_lines.append("")
        if validity:
            for reason, count in sorted(validity.items()):
                md_lines.append(f"- `{reason}`: {count}")
        else:
            md_lines.append("- (none)")

    if norm_summary is not None and norm_summary.eligible_count > 0:
        _append_normalization_markdown(md_lines, norm_summary, norm_results)

    text = "\n".join(md_lines) + "\n"
    if isinstance(output, Path):
        output.write_text(text, encoding="utf-8")
    else:
        output.write(text)


def empty_validity_flags() -> ValidityFlags:
    return ValidityFlags()


def parse_error_flags() -> ValidityFlags:
    return ValidityFlags().with_reason(ValidityReason.PARSE_ERROR)


def _write_normalization_artifact(
    output: IO[str] | Path,
    norm_results: tuple[NormalizedSignalResult, ...],
) -> str:
    if isinstance(output, Path):
        artifact_path = output.with_suffix(".normalization.json")
    else:
        artifact_path = Path("out.normalization.json")

    results_payload = [r.model_dump(mode="json") for r in norm_results]
    text = json.dumps(results_payload, indent=2, ensure_ascii=False)
    artifact_path.write_text(text, encoding="utf-8")
    return str(artifact_path)


def _append_normalization_markdown(
    md_lines: list[str],
    norm_summary: NormalizationSummary,
    norm_results: tuple[NormalizedSignalResult, ...],
) -> None:
    invariant_ok = _check_summary_invariant(norm_summary)
    md_lines.append("")
    md_lines.append("## Sign Normalization")
    md_lines.append("")
    md_lines.append(f"- Eligible: {norm_summary.eligible_count}")
    md_lines.append(f"- Missing: {norm_summary.missing_count}")
    md_lines.append(f"- Results: {norm_summary.result_count}")
    md_lines.append(f"- Normalized: {norm_summary.normalized_count}")
    md_lines.append(f"- Not confirmed: {norm_summary.not_confirmed_count}")
    md_lines.append(f"- Not found: {norm_summary.not_found_count}")
    md_lines.append(f"- Errors: {norm_summary.error_count}")
    md_lines.append(f"- Warnings: {norm_summary.warning_count}")
    md_lines.append(f"- Invariant: {'OK' if invariant_ok else 'FAILED'}")

    warnings = [r for r in norm_results if _result_is_warning(r)]

    if warnings:
        md_lines.append("")
        md_lines.append(f"### Warning details (sample, max {MAX_MD_WARNING_DETAILS})")
        md_lines.append("")
        md_lines.append("| Signal | Timestamp | Status | Detail |")
        md_lines.append("|--------|-----------|--------|--------|")
        for w in warnings[:MAX_MD_WARNING_DETAILS]:
            ts = w.timestamp_utc.isoformat()
            status = w.normalization.status.value
            detail = ""
            if w.normalization.warnings:
                detail = "; ".join(w.normalization.warnings)
            elif w.normalization.status.value == "profile_not_confirmed":
                detail = "direction evidence not CONFIRMED"
            elif w.normalization.status.value == "profile_not_found":
                detail = "no profile for timestamp"
            else:
                detail = w.normalization.status.value
            md_lines.append(f"| `{w.raw_signal_name}` | {ts} | `{status}` | {detail} |")


def _result_is_warning(result: NormalizedSignalResult) -> bool:
    status = result.normalization.status.value
    has_warnings = bool(result.normalization.warnings)
    if status == "normalized" and has_warnings:
        return True
    if status in ("profile_not_confirmed", "profile_not_found"):
        return True
    error_statuses = {
        "nonfinite_value",
        "field_mismatch",
        "invalid_unsigned_negative",
    }
    return status in error_statuses


def _check_summary_invariant(summary: NormalizationSummary) -> bool:
    total = (
        summary.missing_count
        + summary.normalized_count
        + summary.not_confirmed_count
        + summary.not_found_count
        + summary.error_count
    )
    if summary.eligible_count != total:
        return False
    if summary.result_count != summary.eligible_count - summary.missing_count:
        return False
    return summary.warning_count <= summary.result_count


class _TimelineSummaryForReport:
    def __init__(
        self,
        total_samples: int,
        merged_count: int,
        flow_only_count: int,
        telemetry_only_count: int,
        coverage_pct: float,
    ) -> None:
        self.total_samples = total_samples
        self.merged_count = merged_count
        self.flow_only_count = flow_only_count
        self.telemetry_only_count = telemetry_only_count
        self.coverage_pct = coverage_pct


def write_timeline_json(
    timeline: list[CanonicalSample],
    summary: _TimelineSummaryForReport,
    output: IO[str] | Path,
) -> None:
    payload: dict[str, object] = {
        "timeline": [s.model_dump(mode="json") for s in timeline],
        "summary": {
            "total_samples": summary.total_samples,
            "merged_count": summary.merged_count,
            "flow_only_count": summary.flow_only_count,
            "telemetry_only_count": summary.telemetry_only_count,
            "coverage_pct": summary.coverage_pct,
        },
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if isinstance(output, Path):
        output.write_text(text, encoding="utf-8")
    else:
        output.write(text)


def write_timeline_markdown(
    summary: _TimelineSummaryForReport,
    tolerance: timedelta,
    output: IO[str] | Path,
) -> None:
    md_lines = [
        "# Solgreen timeline alignment report",
        "",
        f"- Tolerance: {tolerance}",
        "",
        "## Summary",
        "",
        f"- Total canonical samples: {summary.total_samples}",
        f"- Merged (flow + telemetry): {summary.merged_count}",
        f"- Flow only: {summary.flow_only_count}",
        f"- Telemetry only: {summary.telemetry_only_count}",
        f"- Coverage: {summary.coverage_pct:.1f}%",
    ]
    text = "\n".join(md_lines) + "\n"
    if isinstance(output, Path):
        output.write_text(text, encoding="utf-8")
    else:
        output.write(text)
