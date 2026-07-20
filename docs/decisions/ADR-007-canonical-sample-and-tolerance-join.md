# ADR-007 — CanonicalSample y join por tolerancia para timeline

## Contexto

L1 produce dos lotes independientes: `PlantFlowSample` (flujo de planta, 5 min) e `InverterTelemetrySample` (telemetría técnica, 5 min). Ambos tienen timestamps normalizados a UTC. Antes de calcular métricas o ejecutar reglas, es necesario alinearlos en un eje temporal común que permita comparar señales de ambas fuentes.

FOUNDATIONS.md sección 2 establece que "la tolerancia de unión entre datasets es configurable" y que "un muestreo de cinco minutos representa un punto observado, no un promedio garantizado".

## Decisión

### CanonicalSample

`CanonicalSample` es una muestra alineada que puede provenir de una sola fuente o de ambas fusionadas. No es la fuente original; es la vista alineada.

```
timestamp_axis: datetime          # eje temporal del timeline (UTC)
source: Literal["flow", "telemetry", "merged"]
time_delta: timedelta | None     # diferencia entre timestamp_axis y timestamp_utc de la muestra

# Señales del flujo de planta (todas None si source != flow/merged)
flow_potencia_produccion_w: float | None
flow_potencia_consumo_w: float | None
flow_grid_w: float | None        # signo original SolarMAN
flow_soc_pct: float | None
flow_battery_w: float | None     # signo original SolarMAN

# Señales de telemetría (todas None si source != telemetry/merged)
telemetry_pv_power_w: float | None
telemetry_grid_power_w: float | None
telemetry_battery_power_w: float | None
telemetry_soc_pct: float | None

# Señales canónicas calculadas (disponibles cuando source=merged)
canonical_grid_import_w: float | None   # ≥ 0
canonical_grid_export_w: float | None  # ≥ 0
canonical_battery_charge_w: float | None  # ≥ 0
canonical_battery_discharge_w: float | None  # ≥ 0

quality_level: Literal["measured", "normalized", "calculated"]
confidence: float  # 0.0-1.0
```

### Join por tolerancia

Estrategia: **nearest-match con tolerancia**.

Para cada `PlantFlowSample`:
1. Buscar `InverterTelemetrySample` cuyo `timestamp_utc` esté dentro de `tolerance` del `timestamp_utc` del flow.
2. Si existe exactamente una coincidencia dentro de tolerancia → `source="merged"`, fusionar señales.
3. Si no hay coincidencia → `source="flow"`, señales de telemetría = None.
4. Si hay múltiples coincidencias → usar la más cercana.

Lo mismo a la inversa para samples de telemetría sin match en flow.

Tolerancia por defecto: `timedelta(minutes=2.5)` (mitad del intervalo de muestreo).

### Conversión de signos

FOUNDATIONS.md establece que el modelo canónico usa signos no negativos:
- `grid_import_w ≥ 0` — compra a red
- `grid_export_w ≥ 0` — venta a red
- `battery_charge_w ≥ 0` — carga de batería
- `battery_discharge_w ≥ 0` — descarga de batería

El join **no convierte signos** — eso es responsabilidad de L4 (métricas físicas). CanonicalSample conserva el valor original de cada fuente junto con metadato `quality_level`.

### Lineage

Cada campo de `CanonicalSample` conserva:
- `source` — de dónde viene la señal
- `time_delta` — décalage temporal respecto al eje
- `quality_level` — epistemológico

## Consecuencias

- Positivas: `CanonicalSample` es auto-contenido y serializable; el join no altera samples originales; la estrategia nearest-match es determinista.
- Negativas: si ambas fuentes tienen jitter > tolerancia, el timeline puede estar permanentemente desalineado sin Möglichkeit de corrección. Mitigación: el análisis de calidad de L2 detecta esta situación.
- No se interpola ni se proyecta — solo se alinea.

## Alternativas descartadas

- **Join exacto por timestamp igual** — asume que ambas fuentes muestrean simultáneamente, lo cual no es verdadero en la práctica (jitter de reloj).
- **Interpolación lineal** — ALTERA los datos originales violating ADR-002. Prohibido.
- **Outer join completo** — introduce valores calculados sin transparencia. Se prefiere `source=flow` con `telemetry_*=None` para mantener claridad sobre qué existe realmente.

## Revalidación

Si en L4 se requieren conversiones de signo durante el join (no después), agregar un flag `normalize_signs=True` al join. Requiere revisión humana por impacto en FOUNDATIONS.
