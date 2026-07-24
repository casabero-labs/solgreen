from __future__ import annotations

from click import unstyle
from typer.testing import CliRunner

from solgreen.cli import app
from solgreen.integrations.solarman.doctor import (
    CheckStatus,
    DoctorCheck,
    DoctorResult,
)

runner = CliRunner()


def _plain_help(args: list[str]) -> str:
    result = runner.invoke(app, [*args, "--help"], color=False)
    assert result.exit_code == 0, result.output
    return unstyle(result.stdout)


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
        output = _plain_help(["solarman", "doctor"])
        assert "--station-id" in output

    def test_doctor_help_shows_json_option(self) -> None:
        output = _plain_help(["solarman", "doctor"])
        assert "--json" in output

    def test_doctor_help_no_secrets(self) -> None:
        output_lower = _plain_help(["solarman", "doctor"]).lower()
        assert "token" not in output_lower
        assert "password" not in output_lower
        assert "secret" not in output_lower

    def test_doctor_json_ready_true_exit_0(self) -> None:
        from unittest.mock import patch

        mock_result = DoctorResult()
        mock_result.add("config", CheckStatus.PASS, "Configuration valid")

        with patch(
            "solgreen.integrations.solarman.settings.build_settings_from_env"
        ) as mock_settings:
            mock_settings.return_value = None
            with patch(
                "solgreen.integrations.solarman.doctor.run_doctor",
                return_value=mock_result,
            ):
                result = runner.invoke(
                    app,
                    ["solarman", "doctor", "--json"],
                )
                import json

                output = json.loads(result.stdout)
                assert result.exit_code == 0
                assert output["ok"] is True
                assert output["ready"] is True

    def test_doctor_json_ready_false_exit_1(self) -> None:
        from unittest.mock import patch

        mock_result = DoctorResult()
        mock_result.add("config", CheckStatus.PASS, "Configuration valid")
        mock_result.add("auth", CheckStatus.FAIL, "Authentication failed")

        with patch(
            "solgreen.integrations.solarman.settings.build_settings_from_env"
        ) as mock_settings:
            mock_settings.return_value = None
            with patch(
                "solgreen.integrations.solarman.doctor.run_doctor",
                return_value=mock_result,
            ):
                result = runner.invoke(
                    app,
                    ["solarman", "doctor", "--json"],
                )
                import json

                output = json.loads(result.stdout)
                assert result.exit_code == 1
                assert output["ok"] is False
                assert output["ready"] is False

    def test_doctor_json_migrations_pending_exit_1(self) -> None:
        from unittest.mock import patch

        mock_result = DoctorResult()
        mock_result.add("config", CheckStatus.PASS, "Configuration valid")
        mock_result.add("migrations", CheckStatus.FAIL, "2 migration(s) pending: ['003_xxx']")

        with patch(
            "solgreen.integrations.solarman.settings.build_settings_from_env"
        ) as mock_settings:
            mock_settings.return_value = None
            with patch(
                "solgreen.integrations.solarman.doctor.run_doctor",
                return_value=mock_result,
            ):
                result = runner.invoke(
                    app,
                    ["solarman", "doctor", "--json"],
                )
                import json

                output = json.loads(result.stdout)
                assert result.exit_code == 1
                assert output["ok"] is False
                assert output["ready"] is False
