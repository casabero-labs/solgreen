from __future__ import annotations

import os
from pathlib import Path

import pytest

from solgreen.db import get_connection
from solgreen.db.repositories.psycopg2_repo import Psycopg2Repository

DB_URL = os.environ.get("SOLGREEN_DATABASE_URL")
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

pytestmark = pytest.mark.integration


def _has_db() -> bool:
    if DB_URL is None:
        return False
    try:
        conn = get_connection(DB_URL)
        conn.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_db(), reason="No SOLGREEN_DATABASE_URL set")
def test_schema_exists() -> None:
    conn = get_connection(DB_URL)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        tables = {row[0] for row in cur.fetchall()}
    conn.close()
    expected = {
        "import_batches",
        "canonical_samples",
        "canonical_episodes",
        "rule_executions",
        "llm_interpretations",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


@pytest.mark.skipif(not _has_db(), reason="No SOLGREEN_DATABASE_URL set")
def test_full_pipeline_smoke() -> None:
    from typer.testing import CliRunner

    from solgreen.cli import app

    runner = CliRunner()
    conn = get_connection(DB_URL)
    repo = Psycopg2Repository(conn)

    result = runner.invoke(
        app,
        [
            "import",
            "-f",
            str(FIXTURES_DIR / "flow_small.csv"),
            "--align-with",
            str(FIXTURES_DIR / "telemetry_small.csv"),
            "-o",
            str(Path("/tmp/solgreen_smoke")),
            "--plant-id",
            "smoke-test",
            "--db-url",
            DB_URL,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "episodes:" in result.output
    assert "persisted to database" in result.output

    batches = repo.list_import_batches("smoke-test")
    assert len(batches) >= 2
    batch_id = batches[0].id

    samples = repo.get_canonical_samples(batch_id)
    assert len(samples) > 0

    episodes = repo.get_canonical_episodes(batch_id)
    assert len(episodes) > 0

    for ep in episodes:
        ep_id = repo.save_canonical_episode(batch_id, ep)
        execs = repo.get_rule_executions(ep_id)
        assert isinstance(execs, list)

    conn.close()
