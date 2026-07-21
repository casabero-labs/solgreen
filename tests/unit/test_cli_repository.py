from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from solgreen.cli import (
    _build_repository,
    _episode_checksum,
    _evaluate_rules,
    app,
)
from solgreen.contracts import ImportBatch
from solgreen.db.repositories.base import Repository
from solgreen.diagnostics.rule_catalog import RuleCatalog
from solgreen.timeline.canonical import CanonicalSample
from solgreen.timeline.episode import CanonicalEpisode

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
runner = CliRunner()


class MockRepository(Repository):
    """In-memory mock for testing."""

    def __init__(self) -> None:
        self.batches: dict[Any, ImportBatch] = {}
        self.samples: dict[Any, list[CanonicalSample]] = {}
        self.episodes: dict[Any, list[CanonicalEpisode]] = {}
        self.executions: dict[int, list[Any]] = {}
        self.interpretations: dict[int, list[Any]] = {}
        self._episode_counter = 0

    def save_import_batch(self, batch: ImportBatch) -> None:
        self.batches[batch.id] = batch

    def get_import_batch(self, batch_id: Any) -> ImportBatch | None:
        return self.batches.get(batch_id)

    def list_import_batches(self, plant_id: str) -> list[ImportBatch]:
        return [b for b in self.batches.values() if b.plant_id == plant_id]

    def save_canonical_samples(self, batch_id: Any, samples: list[CanonicalSample]) -> None:
        self.samples[batch_id] = samples

    def get_canonical_samples(self, batch_id: Any) -> list[CanonicalSample]:
        return self.samples.get(batch_id, [])

    def save_canonical_episode(self, batch_id: Any, episode: CanonicalEpisode) -> int:
        self._episode_counter += 1
        ep_id = self._episode_counter
        self.episodes.setdefault(batch_id, []).append(episode)
        return ep_id

    def get_canonical_episodes(self, batch_id: Any) -> list[CanonicalEpisode]:
        return self.episodes.get(batch_id, [])

    def save_rule_execution(self, episode_id: int, execution: Any) -> None:
        self.executions.setdefault(episode_id, []).append(execution)

    def get_rule_executions(self, episode_id: int) -> list[Any]:
        return self.executions.get(episode_id, [])

    def save_llm_interpretation(self, episode_id: int, interpretation: Any) -> None:
        self.interpretations.setdefault(episode_id, []).append(interpretation)

    def get_llm_interpretations(self, episode_id: int) -> list[Any]:
        return self.interpretations.get(episode_id, [])


def _make_episode(
    start: datetime | None = None,
    end: datetime | None = None,
    signals: dict[str, float] | None = None,
) -> CanonicalEpisode:
    if start is None:
        start = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    if end is None:
        end = start + timedelta(hours=1)
    return CanonicalEpisode(
        episode_type="pv_production",
        start=start,
        end=end,
        duration=end - start,
        sample_count=12,
        coverage_pct=95.0,
        source_summary="merged",
        signals=signals
        if signals is not None
        else {"flow_soc_pct": 75.0, "telemetry_pv_power_w": 3500.0},
    )


def test_build_repository_none_when_no_url() -> None:
    assert _build_repository(None) is None


