from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from solgreen.contracts import SourceType
from solgreen.importer.exceptions import UnsupportedFormatError
from solgreen.importer.parsers.base import BaseParser, ParsedFile
from solgreen.importer.parsers.solarman_flow_csv import SolarmanFlowCsvParser
from solgreen.importer.parsers.solarman_flow_xlsx import SolarmanFlowXlsxParser


def _select_parser(source_type: SourceType, suffix: str) -> BaseParser:
    if source_type == SourceType.SOLARMAN_PLANT_FLOW:
        if suffix == ".csv":
            return SolarmanFlowCsvParser()
        if suffix in {".xlsx", ".xlsm"}:
            return SolarmanFlowXlsxParser()
    raise UnsupportedFormatError(path=Path("<registry>"), observed_columns=(suffix,))


def parse_with(source_type: SourceType, path: Path) -> ParsedFile:
    parser = _select_parser(source_type, path.suffix.lower())
    return parser.parse(path)


def iter_with(source_type: SourceType, path: Path) -> Iterator[dict[str, object]]:
    parser = _select_parser(source_type, path.suffix.lower())
    yield from parser.iter_rows(path)
