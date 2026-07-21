import json
from datetime import timedelta
from pathlib import Path

from typer.testing import CliRunner

from solgreen import cli as cli_module
from solgreen.cli import app
from solgreen.timeline.join import DEFAULT_TOLERANCE

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
FLOW = str(FIXTURES_DIR / "flow_small.csv")
TELEMETRY = str(FIXTURES_DIR / "telemetry_small.csv")


class TestToleranceValid:
    def test_valid_tolerance_generates_timeline(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT2M30S",
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output

        json_path = tmp_path / f"{Path(FLOW).stem}__{Path(TELEMETRY).stem}.timeline.json"
        md_path = tmp_path / f"{Path(FLOW).stem}__{Path(TELEMETRY).stem}.timeline.md"
        assert json_path.is_file()
        assert md_path.is_file()

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["summary"]["total_samples"] > 0

    def test_tolerance_reaches_join(self, monkeypatch, tmp_path: Path) -> None:
        captured: list[timedelta] = []
        original = cli_module.join_by_tolerance

        def spy(flow_samples, telemetry_samples, *, tolerance=None):
            if tolerance is not None:
                captured.append(tolerance)
            return original(flow_samples, telemetry_samples, tolerance=tolerance)

        monkeypatch.setattr(cli_module, "join_by_tolerance", spy)

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT1M30S",
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert len(captured) == 1
        assert captured[0] == timedelta(minutes=1, seconds=30)


class TestToleranceRejected:
    def test_pt0s_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0S",
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "--tolerance" in result.output
        assert "PT0S" in result.output

    def test_p1m_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "P1M",
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "--tolerance" in result.output

    def test_precision_exceeded_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0.1234567S",
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code != 0
        assert "microseconds" in result.output or "exceeds" in result.output

    def test_invalid_tolerance_no_output_dir_created(self, tmp_path: Path) -> None:
        outdir = tmp_path / "should-not-exist"
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0S",
                "--no-db",
                "-o",
                str(outdir),
            ],
        )
        assert not outdir.exists()

    def test_invalid_tolerance_no_repo_built(self, monkeypatch, tmp_path: Path) -> None:
        called = False

        def _fake_repo(*args, **kwargs):
            nonlocal called
            called = True

        monkeypatch.setattr("solgreen.cli._build_repository", _fake_repo)

        runner = CliRunner()
        runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0S",
                "-o",
                str(tmp_path),
            ],
        )
        assert not called

    def test_invalid_tolerance_no_llm_built(self, monkeypatch, tmp_path: Path) -> None:
        called = False

        def _fake_llm(*args, **kwargs):
            nonlocal called
            called = True

        monkeypatch.setattr("solgreen.cli._build_llm_provider", _fake_llm)

        runner = CliRunner()
        runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0S",
                "-o",
                str(tmp_path),
            ],
        )
        assert not called

    def test_invalid_tolerance_no_parse_single_file(self, monkeypatch, tmp_path: Path) -> None:
        called = False

        def _fake_parse(*args, **kwargs):
            nonlocal called
            called = True
            raise RuntimeError("should not be called")

        monkeypatch.setattr("solgreen.cli._parse_single_file", _fake_parse)

        runner = CliRunner()
        runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--tolerance",
                "PT0S",
                "-o",
                str(tmp_path),
            ],
        )
        assert not called


class TestToleranceDefault:
    def test_default_tolerance_used(self, monkeypatch, tmp_path: Path) -> None:
        captured: list[timedelta] = []
        original = cli_module.join_by_tolerance

        def spy(flow_samples, telemetry_samples, *, tolerance=None):
            if tolerance is not None:
                captured.append(tolerance)
            return original(flow_samples, telemetry_samples, tolerance=tolerance)

        monkeypatch.setattr(cli_module, "join_by_tolerance", spy)

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "--align-with",
                TELEMETRY,
                "--no-db",
                "-o",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert len(captured) == 1
        assert captured[0] == DEFAULT_TOLERANCE


class TestNoAlignWith:
    def test_without_align_with_still_works(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "-f",
                FLOW,
                "-o",
                str(tmp_path),
                "--plant-id",
                "casabero",
                "--no-db",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Parsed 5/5 rows" in result.output