def test_build_repository_returns_repo_when_url() -> None:
    with patch("solgreen.db.repositories.psycopg2_repo.psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        repo = _build_repository("postgresql://user:pass@localhost:5432/test")
    assert isinstance(repo, Repository)


def test_episode_checksum_consistent() -> None:
    ep = _make_episode()
    c1 = _episode_checksum(ep)
    c2 = _episode_checksum(ep)
    assert c1 == c2
    assert len(c1) == 64  # SHA-256 hex


def test_episode_checksum_changes_with_different_episode() -> None:
    ep1 = _make_episode(start=datetime(2025, 1, 1, 10, 0, tzinfo=UTC))
    ep2 = _make_episode(start=datetime(2025, 1, 1, 11, 0, tzinfo=UTC))
    assert _episode_checksum(ep1) != _episode_checksum(ep2)


def test_evaluate_rules_returns_execution_per_rule() -> None:
    catalog = RuleCatalog()
    episode = _make_episode()
    executions = _evaluate_rules(catalog, episode)
    assert len(executions) == len(catalog.list_rules())


def test_evaluate_rules_fires_when_signals_present() -> None:
    catalog = RuleCatalog()
    signals = {
        "flow_soc_pct": 15.0,  # BAT-001 needs this
        "telemetry_pv_power_w": 3500.0,  # PV-001 needs this
        "telemetry_grid_power_w": 1000.0,  # GRID-003 needs this
        "timestamp_axis": 1.0,  # DATA-001 needs this (sort of)
    }
    episode = _make_episode(signals=signals)
    executions = _evaluate_rules(catalog, episode)
    fired_ids = {e.rule_id for e in executions if e.fired}
    assert "BAT-001" in fired_ids
    assert "PV-001" in fired_ids
    assert "GRID-003" in fired_ids


def test_evaluate_rules_not_fires_when_signals_missing() -> None:
    catalog = RuleCatalog()
    episode = _make_episode(signals={})
    executions = _evaluate_rules(catalog, episode)
    fired_ids = {e.rule_id for e in executions if e.fired}
    assert len(fired_ids) == 0


def test_evaluate_rules_all_have_checksum() -> None:
    catalog = RuleCatalog()
    episode = _make_episode()
    executions = _evaluate_rules(catalog, episode)
    for ex in executions:
        assert len(ex.input_checksum) == 64


def test_cli_import_no_db_persists_nothing(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "import",
            "-f",
            str(FIXTURES_DIR / "flow_small.csv"),
            "-o",
            str(tmp_path),
            "--plant-id",
            "casabero",
            "--no-db",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Parsed 5/5 rows" in result.output
    assert "Persisted" not in result.output


def test_cli_import_with_db_url_persists(tmp_path: Path) -> None:
    mock_repo = MockRepository()
    with patch("solgreen.cli._build_repository", return_value=mock_repo):
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                str(FIXTURES_DIR / "flow_small.csv"),
                "-o",
                str(tmp_path),
                "--plant-id",
                "casabero",
                "--db-url",
                "postgresql://test@localhost/test",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "Persisted batch" in result.output
    assert len(mock_repo.batches) == 1


def test_cli_import_align_with_db_persists_episodes(tmp_path: Path) -> None:
    mock_repo = MockRepository()
    with patch("solgreen.cli._build_repository", return_value=mock_repo):
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                str(FIXTURES_DIR / "flow_small.csv"),
                "--align-with",
                str(FIXTURES_DIR / "telemetry_small.csv"),
                "-o",
                str(tmp_path),
                "--plant-id",
                "casabero",
                "--db-url",
                "postgresql://test@localhost/test",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "episodes:" in result.output
    assert "persisted to database" in result.output
    assert len(mock_repo.batches) == 2
    assert len(mock_repo.samples) >= 1


def test_cli_import_align_with_llm_provider(tmp_path: Path) -> None:
    mock_repo = MockRepository()

    class DummyProvider:
        provider_name = "dummy"
        default_model = "dummy-v1"

        def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
            import json

            return json.dumps(
                {
                    "summary": "Test LLM summary.",
                    "hypotheses": [],
                    "alternatives": [],
                    "missing_info": [],
                    "suggested_actions": [],
                    "warnings": [],
                }
            )

    dummy = DummyProvider()
    with (
        patch("solgreen.cli._build_repository", return_value=mock_repo),
        patch("solgreen.cli._build_llm_provider", return_value=dummy),
    ):
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                str(FIXTURES_DIR / "flow_small.csv"),
                "--align-with",
                str(FIXTURES_DIR / "telemetry_small.csv"),
                "-o",
                str(tmp_path),
                "--plant-id",
                "casabero",
                "--db-url",
                "postgresql://test@localhost/test",
                "--llm-provider",
                "dummy",
                "--llm-api-key",
                "test-key",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "LLM provider: dummy" in result.output
    assert "LLM:" in result.output
