from __future__ import annotations

from typer.testing import CliRunner

from solgreen.cli import app
from solgreen.integrations.solarman.doctor import (
    CheckStatus,
    DoctorCheck,
    DoctorResult,
)

runner = CliRunner()


class TestDoctorCheck:
    def test_to_dict(self) -> None:
        check = DoctorCheck(name="test", status=CheckStatus.PASS, detail="ok")
        d = check.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "PASS"
        assert d["detail"] == "ok"

    def test_to_dict_hides_empty_data(self) -> None:
        check = DoctorCheck(name="test", status=CheckStatus.PASS)
        d = check.to_dict()
        assert "data" not in d

    def test_to_dict_includes_data(self) -> None:
        check = DoctorCheck(name="test", status=CheckStatus.PASS, data={"key": "value"})
        d = check.to_dict()
        assert d["data"] == {"key": "value"}


class TestDoctorResult:
    def test_ready_true_when_all_pass_or_warn(self) -> None:
        result = DoctorResult()
        result.add("a", CheckStatus.PASS)
        result.add("b", CheckStatus.WARN)
        assert result.ready is True

    def test_ready_false_when_any_fail(self) -> None:
        result = DoctorResult()
        result.add("a", CheckStatus.PASS)
        result.add("b", CheckStatus.FAIL)
        assert result.ready is False

    def test_to_dict_summary(self) -> None:
        result = DoctorResult()
        result.add("a", CheckStatus.PASS)
        result.add("b", CheckStatus.WARN)
        result.add("c", CheckStatus.FAIL)
        d = result.to_dict()
        assert d["summary"]["total"] == 3
        assert d["summary"]["pass"] == 1
        assert d["summary"]["warn"] == 1
        assert d["summary"]["fail"] == 1


class TestDoctorCli:
    def test_doctor_command_registered(self) -> None:
        result = runner.invoke(app, ["solarman", "doctor", "--help"])
        assert result.exit_code == 0
        assert "doctor" in result.stdout.lower()

    def test_doctor_help_shows_station_id_option(self) -> None:
        result = runner.invoke(app, ["solarman", "doctor", "--help"])
        assert result.exit_code == 0
        assert "--station-id" in result.stdout

    def test_doctor_help_shows_json_option(self) -> None:
        result = runner.invoke(app, ["solarman", "doctor", "--help"])
        assert result.exit_code == 0
        assert "--json" in result.stdout

    def test_doctor_help_no_secrets(self) -> None:
        result = runner.invoke(app, ["solarman", "doctor", "--help"])
        output_lower = result.stdout.lower()
        assert "token" not in output_lower
        assert "password" not in output_lower
        assert "secret" not in output_lower
