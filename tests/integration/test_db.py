from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import psycopg2
import pytest

from solgreen.contracts import ImportStatus, SourceType
from solgreen.contracts.import_batch import ImportBatch, ImportMetadata, QualitySummary
from solgreen.db.connection import execute_script
from solgreen.db.repositories.psycopg2_repo import Psycopg2Repository
from solgreen.diagnostics.llm_output import Hypothesis, LLMInterpretation
from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline.canonical import CanonicalSample
from solgreen.timeline.episode import CanonicalEpisode

DATABASE_URL = os.environ.get(
    "SOLGREEN_DATABASE_URL",
    "postgresql://solgreen:solgreen@localhost:5432/solgreen",
)


def _has_db() -> bool:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def repo() -> Psycopg2Repository:
    conn = psycopg2.connect(DATABASE_URL)
    migration_path = "solgreen/db/migrations/001_initial.sql"
    with open(migration_path) as f:
        execute_script(f.read(), conn)
    return Psycopg2Repository(conn)


@pytest.fixture
def sample_batch() -> ImportBatch:
    meta = ImportMetadata(
        source_type=SourceType.SOLARMAN_PLANT_FLOW,
        original_filename="test.csv",
        sha256="a" * 64,
        byte_size=1024,
        parser_id="solarman_flow_csv",
        parser_version="1.0.0",
        imported_at=datetime.now(UTC),
    )
    return ImportBatch(
        plant_id="test_plant",
        metadata=meta,
        status=ImportStatus.PARSED,
        quality_summary=QualitySummary(
            rows_total=10,
            rows_parsed=10,
            rows_rejected=0,
            detected_columns=("a", "b"),
        ),
    )


@pytest.fixture
def sample_samples() -> list[CanonicalSample]:
    ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    return [
        CanonicalSample(
            timestamp_axis=ts,
            source="merged",
            flow_potencia_produccion_w=5000.0,
            flow_grid_w=4000.0,
            telemetry_pv_power_w=4900.0,
            confidence=1.0,
        ),
        CanonicalSample(
            timestamp_axis=ts + timedelta(minutes=5),
            source="merged",
            flow_potencia_produccion_w=4800.0,
            flow_grid_w=3800.0,
            telemetry_pv_power_w=4700.0,
            confidence=0.9,
        ),
    ]


@pytest.fixture
def sample_episode() -> CanonicalEpisode:
    ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    return CanonicalEpisode(
        episode_type="pv_production",
        start=ts,
        end=ts + timedelta(minutes=10),
        duration=timedelta(minutes=10),
        sample_count=3,
        coverage_pct=100.0,
        source_summary="merged",
        signals={"flow_potencia_produccion_w": 5000.0},
    )


@pytest.mark.skipif(not _has_db(), reason="No database available")
class TestImportBatchRepo:
    def test_save_and_get(self, repo: Psycopg2Repository, sample_batch: ImportBatch) -> None:
        repo.save_import_batch(sample_batch)
        got = repo.get_import_batch(sample_batch.id)
        assert got is not None
        assert got.plant_id == "test_plant"
        assert got.metadata.original_filename == "test.csv"
        assert got.quality_summary is not None
        assert got.quality_summary.rows_total == 10

    def test_list_by_plant(self, repo: Psycopg2Repository, sample_batch: ImportBatch) -> None:
        repo.save_import_batch(sample_batch)
        batches = repo.list_import_batches("test_plant")
        assert len(batches) >= 1
        assert any(b.id == sample_batch.id for b in batches)


@pytest.mark.skipif(not _has_db(), reason="No database available")
class TestCanonicalSampleRepo:
    def test_save_and_get(
        self,
        repo: Psycopg2Repository,
        sample_batch: ImportBatch,
        sample_samples: list[CanonicalSample],
    ) -> None:
        repo.save_import_batch(sample_batch)
        repo.save_canonical_samples(sample_batch.id, sample_samples)
        got = repo.get_canonical_samples(sample_batch.id)
        assert len(got) == 2
        assert got[0].source == "merged"
        assert got[0].flow_potencia_produccion_w == 5000.0


@pytest.mark.skipif(not _has_db(), reason="No database available")
class TestCanonicalEpisodeRepo:
    def test_save_and_get(
        self, repo: Psycopg2Repository, sample_batch: ImportBatch, sample_episode: CanonicalEpisode
    ) -> None:
        repo.save_import_batch(sample_batch)
        episode_id = repo.save_canonical_episode(sample_batch.id, sample_episode)
        assert episode_id > 0
        eps = repo.get_canonical_episodes(sample_batch.id)
        assert len(eps) == 1
        assert eps[0].episode_type == "pv_production"


@pytest.mark.skipif(not _has_db(), reason="No database available")
class TestRuleExecutionRepo:
    def test_save_and_get(
        self, repo: Psycopg2Repository, sample_batch: ImportBatch, sample_episode: CanonicalEpisode
    ) -> None:
        repo.save_import_batch(sample_batch)
        episode_id = repo.save_canonical_episode(sample_batch.id, sample_episode)
        ts = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
        exec_ = RuleExecution(
            rule_id="PV-001",
            rule_version="1.0.0",
            period_start=ts,
            period_end=ts + timedelta(minutes=10),
            parameters_used={"min_voltage_v": 100},
            fired=True,
            evidence=("PV power dropped.",),
            input_checksum="abc123",
        )
        repo.save_rule_execution(episode_id, exec_)
        got = repo.get_rule_executions(episode_id)
        assert len(got) == 1
        assert got[0].rule_id == "PV-001"
        assert got[0].fired is True


@pytest.mark.skipif(not _has_db(), reason="No database available")
class TestLLMInterpretationRepo:
    def test_save_and_get(
        self, repo: Psycopg2Repository, sample_batch: ImportBatch, sample_episode: CanonicalEpisode
    ) -> None:
        repo.save_import_batch(sample_batch)
        episode_id = repo.save_canonical_episode(sample_batch.id, sample_episode)
        interp = LLMInterpretation(
            summary="PV dropout detected.",
            hypotheses=(
                Hypothesis(description="MPPT fault", support_level="moderate", evidence_refs=(0,)),
            ),
            alternatives=("Cloud cover.",),
            missing_info=("Inverter log.",),
            suggested_actions=("Check MPPT.",),
            warnings=("Do not reset remotely.",),
            provider="openai",
            model="gpt-4",
            prompt_version="1.0.0",
            input_hash="abc123",
        )
        repo.save_llm_interpretation(episode_id, interp)
        got = repo.get_llm_interpretations(episode_id)
        assert len(got) == 1
        assert got[0].summary == "PV dropout detected."
        assert len(got[0].hypotheses) == 1
        assert got[0].hypotheses[0].support_level == "moderate"
