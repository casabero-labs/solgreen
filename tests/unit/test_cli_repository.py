from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from solgreen.cli import (
    _build_repository,
    _run_llm_interpretation,
    app,
)
from solgreen.contracts import ImportBatch
from solgreen.db.repositories.base import Repository
from solgreen.diagnostics.rule import RuleExecution
from solgreen.diagnostics.rule_catalog import RuleCatalog
from solgreen.diagnostics.rule_evaluation import (
    RuleEvaluatorRegistry,
    eligible_fired_rules,
    evaluate_rule_catalog,
)
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


class TestDefensiveRuleEngine:
    def test_cli_persists_no_executions_for_seed_rules(self) -> None:
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
                    str(FIXTURES_DIR.parent / "_out"),
                    "--plant-id",
                    "casabero",
                    "--db-url",
                    "postgresql://test@localhost/test",
                ],
            )
        assert result.exit_code == 0, result.output
        assert mock_repo.executions == {}
        assert "not evaluable" in result.output

    def test_mock_repository_executions_remain_empty_for_seed(self) -> None:
        mock_repo = MockRepository()
        catalog = RuleCatalog()
        registry = RuleEvaluatorRegistry()
        episode = _make_episode()
        outcomes = evaluate_rule_catalog(catalog, episode, registry)
        for outcome in outcomes:
            if outcome.execution is not None:
                mock_repo.executions.setdefault(0, []).append(outcome.execution)
        assert mock_repo.executions == {}

    def test_cli_reports_rules_count(self) -> None:
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
                    str(FIXTURES_DIR.parent / "_out"),
                    "--plant-id",
                    "casabero",
                    "--db-url",
                    "postgresql://test@localhost/test",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "Rules:" in result.output

    def test_cli_no_all_required_signals_evidence(self) -> None:
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
                    str(FIXTURES_DIR.parent / "_out"),
                    "--plant-id",
                    "casabero",
                    "--db-url",
                    "postgresql://test@localhost/test",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "All required signals present" not in result.output


