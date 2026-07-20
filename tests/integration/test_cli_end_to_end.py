import json
from pathlib import Path

from typer.testing import CliRunner

from solgreen.cli import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_cli_import_flow_writes_reports(tmp_path: Path) -> None:
    runner = CliRunner()
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
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Parsed 5/5 rows" in result.output
    json_path = tmp_path / "flow_small.import.json"
    md_path = tmp_path / "flow_small.import.md"
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["batch"]["plant_id"] == "casabero"
    assert payload["batch"]["metadata"]["source_type"] == "solarman_plant_flow"
    assert payload["parser_status"] == "ok"


def test_cli_import_telemetry_writes_reports(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "import",
            "-f",
            str(FIXTURES_DIR / "telemetry_small.csv"),
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Parsed 3/3 rows" in result.output
    payload = json.loads((tmp_path / "telemetry_small.import.json").read_text(encoding="utf-8"))
    assert payload["batch"]["metadata"]["source_type"] == "solarman_inverter_telemetry"


def test_cli_import_unknown_format_fails(tmp_path: Path) -> None:
    runner = CliRunner()
    bad = tmp_path / "garbage.csv"
    bad.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    result = runner.invoke(app, ["import", "-f", str(bad), "-o", str(tmp_path)])
    assert result.exit_code != 0
