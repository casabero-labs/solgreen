# ADR-006 — Resultados derivados de calidad de datos

## Contexto

L1 produce lotes de `InverterTelemetrySample` y `PlantFlowSample` sin orden garantizado ni marcación de calidad derivada del análisis temporal. Antes de ejecutar reglas de L2 es necesario establecer el orden canónico, identificar filas duplicadas por timestamp, y detectar huecos respecto al intervalo de muestreo esperado.

El contrato `ValidityFlags` ya existe con la razón `DUPLICATE`. No existe aún un contrato para resultados de análisis de orden, duplicados o huecos.

## Decisión

Se introduce un módulo `solgreen/quality/` con funciones puras que operan sobre secuencias de samples y devuelven resultados tipados. Ninguna función de quality tiene I/O ni acceso a estado global.

### Contratos de resultado

`OrderingResult` — indica si el lote requirió reordenamiento:

```
is_ordered: bool       # True si ya estaba ordenado por timestamp_utc
is_strict: bool        # True si no había timestamps iguales (duplicados)
```

`DuplicateTimestamp` — identifica una fila duplicada:

```
index: int             # posición en la secuencia original (0-based)
timestamp: datetime    # valor duplicado
count: int             # cuántas veces aparece
```

`TemporalGap` — identifica un hueco entre muestras:

```
before_index: int
after_index: int
gap_duration: timedelta
expected_interval: timedelta
gap_ratio: float       # gap_duration / expected_interval (>1 = hueco real)
```

`QualityResult` —聚合 resultado por lote:

```
source_type: SourceType
total_rows: int
is_ordered: bool
has_duplicates: bool
has_gaps: bool
duplicates: tuple[DuplicateTimestamp, ...]
gaps: tuple[TemporalGap, ...]
quality_score: float   # 0.0-1.0 basado en cobertura temporal
```

### Algoritmo de detección de huecos

1. Ordenadar samples por `timestamp_utc`.
2. Para cada par consecutive, calcular `delta = after.timestamp_utc - before.timestamp_utc`.
3. Si `delta > expected_interval * factor` (factor = 1.5 por defecto, configurable), registrar un `TemporalGap`.
4. No se interpola, no se modifica el dataset original.

### Algoritmo de detección de duplicados

1. Detectar grupos de `timestamp_utc` idénticos dentro de un lote.
2. Para cada grupo con `len > 1`, generar un `DuplicateTimestamp` con la posición de cada ejemplar.
3. La primera occurrence se marca como `is_valid=True`; las demás como `is_valid=False` con razón `DUPLICATE`.

### Score de calidad

```
quality_score = 1.0 - max(
    len(gaps) / max(len(samples), 1) * 0.4,
    duplicate_count / max(len(samples), 1) * 0.6,
)
```

No puede ser negativo. Refleja cobertura temporal y presencia de duplicados.

## Consecuencias

- Positivas: funciones puras, testeables sin mocks; resultados tipados y serializables; se introducen como extensión de `QualitySummary` en `ImportBatch` sin romper контрактов existentes.
- Negativas: el análisis de huecos es sensible al intervalo esperado. Un intervalo incorrecto produce falsos positivos. Mitigación: el intervalo se configura vía `PlantProfile.interval_minutes` y se valida que sea > 0.
- Las funciones de quality no escriben nada; la decisión de marcar o filtrar samples queda en capas superiores.

## Alternativas descartadas

- **Marcar directamente sobre el sample** — altera el `ValidityFlags` original y pierde trazabilidad de qué análisis produjo el flag. Se prefiere retornar resultados derivados sin mutar.
- **Detectar huecos durante el parsing** — el parser no tiene contexto del intervalo esperado ni del lote completo; el análisis requiere la secuencia completa.
- **Score agregado en `ImportBatch.quality_summary`** — `QualitySummary` es de L1 y solo contiene recuentos de parsing. Un campo nuevo `QualityResult` se añade en L2 sin modificar el schema de L1.

## Revalidación

Si en L2.2 se requiere interpolación o llenado de huecos, el módulo `quality/` debe crecer con funciones explícitas antes de modificar samples. No se introduce interpolación en L2.1.
