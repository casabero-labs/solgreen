from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from solgreen.contracts.enums import SourceType


class DuplicateTimestamp(BaseModel):
    model_config = {"frozen": True}

    index: int = Field(ge=0, description="Posicion 0-based en la secuencia original.")
    timestamp: datetime = Field(description="Timestamp UTC duplicado.")
    count: int = Field(ge=2, description="Numero de ejemplares con este timestamp.")
    indices: tuple[int, ...] = Field(
        description="Todas las posiciones 0-based con este timestamp."
    )


class TemporalGap(BaseModel):
    model_config = {"frozen": True}

    before_index: int = Field(ge=0, description="Indice del sample anterior al hueco.")
    after_index: int = Field(ge=0, description="Indice del sample posterior al hueco.")
    gap_duration: timedelta = Field(description="Duracion real del hueco.")
    expected_interval: timedelta = Field(description="Intervalo esperado entre samples.")
    gap_ratio: float = Field(
        ge=0.0,
        description="gap_duration / expected_interval. Valores >1 indican hueco real.",
    )


class OrderingInfo(BaseModel):
    model_config = {"frozen": True}

    was_ordered: bool = Field(
        description="True si los samples ya estaban ordenados por timestamp_utc."
    )
    was_strict: bool = Field(
        description="True si no habia timestamps duplicados."
    )


class QualityResult(BaseModel):
    model_config = {"frozen": True}

    source_type: SourceType
    total_rows: int = Field(ge=0)
    ordering: OrderingInfo = Field(description="Info de ordenamiento.")
    duplicates: tuple[DuplicateTimestamp, ...] = Field(
        default_factory=tuple,
        description="Grupos de timestamps duplicados."
    )
    gaps: tuple[TemporalGap, ...] = Field(
        default_factory=tuple,
        description="Huecos detectados respecto al intervalo esperado."
    )
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="Score de calidad 0.0-1.0 basado en cobertura temporal y duplicados."
    )

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicates or self.gaps)
