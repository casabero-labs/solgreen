from __future__ import annotations

from pathlib import Path

from solgreen.contracts import PlantFlowSample
from solgreen.contracts.validity import ValidityFlags, ValidityReason
from solgreen.core.time import TimestampParseError, parse_timestamp
from solgreen.importer.exceptions import HeaderMismatchError
from solgreen.importer.parsers.base import PLANT_FLOW_COLUMNS
from solgreen.importer.parsers.solarman_flow_csv import SolarmanFlowCsvParser
from solgreen.importer.parsers.solarman_flow_xlsx import SolarmanFlowXlsxParser


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _row_to_sample(row: dict[str, object]) -> PlantFlowSample:
    raw_ts = row.get("Hora actualizada")
    source_tz = row.get("Zona horaria")
    source_tz_str = str(source_tz).strip() if source_tz is not None else None

    ts_raw_str = str(raw_ts).strip() if raw_ts is not None else ""

    try:
        original, utc, tz_label = parse_timestamp(ts_raw_str, source_tz_str)
    except TimestampParseError:
        from datetime import datetime

        fallback = datetime(1970, 1, 1)
        return PlantFlowSample(
            timestamp_original=fallback,
            timestamp_utc=fallback,
            timezone_source=None,
            validity=ValidityFlags().with_reason(ValidityReason.PARSE_ERROR),
        )

    return PlantFlowSample(
        timestamp_original=original,
        timestamp_utc=utc,
        timezone_source=tz_label,
        nombre_de_planta=str(row["Nombre de planta"]).strip() or None,
        potencia_de_produccion_w=_coerce_float(row.get("Potencia de producción(W)")),
        potencia_de_consumo_w=_coerce_float(row.get("Potencia de consumo(W)")),
        energia_de_la_red_w=_coerce_float(row.get("Energía de la red(W)")),
        poder_adquisitivo_w=_coerce_float(row.get("Poder adquisitivo(W)")),
        potencia_de_alimentacion_w=_coerce_float(row.get("Potencia de alimentación(W)")),
        potencia_de_la_bateria_w=_coerce_float(row.get("Potencia de la batería(W)")),
        potencia_de_carga_w=_coerce_float(row.get("Potencia de carga(W)")),
        poder_de_descarga_w=_coerce_float(row.get("Poder de descarga(W)")),
        soc_pct=_coerce_float(row.get("SoC(%)")),
    )


def parse_plant_flow_csv(path: Path) -> list[PlantFlowSample]:
    parser = SolarmanFlowCsvParser()
    parsed = parser.parse(path)
    _verify_headers(parsed.columns)
    return [_row_to_sample(row) for row in parsed.rows]


def parse_plant_flow_xlsx(path: Path) -> list[PlantFlowSample]:
    parser = SolarmanFlowXlsxParser()
    parsed = parser.parse(path)
    _verify_headers(parsed.columns)
    return [_row_to_sample(row) for row in parsed.rows]


def parse_plant_flow(path: Path) -> list[PlantFlowSample]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_plant_flow_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return parse_plant_flow_xlsx(path)
    raise HeaderMismatchError(path=path, missing=PLANT_FLOW_COLUMNS, unexpected=(path.suffix,))


def _verify_headers(observed: tuple[str, ...]) -> None:
    missing = tuple(c for c in PLANT_FLOW_COLUMNS if c not in observed)
    if missing:
        raise HeaderMismatchError(path=Path("<memory>"), missing=missing, unexpected=())
