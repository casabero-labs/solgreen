from pathlib import Path

from openpyxl import Workbook

from solgreen.contracts import ORIGINAL_ES_TO_CANONICAL, SIGNAL_SPECS, ValidityReason
from solgreen.contracts.enums import SignalKind
from solgreen.importer.parsers.registry import iter_with, parse_with
from solgreen.importer.parsers.solarman_telemetry import (
    _coerce_signal,
    _redact_serial,
    _row_to_sample,
    parse_inverter_telemetry,
    parse_inverter_telemetry_csv,
    parse_inverter_telemetry_xlsx,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _build_telemetry_xlsx(path: Path, rows: list[list[object]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(list(ORIGINAL_ES_TO_CANONICAL.keys()))
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_redact_serial_handles_short_and_long_inputs() -> None:
    assert _redact_serial(None) is None
    assert _redact_serial("") is None
    assert _redact_serial("   ") is None
    assert _redact_serial("ABC123XYZ789") == "redacted:Z789"
    assert _redact_serial("AB") == "redacted:****"
    assert _redact_serial("redacted:1234") == "redacted:1234"


def test_coerce_signal_per_kind() -> None:
    assert _coerce_signal(None, SignalKind.POWER_W) is None
    assert _coerce_signal("", SignalKind.POWER_W) is None
    assert _coerce_signal("123.4", SignalKind.POWER_W) == 123.4
    assert _coerce_signal(7, SignalKind.POWER_W) == 7.0
    assert _coerce_signal(True, SignalKind.POWER_W) is None
    assert _coerce_signal(True, SignalKind.STATUS) == "True"
    assert _coerce_signal("running", SignalKind.STATUS) == "running"
    assert _coerce_signal("3", SignalKind.COUNT) == 3
    assert _coerce_signal("v1.0", SignalKind.VERSION) == "v1.0"
    assert _coerce_signal("12:35:00", SignalKind.TIME) == "12:35:00"


def test_row_to_sample_maps_known_signals() -> None:
    row = {
        "Hora actualizada": "2026-07-19 09:00:00",
        "Nombre del dispositivo": "INV-X",
        "número de serie": "SN12345678",
        "Voltaje CC PV1(V)": "312.4",
        "SoC(%)": "72.0",
        "Current state of machine": "running",
    }
    sample = _row_to_sample(row, ORIGINAL_ES_TO_CANONICAL)
    assert sample.validity.is_valid
    assert sample.timestamp_utc.hour == 9
    assert sample.timezone_source == "naive"
    assert sample.serial_redacted == "redacted:5678"
    assert sample.device_name == "INV-X"
    assert sample.get_float("voltaje_cc_pv1_v") == 312.4
    assert sample.get_float("soc_pct") == 72.0
    assert sample.signals["current_state_of_machine"] == "running"


def test_row_to_sample_invalid_timestamp_marks_parse_error() -> None:
    sample = _row_to_sample(
        {"Hora actualizada": "", "número de serie": "ABC"},
        ORIGINAL_ES_TO_CANONICAL,
    )
    assert not sample.validity.is_valid
    assert ValidityReason.PARSE_ERROR in sample.validity.reasons


def test_parse_inverter_telemetry_csv_fixture() -> None:
    path = FIXTURES_DIR / "telemetry_small.csv"
    samples = parse_inverter_telemetry_csv(path)
    assert len(samples) == 3
    for s in samples:
        assert s.validity.is_valid
        assert s.serial_redacted
        assert s.serial_redacted.startswith("redacted:")
        assert "current_state_of_machine" in s.signals
        assert "voltaje_cc_pv1_v" in s.signals
        assert len(s.signals) == len(
            {sp.original_es for sp in SIGNAL_SPECS if sp.original_es in _first_row_keys(path)}
        )


def _first_row_keys(path: Path) -> set[str]:
    import csv

    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
    return set(header)


def test_parse_inverter_telemetry_xlsx_round_trip(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "tiny_telemetry.xlsx"
    full_row: list[object] = [None] * len(ORIGINAL_ES_TO_CANONICAL)
    headers = list(ORIGINAL_ES_TO_CANONICAL.keys())
    full_row[headers.index("Nombre del dispositivo")] = "INV-X"
    full_row[headers.index("número de serie")] = "SN1234ABCD"
    full_row[headers.index("Hora actualizada")] = "2026-07-19 09:00:00"
    full_row[headers.index("PV Open Circuit Voltage(V)")] = 350.0
    full_row[headers.index("Voltaje CC PV1(V)")] = 312.0
    full_row[headers.index("SoC(%)")] = 71.0
    full_row[headers.index("Current state of machine")] = "running"
    _build_telemetry_xlsx(xlsx_path, [full_row])
    samples = parse_inverter_telemetry_xlsx(xlsx_path)
    assert len(samples) == 1
    s = samples[0]
    assert s.get_float("pv_open_circuit_voltage_v") == 350.0
    assert s.get_float("voltaje_cc_pv1_v") == 312.0
    assert s.get_float("soc_pct") == 71.0
    assert s.serial_redacted == "redacted:ABCD"


def test_parse_inverter_telemetry_dispatches_by_extension() -> None:
    csv_path = FIXTURES_DIR / "telemetry_small.csv"
    assert len(parse_inverter_telemetry(csv_path)) == 3

    class _NoMatch:
        suffix = ".txt"

    from solgreen.importer.parsers.solarman_telemetry import parse_inverter_telemetry as _p

    try:
        _p(Path("anything.txt"))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for .txt")


def test_registry_routes_telemetry() -> None:
    from solgreen.importer.detector import detect_format

    path = FIXTURES_DIR / "telemetry_small.csv"
    source_type = detect_format(path)
    parsed = parse_with(source_type, path)
    assert parsed.source_type.value == "solarman_inverter_telemetry"
    assert len(parsed.rows) == 3
    assert list(iter_with(source_type, path))
