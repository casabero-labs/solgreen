from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import polars as pl

from solgreen.contracts import SourceType
from solgreen.importer.exceptions import HeaderMismatchError
from solgreen.importer.parsers.base import PLANT_FLOW_COLUMNS, BaseParser, ParsedFile


class SolarmanFlowCsvParser(BaseParser):
    source_type = SourceType.SOLARMAN_PLANT_FLOW

    def parse(self, path: Path) -> ParsedFile:
        frame = pl.read_csv(path, infer_schema_length=10000)
        observed = tuple(frame.columns)
        self._validate_headers(observed)
        return ParsedFile(
            source_type=self.source_type,
            columns=observed,
            rows=[self._row_to_dict(row) for row in frame.iter_rows(named=True)],
        )

    def iter_rows(self, path: Path) -> Iterator[dict[str, object]]:
        frame = pl.read_csv(path, infer_schema_length=10000)
        for row in frame.iter_rows(named=True):
            yield self._row_to_dict(row)

    @staticmethod
    def _validate_headers(observed: tuple[str, ...]) -> None:
        missing = tuple(c for c in PLANT_FLOW_COLUMNS if c not in observed)
        if missing:
            raise HeaderMismatchError(path=Path("<csv>"), missing=missing, unexpected=())

    @staticmethod
    def _row_to_dict(row: dict[str, object]) -> dict[str, object]:
        return dict(row)
