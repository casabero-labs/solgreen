from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(description="Descripción de la hipótesis.")
    support_level: Literal["strong", "moderate", "weak"] = Field(
        description="Nivel de soporte evidencial."
    )
    evidence_refs: tuple[int, ...] = Field(
        default=(),
        description="Índices (0-based) de las evidencias que soportan esta hipótesis.",
    )


class LLMInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="Resumen del episodio en 1-3 oraciones.")
    hypotheses: tuple[Hypothesis, ...] = Field(
        default=(),
        description="Hipótesis ordenadas por support_level (strong primero).",
    )
    alternatives: tuple[str, ...] = Field(
        default=(),
        description="Explicaciones alternativas consideradas.",
    )
    missing_info: tuple[str, ...] = Field(
        default=(),
        description="Información faltante para un diagnóstico más preciso.",
    )
    suggested_actions: tuple[str, ...] = Field(
        default=(),
        description="Acciones sugeridas para el operador.",
    )
    warnings: tuple[str, ...] = Field(
        default=(),
        description="Advertencias de seguridad o operación.",
    )
    prohibited_claims: tuple[str, ...] = Field(
        default=(),
        description="Siempre vacío. El LLM nunca declara causas confirmadas. Validado por llm_validator.",
    )
    provider: str = Field(description="Proveedor del LLM usado.")
    model: str = Field(description="Modelo del LLM usado.")
    prompt_version: str = Field(description="Versión del prompt usado.")
    input_hash: str = Field(description="SHA-256 del input enviado al LLM.")
