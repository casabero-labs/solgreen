from __future__ import annotations

from pathlib import Path

from solgreen.contracts import (
    ORIGINAL_ES_TO_CANONICAL,
    InverterTelemetrySample,
    SignalValue,
)
from solgreen.contracts.enums import SignalKind
from solgreen.contracts.validity import ValidityFlags, ValidityReason
from solgreen.core.time import TimestampParseError, parse_timestamp
from solgreen.importer.parsers.solarman_telemetry_csv import SolarmanTelemetryCsvParser
from solgreen.importer.parsers.solarman_telemetry_xlsx import SolarmanTelemetryXlsxParser


def _coerce_signal(value: object, kind: SignalKind) -> SignalValue:
    if value is None:
        return None
    if isinstance(value, bool):
        if kind in {SignalKind.STATUS, SignalKind.TEXT, SignalKind.VERSION}:
            return str(value)
        return None
    if kind in {SignalKind.TEXT, SignalKind.STATUS, SignalKind.VERSION}:
        text = str(value).strip()
        return text or None
    if kind in {SignalKind.TIME}:
        return str(value)
    if kind == SignalKind.COUNT:
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip()
        try:
            return int(text)
        except ValueError:
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


def _redact_serial(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.lower().startswith("redacted:"):
        return text
    return f"redacted:{text[-4:]}" if len(text) >= 4 else "redacted:****"


def _row_to_sample(
    row: dict[str, object],
    observed_to_canonical: dict[str, str],
) -> InverterTelemetrySample:
    raw_ts_obj = row.get("Hora actualizada")
    raw_ts = str(raw_ts_obj).strip() if raw_ts_obj is not None else ""
    serial_raw = row.get("número de serie")

    try:
        original, utc, tz_label = parse_timestamp(raw_ts, None)
        validity = ValidityFlags()
    except TimestampParseError:
        from datetime import datetime

        fallback = datetime(1970, 1, 1)
        sample = InverterTelemetrySample(
            timestamp_original=fallback,
            timestamp_utc=fallback,
            timezone_source=None,
            serial_redacted=_redact_serial(serial_raw),
            validity=ValidityFlags().with_reason(ValidityReason.PARSE_ERROR),
        )
        return sample

    device_name_obj = row.get("Nombre del dispositivo")
    device_name = str(device_name_obj).strip() if device_name_obj is not None else None

    signals: dict[str, SignalValue] = {}
    from solgreen.contracts.inverter_telemetry import SIGNAL_SPECS

    for spec in SIGNAL_SPECS:
        if spec.original_es not in row:
            continue
        canonical = observed_to_canonical.get(spec.original_es)
        if canonical is None:
            continue
        signals[canonical] = _coerce_signal(row.get(spec.original_es), spec.kind)

    return InverterTelemetrySample(
        timestamp_original=original,
        timestamp_utc=utc,
        timezone_source=tz_label,
        device_name=device_name or None,
        serial_redacted=_redact_serial(serial_raw),
        signals=signals,
        validity=validity,
    )


def _build_column_map(observed: tuple[str, ...]) -> dict[str, str]:
    return {
        original: ORIGINAL_ES_TO_CANONICAL[original]
        for original in observed
        if original in ORIGINAL_ES_TO_CANONICAL
    }


def parse_inverter_telemetry_csv(path: Path) -> list[InverterTelemetrySample]:
    parsed = SolarmanTelemetryCsvParser().parse(path)
    column_map = _build_column_map(parsed.columns)
    return [_row_to_sample(row, column_map) for row in parsed.rows]


def parse_inverter_telemetry_xlsx(path: Path) -> list[InverterTelemetrySample]:
    parsed = SolarmanTelemetryXlsxParser().parse(path)
    column_map = _build_column_map(parsed.columns)
    return [_row_to_sample(row, column_map) for row in parsed.rows]


def parse_inverter_telemetry(path: Path) -> list[InverterTelemetrySample]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_inverter_telemetry_csv(path)
    if suffix in {".xlsx", ".xlsm"}:
        return parse_inverter_telemetry_xlsx(path)
    raise ValueError(f"Unsupported extension for telemetry: {path.suffix}")
