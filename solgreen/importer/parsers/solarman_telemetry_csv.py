from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import polars as pl

from solgreen.contracts import SourceType
from solgreen.importer.parsers.base import BaseParser, ParsedFile


class SolarmanTelemetryCsvParser(BaseParser):
    source_type = SourceType.SOLARMAN_INVERTER_TELEMETRY

    def parse(self, path: Path) -> ParsedFile:
        frame = pl.read_csv(path, infer_schema_length=10000)
        return ParsedFile(
            source_type=self.source_type,
            columns=tuple(frame.columns),
            rows=[dict(row) for row in frame.iter_rows(named=True)],
        )

    def iter_rows(self, path: Path) -> Iterator[dict[str, object]]:
        yield from self.parse(path).rows
