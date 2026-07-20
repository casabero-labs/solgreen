from pathlib import Path

import pytest

from solgreen.contracts import SourceType
from solgreen.importer.detector import detect_format

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(scope="module")
def flow_csv() -> Path:
    return FIXTURES_DIR / "flow_small.csv"


@pytest.fixture(scope="module")
def telemetry_csv() -> Path:
    return FIXTURES_DIR / "telemetry_small.csv"


@pytest.fixture(scope="module")
def garbage_csv() -> Path:
    return FIXTURES_DIR / "garbage.csv"


def test_detect_format_plant_flow_csv(flow_csv: Path) -> None:
    assert detect_format(flow_csv) == SourceType.SOLARMAN_PLANT_FLOW


def test_detect_format_inverter_telemetry_csv(telemetry_csv: Path) -> None:
    assert detect_format(telemetry_csv) == SourceType.SOLARMAN_INVERTER_TELEMETRY


def test_detect_format_unknown_columns_returns_unknown(garbage_csv: Path) -> None:
    assert detect_format(garbage_csv) == SourceType.UNKNOWN


def test_detect_format_unsupported_extension_returns_unknown(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello", encoding="utf-8")
    assert detect_format(file_path) == SourceType.UNKNOWN


def test_detect_format_empty_csv_returns_unknown(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert detect_format(empty) == SourceType.UNKNOWN


def test_detect_format_xlsx(tmp_path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(
        [
            "Nombre del dispositivo",
            "número de serie",
            "Hora actualizada",
            "PV Open Circuit Voltage(V)",
            "Voltaje CC PV1(V)",
            "Grid Code",
            "BUS voltage(V)",
        ]
    )
    xlsx_path = tmp_path / "tiny.xlsx"
    workbook.save(xlsx_path)
    assert detect_format(xlsx_path) == SourceType.SOLARMAN_INVERTER_TELEMETRY
