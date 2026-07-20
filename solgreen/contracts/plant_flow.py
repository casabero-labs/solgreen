from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from solgreen.contracts.validity import ValidityFlags


class PlantFlowSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp_original: datetime = Field(description="Timestamp crudo del archivo.")
    timestamp_utc: datetime = Field(description="Mismo instante normalizado a UTC.")
    timezone_source: str | None = Field(
        default=None,
        description="Etiqueta de zona horaria original (ej. America/Bogota, naive, UTC).",
    )

    nombre_de_planta: str | None = None

    potencia_de_produccion_w: float | None = Field(
        default=None,
        description="Producción FV instantánea (W).",
    )
    potencia_de_consumo_w: float | None = Field(
        default=None,
        description="Consumo total instantáneo (W).",
    )
    energia_de_la_red_w: float | None = Field(
        default=None,
        description="Potencia en el punto de red (W). Signo requiere validación con perfil de planta.",
    )
    poder_adquisitivo_w: float | None = Field(
        default=None,
        description="Marcada como no autoridad por docs/domain/data-dictionary/solarman-plant-flow.md.",
    )
    potencia_de_alimentacion_w: float | None = Field(
        default=None,
        description="Marcada como no autoridad por docs/domain/data-dictionary/solarman-plant-flow.md.",
    )
    potencia_de_la_bateria_w: float | None = Field(
        default=None,
        description="Potencia instantánea de batería. Signo canónico se calcula en parser (carga>=0, descarga>=0).",
    )
    potencia_de_carga_w: float | None = None
    poder_de_descarga_w: float | None = None
    soc_pct: float | None = Field(default=None, ge=0.0, le=100.0)

    validity: ValidityFlags = Field(default_factory=ValidityFlags)
