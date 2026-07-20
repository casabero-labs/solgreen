from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from solgreen.diagnostics.rule import RuleExecution
from solgreen.timeline.episode import CanonicalEpisode


class LLMEpisodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plant_id: str = Field(description="Identificador de la planta.")
    episode: CanonicalEpisode = Field(description="Episodio a interpretar.")
    fired_rules: tuple[RuleExecution, ...] = Field(
        default=(),
        description="Reglas que se activaron (fired=True) en este episodio.",
    )
    data_quality_summary: str = Field(
        default="",
        description="Resumen de la calidad de datos del período.",
    )
    manual_excerpts: tuple[str, ...] = Field(
        default=(),
        description="Extractos autorizados de manuales de equipo.",
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Límite máximo de tokens en la respuesta del LLM.",
    )
