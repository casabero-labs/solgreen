# ADR-004 — Modelo `signals: dict` para telemetría

## Contexto

`docs/domain/data-dictionary/solarman-inverter-telemetry.md` define 120 columnas. Modelarlas como 120 atributos tipados en `InverterTelemetrySample` produciría una clase con 120 campos `Optional[float]`, difícil de mantener y con baja densidad de información en diffs.

Además, varios campos del archivo real usan la misma columna `Nombre del dispositivo` dos veces (índices 1 y 6), por lo que un modelo con claves únicas por nombre canónico evita colisiones silenciosas.

## Decisión

`InverterTelemetrySample` define:

- metadatos de fila (`timestamp_*`, `device_name`, `serial_redacted`);
- `signals: dict[str, float | str | None]` cuyas claves pertenecen al conjunto canónico definido por `SIGNAL_SPECS` (120 entradas, validado en `field_validator`);
- `validity: ValidityFlags`.

El parser debe traducir cada nombre original SolarMAN al `canonical_name` correspondiente usando `ORIGINAL_ES_TO_CANONICAL`. Cuando un mapeo no exista, el parser rechaza la fila y emite `ValidityReason.PARSE_ERROR`.

## Consecuencias

- Positivas: agregar o versionar una señal no rompe el modelo base; los 120 `SignalSpec` viven en un único módulo auditable; la serialización/parquet round-trip es trivial.
- Negativas: el tipado de campos individuales se pierde en firmas de función. Mitigación: helpers tipados (`get_float(name)`) y catálogo `SIGNAL_SPECS` para descubrir tipo y unidad.
- El validador rechaza claves desconocidas para evitar typos silenciosos.

## Revalidación

Si en L4-L5 se requieren invariantes compilador-tiempo sobre señales prioritarias, extraer una clase `PrioritySignalsMixin` con propiedades `pv1_voltage_v`, `pv2_power_w`, etc., que lean de `self.signals`. No se requiere para L1-L3.