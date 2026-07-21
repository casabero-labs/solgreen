from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from solgreen.diagnostics.severity import SeverityLevel


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(description="Identificador único de la regla (ej. DATA-001).")
    version: str = Field(default="1.0.0", description="Versión semántica de la regla.")
    name: str = Field(description="Nombre corto de la regla.")
    category: Literal["data", "battery", "pv", "grid", "inverter", "correlation"] = Field(
        description="Categoría funcional de la regla."
    )
    question: str = Field(description="Pregunta técnica que la regla responde.")
    signals_required: tuple[str, ...] = Field(
        description="Señales necesarias para evaluar la regla."
    )
    signals_optional: tuple[str, ...] = Field(
        default=(),
        description="Señales opcionales que enriquecen la evaluación.",
    )
    base_severity: SeverityLevel = Field(
        description="Severidad por defecto cuando la regla se activa."
    )
    parameters: dict[str, float | int | str] = Field(
        default_factory=dict,
        description="Parámetros umbral configurables por perfil de planta.",
    )
    known_false_positives: tuple[str, ...] = Field(
        default=(),
        description="Descripciones de falsos positivos conocidos.",
    )


class RuleExecution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(description="ID de la regla evaluada.")
    rule_version: str = Field(description="Versión de la regla evaluada.")
    period_start: datetime = Field(description="Inicio del período evaluado (UTC).")
    period_end: datetime = Field(description="Fin del período evaluado (UTC).")
    parameters_used: dict[str, float | int | str] = Field(
        description="Parámetros efectivamente usados en la evaluación."
    )
    fired: bool = Field(description="True si la regla se activó.")
    evidence: tuple[str, ...] = Field(
        default=(),
        description="Evidencias producidas por la evaluación.",
    )
    input_checksum: str = Field(description="SHA-256 de los inputs usados para la evaluación.")
