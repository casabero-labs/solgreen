from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import psycopg2.extras

from solgreen.contracts import ImportStatus, SourceType
from solgreen.contracts.import_batch import ImportBatch, ImportMetadata, QualitySummary
from solgreen.db.connection import get_connection
from solgreen.db.repositories.base import Repository
from solgreen.diagnostics.llm_output import Hypothesis, LLMInterpretation
from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline.canonical import CanonicalSample
from solgreen.timeline.episode import CanonicalEpisode


def _ts(val: Any) -> datetime:
    if val is None:
        return datetime.now(UTC)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val
    return datetime.now(UTC)


def _interval_to_seconds(val: Any) -> float | None:
    if val is None:
        return None
    if hasattr(val, "total_seconds"):
        from datetime import timedelta

        td: timedelta = val
        return td.total_seconds()
    return None


class Psycopg2Repository(Repository):
    def __init__(self, conn: Any | None = None) -> None:
        self._conn = conn

    @property
    def conn(self) -> Any:
        if self._conn is None:
            self._conn = get_connection()
        return self._conn

    def save_import_batch(self, batch: ImportBatch) -> None:
        meta = batch.metadata
        qs = batch.quality_summary
        sql = """
            INSERT INTO import_batches (
                id, plant_id, source_type, original_filename, sha256,
                byte_size, parser_id, parser_version, imported_at,
                status, quality_summary, created_at
            ) VALUES (
                %(id)s, %(plant_id)s, %(source_type)s, %(original_filename)s, %(sha256)s,
                %(byte_size)s, %(parser_id)s, %(parser_version)s, %(imported_at)s,
                %(status)s, %(quality_summary)s, %(created_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
        qs_json = qs.model_dump(mode="json") if qs else None
        params = {
            "id": str(batch.id),
            "plant_id": batch.plant_id,
            "source_type": meta.source_type.value,
            "original_filename": meta.original_filename,
            "sha256": meta.sha256,
            "byte_size": meta.byte_size,
            "parser_id": meta.parser_id,
            "parser_version": meta.parser_version,
            "imported_at": meta.imported_at,
            "status": batch.status.value,
            "quality_summary": json.dumps(qs_json) if qs_json else None,
            "created_at": batch.created_at,
        }
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
        self.conn.commit()

    def get_import_batch(self, batch_id: UUID) -> ImportBatch | None:
        sql = "SELECT * FROM import_batches WHERE id = %(id)s"
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"id": str(batch_id)})
            row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_import_batch(row)

    def list_import_batches(self, plant_id: str) -> list[ImportBatch]:
        sql = "SELECT * FROM import_batches WHERE plant_id = %(plant_id)s ORDER BY imported_at DESC"
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"plant_id": plant_id})
            rows = cur.fetchall()
        return [self._row_to_import_batch(r) for r in rows]

    def _row_to_import_batch(self, row: dict[str, Any]) -> ImportBatch:
        qs_data = row.get("quality_summary")
        qs = QualitySummary(**qs_data) if qs_data else None
        metadata = ImportMetadata(
            source_type=SourceType(row["source_type"]),
            original_filename=row["original_filename"],
            sha256=row["sha256"],
            byte_size=row["byte_size"],
            parser_id=row["parser_id"],
            parser_version=row["parser_version"],
            imported_at=_ts(row["imported_at"]),
        )
        return ImportBatch(
            id=UUID(row["id"]),
            plant_id=row["plant_id"],
            metadata=metadata,
            status=ImportStatus(row["status"]),
            quality_summary=qs,
            created_at=_ts(row["created_at"]),
        )

    def save_canonical_samples(
        self, batch_id: UUID, samples: list[CanonicalSample]
    ) -> None:
        sql = """
            INSERT INTO canonical_samples (
                batch_id, timestamp_axis, source, time_delta,
                flow_potencia_produccion_w, flow_potencia_consumo_w,
                flow_grid_w, flow_soc_pct, flow_battery_w,
                telemetry_pv_power_w, telemetry_grid_power_w,
                telemetry_battery_power_w, telemetry_soc_pct,
                telemetry_inverter_state, quality_level, confidence
            ) VALUES (
                %(batch_id)s, %(timestamp_axis)s, %(source)s, %(time_delta)s,
                %(flow_potencia_produccion_w)s, %(flow_potencia_consumo_w)s,
                %(flow_grid_w)s, %(flow_soc_pct)s, %(flow_battery_w)s,
                %(telemetry_pv_power_w)s, %(telemetry_grid_power_w)s,
                %(telemetry_battery_power_w)s, %(telemetry_soc_pct)s,
                %(telemetry_inverter_state)s, %(quality_level)s, %(confidence)s
            )
        """
        for s in samples:
            td = s.time_delta
            params = {
                "batch_id": str(batch_id),
                "timestamp_axis": s.timestamp_axis,
                "source": s.source,
                "time_delta": td,
                "flow_potencia_produccion_w": s.flow_potencia_produccion_w,
                "flow_potencia_consumo_w": s.flow_potencia_consumo_w,
                "flow_grid_w": s.flow_grid_w,
                "flow_soc_pct": s.flow_soc_pct,
                "flow_battery_w": s.flow_battery_w,
                "telemetry_pv_power_w": s.telemetry_pv_power_w,
                "telemetry_grid_power_w": s.telemetry_grid_power_w,
                "telemetry_battery_power_w": s.telemetry_battery_power_w,
                "telemetry_soc_pct": s.telemetry_soc_pct,
                "telemetry_inverter_state": s.telemetry_inverter_state,
                "quality_level": s.quality_level,
                "confidence": s.confidence,
            }
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
        self.conn.commit()

    def get_canonical_samples(self, batch_id: UUID) -> list[CanonicalSample]:
        sql = """
            SELECT * FROM canonical_samples
            WHERE batch_id = %(batch_id)s
            ORDER BY timestamp_axis
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"batch_id": str(batch_id)})
            rows = cur.fetchall()
        return [self._row_to_canonical_sample(r) for r in rows]

    def _row_to_canonical_sample(self, row: dict[str, Any]) -> CanonicalSample:
        td_raw = row.get("time_delta")
        td = None
        if td_raw is not None and hasattr(td_raw, "total_seconds"):
            from datetime import timedelta

            td = timedelta(seconds=td_raw.total_seconds())
        return CanonicalSample(
            timestamp_axis=_ts(row["timestamp_axis"]),
            source=row["source"],
            time_delta=td,
            flow_potencia_produccion_w=row.get("flow_potencia_produccion_w"),
            flow_potencia_consumo_w=row.get("flow_potencia_consumo_w"),
            flow_grid_w=row.get("flow_grid_w"),
            flow_soc_pct=row.get("flow_soc_pct"),
            flow_battery_w=row.get("flow_battery_w"),
            telemetry_pv_power_w=row.get("telemetry_pv_power_w"),
            telemetry_grid_power_w=row.get("telemetry_grid_power_w"),
            telemetry_battery_power_w=row.get("telemetry_battery_power_w"),
            telemetry_soc_pct=row.get("telemetry_soc_pct"),
            telemetry_inverter_state=row.get("telemetry_inverter_state"),
            quality_level=row.get("quality_level", "measured"),
            confidence=row.get("confidence", 1.0),
        )

    def save_canonical_episode(
        self, batch_id: UUID, episode: CanonicalEpisode
    ) -> int:
        sql = """
            INSERT INTO canonical_episodes (
                batch_id, episode_type, start, "end", duration,
                sample_count, coverage_pct, source_summary, signals
            ) VALUES (
                %(batch_id)s, %(episode_type)s, %(start)s, %(end)s, %(duration)s,
                %(sample_count)s, %(coverage_pct)s, %(source_summary)s, %(signals)s
            )
            RETURNING id
        """
        signals_json = json.dumps(episode.signals) if episode.signals else None
        params = {
            "batch_id": str(batch_id),
            "episode_type": episode.episode_type,
            "start": episode.start,
            "end": episode.end,
            "duration": episode.duration,
            "sample_count": episode.sample_count,
            "coverage_pct": episode.coverage_pct,
            "source_summary": episode.source_summary,
            "signals": signals_json,
        }
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            episode_id: int = row[0]
        self.conn.commit()
        return episode_id

    def get_canonical_episodes(self, batch_id: UUID) -> list[CanonicalEpisode]:
        sql = """
            SELECT * FROM canonical_episodes
            WHERE batch_id = %(batch_id)s
            ORDER BY start
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"batch_id": str(batch_id)})
            rows = cur.fetchall()
        return [self._row_to_canonical_episode(r) for r in rows]

    def _row_to_canonical_episode(self, row: dict[str, Any]) -> CanonicalEpisode:
        signals_raw = row.get("signals")
        signals = json.loads(signals_raw) if signals_raw else {}
        return CanonicalEpisode(
            episode_type=row["episode_type"],
            start=_ts(row["start"]),
            end=_ts(row["end"]),
            duration=row["duration"],
            sample_count=row["sample_count"],
            coverage_pct=row["coverage_pct"],
            source_summary=row["source_summary"],
            signals=signals,
        )

    def save_rule_execution(
        self, episode_id: int, execution: RuleExecution
    ) -> None:
        sql = """
            INSERT INTO rule_executions (
                episode_id, rule_id, rule_version, period_start, period_end,
                parameters_used, fired, evidence, input_checksum
            ) VALUES (
                %(episode_id)s, %(rule_id)s, %(rule_version)s, %(period_start)s, %(period_end)s,
                %(parameters_used)s, %(fired)s, %(evidence)s, %(input_checksum)s
            )
        """
        params = {
            "episode_id": episode_id,
            "rule_id": execution.rule_id,
            "rule_version": execution.rule_version,
            "period_start": execution.period_start,
            "period_end": execution.period_end,
            "parameters_used": json.dumps(execution.parameters_used),
            "fired": execution.fired,
            "evidence": json.dumps(execution.evidence),
            "input_checksum": execution.input_checksum,
        }
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
        self.conn.commit()

    def get_rule_executions(self, episode_id: int) -> list[RuleExecution]:
        sql = """
            SELECT * FROM rule_executions
            WHERE episode_id = %(episode_id)s
            ORDER BY period_start
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"episode_id": episode_id})
            rows = cur.fetchall()
        return [self._row_to_rule_execution(r) for r in rows]

    def _row_to_rule_execution(self, row: dict[str, Any]) -> RuleExecution:
        params_raw = row.get("parameters_used") or {}
        evidence_raw = row.get("evidence") or []
        return RuleExecution(
            rule_id=row["rule_id"],
            rule_version=row["rule_version"],
            period_start=_ts(row["period_start"]),
            period_end=_ts(row["period_end"]),
            parameters_used=params_raw,
            fired=row["fired"],
            evidence=tuple(evidence_raw),
            input_checksum=row["input_checksum"],
        )

    def save_llm_interpretation(
        self, episode_id: int, interpretation: LLMInterpretation
    ) -> None:
        sql = """
            INSERT INTO llm_interpretations (
                episode_id, summary, hypotheses, alternatives,
                missing_info, suggested_actions, warnings,
                provider, model, prompt_version, input_hash
            ) VALUES (
                %(episode_id)s, %(summary)s, %(hypotheses)s, %(alternatives)s,
                %(missing_info)s, %(suggested_actions)s, %(warnings)s,
                %(provider)s, %(model)s, %(prompt_version)s, %(input_hash)s
            )
        """
        hyps = [
            {"description": h.description, "support_level": h.support_level, "evidence_refs": list(h.evidence_refs)}
            for h in interpretation.hypotheses
        ]
        params = {
            "episode_id": episode_id,
            "summary": interpretation.summary,
            "hypotheses": json.dumps(hyps),
            "alternatives": json.dumps(interpretation.alternatives),
            "missing_info": json.dumps(interpretation.missing_info),
            "suggested_actions": json.dumps(interpretation.suggested_actions),
            "warnings": json.dumps(interpretation.warnings),
            "provider": interpretation.provider,
            "model": interpretation.model,
            "prompt_version": interpretation.prompt_version,
            "input_hash": interpretation.input_hash,
        }
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
        self.conn.commit()

    def get_llm_interpretations(
        self, episode_id: int
    ) -> list[LLMInterpretation]:
        sql = """
            SELECT * FROM llm_interpretations
            WHERE episode_id = %(episode_id)s
            ORDER BY created_at
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, {"episode_id": episode_id})
            rows = cur.fetchall()
        return [self._row_to_llm_interpretation(r) for r in rows]

    def _row_to_llm_interpretation(self, row: dict[str, Any]) -> LLMInterpretation:
        hyps_raw = row.get("hypotheses") or []
        hypotheses = tuple(
            Hypothesis(
                description=h["description"],
                support_level=h["support_level"],
                evidence_refs=tuple(h.get("evidence_refs", [])),
            )
            for h in hyps_raw
        )
        return LLMInterpretation(
            summary=row["summary"],
            hypotheses=hypotheses,
            alternatives=tuple(row.get("alternatives") or ()),
            missing_info=tuple(row.get("missing_info") or ()),
            suggested_actions=tuple(row.get("suggested_actions") or ()),
            warnings=tuple(row.get("warnings") or ()),
            provider=row["provider"],
            model=row["model"],
            prompt_version=row["prompt_version"],
            input_hash=row["input_hash"],
        )