class TestLLMGate:
    def test_provider_not_called_without_eligible_rules(self) -> None:
        class DummyProvider:
            provider_name = "dummy"
            default_model = "dummy-v1"

            def __init__(self) -> None:
                self.called = False

            def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
                self.called = True
                return "{}"

        provider = DummyProvider()
        episode = _make_episode()
        outcomes = evaluate_rule_catalog(RuleCatalog(), episode, RuleEvaluatorRegistry())
        _run_llm_interpretation(
            provider=provider,  # type: ignore[arg-type]
            plant_id="casabero",
            episode=episode,
            outcomes=outcomes,
            episode_id=1,
            repo=MockRepository(),
        )
        assert provider.called is False

    def test_no_llm_interpretation_saved_without_eligible_rules(self) -> None:
        mock_repo = MockRepository()

        class DummyProvider:
            provider_name = "dummy"
            default_model = "dummy-v1"

            def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
                return "{}"

        episode = _make_episode()
        outcomes = evaluate_rule_catalog(RuleCatalog(), episode, RuleEvaluatorRegistry())
        _run_llm_interpretation(
            provider=DummyProvider(),  # type: ignore[arg-type]
            plant_id="casabero",
            episode=episode,
            outcomes=outcomes,
            episode_id=1,
            repo=mock_repo,
        )
        assert mock_repo.interpretations == {}

    def test_cli_shows_llm_skipped_message(self) -> None:
        mock_repo = MockRepository()

        class DummyProvider:
            provider_name = "dummy"
            default_model = "dummy-v1"

            def __init__(self) -> None:
                self.called = False

            def complete(self, prompt: str, *, max_tokens: int = 2000) -> str:
                self.called = True
                return "{}"

        with (
            patch("solgreen.cli._build_repository", return_value=mock_repo),
            patch(
                "solgreen.cli._build_llm_provider",
                return_value=DummyProvider(),
            ),
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
                    str(FIXTURES_DIR.parent / "_out"),
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
        assert "LLM skipped: no validated fired-rule evidence" in result.output

    def test_fired_false_excluded_from_llm_input(self) -> None:
        episode = _make_episode()
        executions = (
            RuleExecution(
                rule_id="R-A",
                rule_version="1.0.0",
                period_start=episode.start,
                period_end=episode.end,
                parameters_used={},
                fired=False,
                evidence=("ignored",),
                input_checksum="abc",
            ),
        )
        assert eligible_fired_rules(executions) == ()

    def test_fired_true_no_evidence_excluded_from_llm_input(self) -> None:
        episode = _make_episode()
        executions = (
            RuleExecution(
                rule_id="R-A",
                rule_version="1.0.0",
                period_start=episode.start,
                period_end=episode.end,
                parameters_used={},
                fired=True,
                evidence=(),
                input_checksum="abc",
            ),
        )
        assert eligible_fired_rules(executions) == ()

    def test_fired_true_with_evidence_eligible(self) -> None:
        episode = _make_episode()
        execution = RuleExecution(
            rule_id="R-A",
            rule_version="1.0.0",
            period_start=episode.start,
            period_end=episode.end,
            parameters_used={},
            fired=True,
            evidence=("real",),
            input_checksum="abc",
        )
        assert eligible_fired_rules((execution,)) == (execution,)

    def test_llm_input_receives_only_eligible_rules(self) -> None:
        from solgreen.diagnostics.llm_input import LLMEpisodeInput

        episode = _make_episode()
        good = RuleExecution(
            rule_id="R-GOOD",
            rule_version="1.0.0",
            period_start=episode.start,
            period_end=episode.end,
            parameters_used={},
            fired=True,
            evidence=("real",),
            input_checksum="abc",
        )
        not_fired = RuleExecution(
            rule_id="R-NOT-FIRED",
            rule_version="1.0.0",
            period_start=episode.start,
            period_end=episode.end,
            parameters_used={},
            fired=False,
            evidence=("no fire",),
            input_checksum="abc",
        )
        eligible = eligible_fired_rules((good, not_fired))
        inp = LLMEpisodeInput(plant_id="casabero", episode=episode, fired_rules=eligible)
        assert inp.fired_rules == (good,)


class TestBuildPromptDoesNotReceiveUnevaluable:
    def test_build_prompt_excludes_unevaluated(self) -> None:
        from solgreen.diagnostics.llm_input import LLMEpisodeInput
        from solgreen.diagnostics.prompt_builder import build_prompt

        episode = _make_episode()
        outcomes = evaluate_rule_catalog(RuleCatalog(), episode, RuleEvaluatorRegistry())
        real_executions = tuple(o.execution for o in outcomes if o.execution is not None)
        eligible = eligible_fired_rules(real_executions)
        assert eligible == ()

        inp = LLMEpisodeInput(plant_id="casabero", episode=episode, fired_rules=eligible)
        prompt = build_prompt(inp)
        assert "Activated rules" not in prompt


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


class TestDbMigrateCommand:
    def test_db_migrate_registered(self) -> None:
        result = runner.invoke(app, ["db", "migrate", "--help"])
        assert result.exit_code == 0
        assert "migrate" in result.stdout.lower()

    def test_db_migrate_help_shows_options(self) -> None:
        result = runner.invoke(app, ["db", "migrate", "--help"])
        assert result.exit_code == 0
        assert "--db-url" in result.stdout
        assert "--migrations-dir" in result.stdout
        assert "--to" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--json" in result.stdout

    def test_db_migrate_json_no_db_url_error(self) -> None:
        result = runner.invoke(app, ["db", "migrate", "--json"])
        assert result.exit_code != 0


class TestDbStatusCommand:
    def test_db_status_registered(self) -> None:
        result = runner.invoke(app, ["db", "status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.stdout.lower()

    def test_db_status_help_shows_options(self) -> None:
        result = runner.invoke(app, ["db", "status", "--help"])
        assert result.exit_code == 0
        assert "--db-url" in result.stdout
        assert "--migrations-dir" in result.stdout
        assert "--json" in result.stdout

    def test_db_status_json_no_db_url_error(self) -> None:
        result = runner.invoke(app, ["db", "status", "--json"])
        assert result.exit_code != 0
