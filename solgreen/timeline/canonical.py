from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CanonicalSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp_axis: datetime = Field(description="Instante del eje temporal canónico (UTC).")
    source: Literal["flow", "telemetry", "merged"] = Field(
        description="Indica si la muestra proviene solo de flow, solo de telemetry, o ambas fusionadas."
    )
    time_delta: timedelta | None = Field(
        default=None,
        description="Diferencia entre timestamp_axis y el timestamp_utc original de la muestra. None si source=merged con desalineacion cero.",
    )

    flow_potencia_produccion_w: float | None = Field(
        default=None,
        description="Potencia FV instantanea (W). Solo presente si source=flow o source=merged.",
    )
    flow_potencia_consumo_w: float | None = Field(
        default=None,
        description="Consumo total instantaneo (W). Solo presente si source=flow o source=merged.",
    )
    flow_grid_w: float | None = Field(
        default=None,
        description="Potencia en punto de red (W). Signo original SolarMAN — requiere validacion con perfil.",
    )
    flow_soc_pct: float | None = Field(
        default=None,
        description="State of Charge (%). Solo presente si source=flow o source=merged.",
    )
    flow_battery_w: float | None = Field(
        default=None,
        description="Potencia de bateria (W). Signo original SolarMAN — carga negativa, descarga positiva.",
    )

    telemetry_pv_power_w: float | None = Field(
        default=None,
        description="Potencia CC total FV (W). Solo presente si source=telemetry o source=merged.",
    )
    telemetry_grid_power_w: float | None = Field(
        default=None,
        description=(
            "Potencia activa del punto de red medida por telemetria (W). "
            "Valor y convencion de signo originales del inversor — "
            "requiere perfil de planta confirmado antes de derivar "
            "importacion o exportacion. Solo presente si source=telemetry "
            "o source=merged."
        ),
    )
    telemetry_battery_power_w: float | None = Field(
        default=None,
        description="Potencia de bateria segun inversor (W). Solo presente si source=telemetry o source=merged.",
    )
    telemetry_soc_pct: float | None = Field(
        default=None,
        description="SOC (%) desde BMS. Solo presente si source=telemetry o source=merged.",
    )
    telemetry_inverter_state: str | None = Field(
        default=None,
        description="Estado de maquina del inversor. Solo presente si source=telemetry o source=merged.",
    )

    quality_level: Literal["measured", "normalized", "calculated"] = Field(
        default="measured",
        description="Nivel epistemologico de los campos canonicos. calculated requiere conversion de signos.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confianza en la muestra alineada. Reducida cuando time_delta es grande.",
    )
