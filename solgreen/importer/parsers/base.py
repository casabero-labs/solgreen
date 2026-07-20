from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from solgreen.contracts import SourceType

PLANT_FLOW_COLUMNS: tuple[str, ...] = (
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


@dataclass
class ParsedFile:
    source_type: SourceType
    columns: tuple[str, ...]
    rows: list[dict[str, object]] = field(default_factory=list)


class BaseParser(ABC):
    source_type: SourceType

    @abstractmethod
    def parse(self, path: Path) -> ParsedFile: ...

    def iter_rows(self, path: Path) -> Iterator[dict[str, object]]:
        yield from self.parse(path).rows
