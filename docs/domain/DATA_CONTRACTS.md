# Contratos de datos

## Entidades principales

### `ImportBatch`

- `id`
- `plant_id`
- `source_type`
- `original_filename`
- `sha256`
- `byte_size`
- `parser_id`
- `parser_version`
- `imported_at`
- `status`
- `quality_summary`

### `PlantFlowSample`

- timestamp original y UTC;
- producción FV;
- consumo;
- importación y exportación;
- carga y descarga de batería;
- SOC;
- banderas de validez y procedencia.

### `InverterTelemetrySample`

- señales MPPT;
- salida AC;
- red L1/L2;
- carga L1/L2;
- batería;
- BUS;
- temperaturas;
- estados;
- versiones;
- acumulados.

### `CanonicalSample`

Vista temporal alineada. Cada campo conserva:

- valor;
- unidad;
- fuente;
- timestamp de fuente;
- diferencia temporal respecto al eje;
- calidad;
- transformación aplicada.

### `RuleExecution`

- regla y versión;
- periodo;
- parámetros;
- resultado;
- evidencias;
- checksum de inputs.

### `Episode`

- tipo;
- inicio, pico y fin;
- severidad;
- confianza;
- señales afectadas;
- reglas activadas;
- evidencias;
- limitaciones;
- estado de revisión.

### `AIInterpretation`

- proveedor y modelo;
- prompt version;
- input hash;
- respuesta estructurada;
- resultado de validación;
- coste y latencia;
- fecha;
- flags de revisión.

## Versionado

Cambios incompatibles exigen nueva versión de parser, schema o regla. Los análisis históricos no se sobrescriben; se regeneran en una nueva ejecución.
