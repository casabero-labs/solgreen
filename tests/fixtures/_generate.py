"""Generate synthetic CSV fixtures for tests and development.

Usage:
    uv run python tests/fixtures/_generate.py

Produces:
    tests/fixtures/flow_small.csv        (5 rows, 12 columns)
    tests/fixtures/telemetry_small.csv   (3 rows, 120 columns)
    tests/fixtures/garbage.csv           (10 rows, 5 random columns)

Values are deterministic (random seed fixed) and contain no private data.
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from solgreen.contracts import SIGNAL_SPECS, SignalKind

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_HEADER: tuple[str, ...] = (
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
)
FLOW_ROW_COUNT = 5
TELEMETRY_ROW_COUNT = 3

STATUS_TEXTS: dict[str, str] = {
    "estado_de_bateria": "charging",
    "estado_de_red": "ok",
    "estado_de_inversor": "running",
    "system_status": "ok",
    "current_state_of_machine": "running",
    "grid_code": "CO-LV-001",
    "battery_charging_type": "pv",
    "battery_1_status": "ok",
    "parallel_mode": "single",
    "generator_operation_mode": "off",
    "upgrade_flag_bit": "0",
}

TEXT_VALUES: dict[str, str] = {
    "nombre_del_dispositivo": "INV-CASABERO-01",
    "nombre_del_dispositivo_b": "INV-CASABERO-01",
    "dispositivo_principal": "INV-CASABERO-01",
    "numero_de_serie_del_dispositivo": "redacted:01HFAZ",
    "bms_version1": "v1.2.3",
    "bms_version2": "v1.2.3",
    "software_version_number_1": "v2.4.1",
    "software_version_number_2": "v2.4.1",
    "hardware_version": "v3.0.0",
    "software_version_number_4": "v2.4.1",
    "minor_version_number": "4",
}

COUNT_VALUES: dict[str, int] = {
    "number_of_parallel_machines": 1,
}


def _synthetic_value(canonical: str, kind: SignalKind, rng: random.Random, row_idx: int) -> object:
    if canonical in STATUS_TEXTS:
        return STATUS_TEXTS[canonical]
    if canonical in TEXT_VALUES:
        return TEXT_VALUES[canonical]
    if canonical in COUNT_VALUES:
        return COUNT_VALUES[canonical]
    if kind == SignalKind.POWER_W:
        return round(rng.uniform(800.0, 4200.0), 1)
    if kind == SignalKind.VOLTAGE_V:
        return round(rng.uniform(220.0, 250.0), 1)
    if kind == SignalKind.CURRENT_A:
        return round(rng.uniform(0.5, 15.0), 2)
    if kind == SignalKind.FREQUENCY_HZ:
        return round(rng.uniform(59.95, 60.05), 2)
    if kind == SignalKind.SOC_PCT:
        return round(60.0 + row_idx * 1.5 + rng.uniform(-2.0, 2.0), 1)
    if kind == SignalKind.TEMPERATURE_C:
        return round(rng.uniform(24.0, 42.0), 1)
    if kind == SignalKind.ENERGY_WH:
        return round(1000.0 + row_idx * 1.234 + rng.uniform(0.0, 0.5), 3)
    if kind == SignalKind.RATIO_PCT:
        return round(rng.uniform(25.0, 75.0), 1)
    if kind == SignalKind.TIME:
        return ""
    if kind == SignalKind.TEXT:
        return "synthetic"
    if kind == SignalKind.STATUS:
        return "ok"
    if kind == SignalKind.VERSION:
        return "v0.0.0"
    if kind == SignalKind.COUNT:
        return 0
    return ""


def _format_timestamp(base: datetime, minute_offset: int) -> str:
    return (base + timedelta(minutes=minute_offset * 5)).strftime("%Y-%m-%d %H:%M:%S")


def write_flow_csv(path: Path, row_count: int = FLOW_ROW_COUNT) -> None:
    rng = random.Random(20260720)
    base_ts = datetime(2026, 7, 17, 12, 35, 0)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(FLOW_HEADER)
        for row_idx in range(row_count):
            writer.writerow(
                (
                    "casabero",
                    _format_timestamp(base_ts, row_idx),
                    "America/Bogota",
                    f"{round(2800 + 600 * (row_idx % 2), 1)}",
                    f"{round(900 + 200 * (row_idx % 2), 1)}",
                    f"{(-1) ** row_idx * round(rng.uniform(120.0, 480.0), 1)}",
                    f"{round(rng.uniform(0.0, 200.0), 1)}",
                    f"{round(rng.uniform(0.0, 800.0), 1)}",
                    f"{(-1) ** row_idx * round(rng.uniform(200.0, 1500.0), 1)}",
                    f"{round(max(0.0, (-1) ** row_idx * rng.uniform(0.0, 1200.0)), 1)}",
                    f"{round(max(0.0, (-1) ** (row_idx + 1) * rng.uniform(0.0, 1500.0)), 1)}",
                    f"{round(70.0 + row_idx * 0.5, 1)}",
                )
            )


def write_telemetry_csv(path: Path, row_count: int = TELEMETRY_ROW_COUNT) -> None:
    rng = random.Random(20260720)
    base_ts = datetime(2026, 7, 19, 9, 0, 0)
    header_es = tuple(spec.original_es for spec in SIGNAL_SPECS)
    time_columns = [i for i, spec in enumerate(SIGNAL_SPECS) if spec.kind == SignalKind.TIME]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header_es)
        for row_idx in range(row_count):
            row: list[object] = []
            ts_value = _format_timestamp(base_ts, row_idx)
            for col_idx, spec in enumerate(SIGNAL_SPECS):
                if col_idx in time_columns:
                    row.append(ts_value)
                else:
                    row.append(_synthetic_value(spec.canonical_name, spec.kind, rng, row_idx))
            writer.writerow(row)


def write_garbage_csv(path: Path) -> None:
    rng = random.Random(0)
    header = ("id", "nota", "valor", "fecha_random", "rare_signal")
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for i in range(10):
            writer.writerow((i, f"note-{i}", rng.randint(0, 100), "2026-01-01", f"x{i}"))


def main() -> None:
    flow = SCRIPT_DIR / "flow_small.csv"
    telemetry = SCRIPT_DIR / "telemetry_small.csv"
    garbage = SCRIPT_DIR / "garbage.csv"

    write_flow_csv(flow)
    write_telemetry_csv(telemetry)
    write_garbage_csv(garbage)

    print(f"Wrote {flow}")
    print(f"Wrote {telemetry}")
    print(f"Wrote {garbage}")


if __name__ == "__main__":
    main()
