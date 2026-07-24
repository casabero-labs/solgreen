from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from solgreen.contracts.enums import SourceType


class DuplicateTimestamp(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0, description="Posicion 0-based en la secuencia original.")
    timestamp: datetime = Field(description="Timestamp UTC duplicado.")
    count: int = Field(ge=2, description="Numero de ejemplares con este timestamp.")
    indices: tuple[int, ...] = Field(description="Todas las posiciones 0-based con este timestamp.")


class TemporalGap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    before_index: int = Field(ge=0, description="Indice del sample anterior al hueco.")
    after_index: int = Field(ge=0, description="Indice del sample posterior al hueco.")
    gap_duration: timedelta = Field(description="Duracion real del hueco.")
    expected_interval: timedelta = Field(description="Intervalo esperado entre samples.")
    gap_ratio: float = Field(
        ge=0.0,
        description="gap_duration / expected_interval. Valores >1 indican hueco real.",
    )


class OrderingInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    was_ordered: bool = Field(
        description="True si los samples ya estaban ordenados por timestamp_utc."
    )
    was_strict: bool = Field(description="True si no habia timestamps duplicados.")


class QualityDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    completeness: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Fraccion de muestras unicas observadas frente a una expectativa "
            "explicita (expected_sample_count). None si no hay expectativa. "
            "Para lote vacio, siempre 0.0."
        ),
    )
    temporal_coverage: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Fraccion de tiempo cubierto dentro del analysis_span. "
            "covered_duration / analysis_span donde covered_duration = "
            "max(analysis_span - missing_duration, 0)."
        ),
    )
    duplicate_integrity: float = Field(
        ge=0.0,
        le=1.0,
        description=("1 - (samples_duplicados / total_samples). Para lote vacio, 1.0."),
    )
    plausibility_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=("Reservado para U1.3 (plausibilidad fisica respaldada por perfil)."),
    )
    consistency_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=("Reservado para U1.4 (consistencia entre fuentes)."),
    )


class QualityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_type: SourceType
    total_rows: int = Field(ge=0)
    ordering: OrderingInfo = Field(description="Info de ordenamiento.")
    duplicates: tuple[DuplicateTimestamp, ...] = Field(
        default_factory=tuple, description="Grupos de timestamps duplicados."
    )
    gaps: tuple[TemporalGap, ...] = Field(
        default_factory=tuple, description="Huecos detectados respecto al intervalo esperado."
    )
    quality_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Score global 0.0-1.0 derivado de las dimensiones no-None. "
            "Para lote vacio es 0.0. Campo Pydantic serializado, no property."
        ),
    )
    dimensions: QualityDimensions = Field(description="Dimensiones separadas de calidad.")

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicates or self.gaps)
