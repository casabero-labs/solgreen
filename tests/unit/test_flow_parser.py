from pathlib import Path

from openpyxl import Workbook

from solgreen.importer.parsers.registry import iter_with, parse_with
from solgreen.importer.parsers.solarman_flow import (
    _coerce_float,
    _row_to_sample,
    parse_plant_flow,
    parse_plant_flow_csv,
    parse_plant_flow_xlsx,
)
from solgreen.importer.parsers.solarman_flow_csv import SolarmanFlowCsvParser
from solgreen.importer.parsers.solarman_flow_xlsx import SolarmanFlowXlsxParser

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _build_xlsx(path: Path, rows: list[tuple[object, ...]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(
        [
            "Nombre de planta",
            "Hora actualizada",
            "Zona horaria",
            "Potencia de producción(W)",
            "Potencia de consumo(W)",
            "Energía de la red(W)",
            "Poder adquisitivo(W)",
            "Potencia de alimentación(W)",
            "Potencia de la batería(W)",
            "Potencia de carga(W)",
            "Poder de descarga(W)",
            "SoC(%)",
        ]
    )
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_coerce_float_handles_inputs() -> None:
    assert _coerce_float("12.5") == 12.5
    assert _coerce_float("  -3 ") == -3.0
    assert _coerce_float(7) == 7.0
    assert _coerce_float(2.5) == 2.5
    assert _coerce_float(None) is None
    assert _coerce_float("") is None
    assert _coerce_float("   ") is None
    assert _coerce_float("not-a-number") is None
    assert _coerce_float(True) is None


def test_row_to_sample_normalizes_bogota_to_utc() -> None:
    sample = _row_to_sample(
        {
            "Nombre de planta": "casabero",
            "Hora actualizada": "2026-07-17 12:35:00",
            "Zona horaria": "America/Bogota",
            "Potencia de producción(W)": "2800",
            "Potencia de consumo(W)": "900",
            "Energía de la red(W)": "-150",
            "Poder adquisitivo(W)": "120",
            "Potencia de alimentación(W)": "60",
            "Potencia de la batería(W)": "-300",
            "Potencia de carga(W)": "300",
            "Poder de descarga(W)": "0",
            "SoC(%)": "72.5",
        }
    )
    assert sample.timestamp_utc.hour == 17
    assert sample.timestamp_utc.minute == 35
    assert sample.timezone_source == "America/Bogota"
    assert sample.potencia_de_produccion_w == 2800.0
    assert sample.soc_pct == 72.5
    assert sample.energia_de_la_red_w == -150.0
    assert sample.validity.is_valid


def test_row_to_sample_invalid_timestamp_marks_parse_error() -> None:
    sample = _row_to_sample(
        {
            "Nombre de planta": "casabero",
            "Hora actualizada": "",
            "Zona horaria": "America/Bogota",
        }
    )
    assert not sample.validity.is_valid
    from solgreen.contracts import ValidityReason

    assert ValidityReason.PARSE_ERROR in sample.validity.reasons


def test_parse_plant_flow_csv_fixture() -> None:
    path = FIXTURES_DIR / "flow_small.csv"
    samples = parse_plant_flow_csv(path)
    assert len(samples) == 5
    assert all(s.validity.is_valid for s in samples)
    assert samples[0].nombre_de_planta == "casabero"
    assert samples[0].timestamp_utc.hour == 17


def test_parse_plant_flow_xlsx_round_trip(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "flow_small.xlsx"
    _build_xlsx(
        xlsx_path,
        [
            (
                "casabero",
                "2026-07-17 12:35:00",
                "America/Bogota",
                2800.0,
                900.0,
                -150.0,
                120.0,
                60.0,
                -300.0,
                300.0,
                0.0,
                72.5,
            ),
            (
                "casabero",
                "2026-07-17 12:40:00",
                "America/Bogota",
                3100.0,
                950.0,
                200.0,
                50.0,
                0.0,
                100.0,
                0.0,
                100.0,
                71.0,
            ),
        ],
    )
    samples = parse_plant_flow_xlsx(xlsx_path)
    assert len(samples) == 2
    assert samples[0].potencia_de_produccion_w == 2800.0
    assert samples[0].timestamp_utc.hour == 17
    assert samples[1].soc_pct == 71.0


def test_parse_plant_flow_dispatches_by_extension(tmp_path: Path) -> None:
    csv_path = FIXTURES_DIR / "flow_small.csv"
    samples_csv = parse_plant_flow(csv_path)
    assert len(samples_csv) == 5

    xlsx_path = tmp_path / "flow.xlsx"
    _build_xlsx(xlsx_path, [])
    samples_xlsx = parse_plant_flow(xlsx_path)
    assert samples_xlsx == []


def test_parse_with_registry_routes_csv_to_csv_parser() -> None:
    path = FIXTURES_DIR / "flow_small.csv"
    parsed = parse_with(_from_csv(path).source_type, path)
    assert parsed.source_type.value == "solarman_plant_flow"
    assert len(parsed.rows) == 5


def _from_csv(path: Path):
    return SolarmanFlowCsvParser().parse(path)


def test_iter_with_yields_dicts() -> None:
    path = FIXTURES_DIR / "flow_small.csv"
    rows = list(iter_with(_from_csv(path).source_type, path))
    assert len(rows) == 5
    assert "Hora actualizada" in rows[0]
    assert "SoC(%)" in rows[0]


def test_csv_parser_raises_on_missing_headers(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("only,three,cols\n1,2,3\n", encoding="utf-8")
    from solgreen.importer.exceptions import HeaderMismatchError

    with __import__("pytest").raises(HeaderMismatchError):
        parse_plant_flow_csv(bad)


def test_xlsx_parser_raises_on_empty_sheet(tmp_path: Path) -> None:
    workbook = Workbook()
    xlsx = tmp_path / "empty.xlsx"
    workbook.save(xlsx)
    from solgreen.importer.exceptions import CorruptFileError

    with __import__("pytest").raises(CorruptFileError):
        SolarmanFlowXlsxParser().parse(xlsx)
