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

## Entidades económicas

Los detalles de campo y unidades están en [`data-dictionary/afinia-billing.md`](data-dictionary/afinia-billing.md).

### `TariffProfile`

Fuente versionada de reglas económicas:

- proveedor y segmento;
- territorio;
- vigencia;
- CU;
- política de subsidio;
- cargos no energéticos;
- reglas de redondeo;
- fuente y estado de verificación.

Un perfil histórico no se utiliza como vigente sin una decisión humana explícita.

### `InvoiceDocument`

- hash del original privado;
- proveedor;
- fecha de emisión y vencimiento;
- ciclo asociado;
- identificadores redactados;
- total observado;
- versión del parser;
- confianza y revisión.

### `InvoiceLine`

- código canónico;
- etiqueta observada;
- cantidad, unidad y tarifa;
- monto en centavos de COP;
- cargo o crédito;
- nivel epistemológico;
- ubicación en el documento.

### `BillingCycle`

- inicio y fin local;
- timezone;
- duración real;
- lecturas fiscales opcionales;
- energía facturada;
- perfil tarifario;
- estado abierto, proyectado, cerrado o conciliado.

### `BillingEstimate`

- energía importada estimada;
- cargo bruto;
- subsidio;
- subtotal;
- cargos no energéticos;
- P10/P50/P90;
- cobertura y confianza;
- supuestos;
- traza de cálculo y redondeo.

### `BillingReconciliation`

- estimación y factura comparadas;
- delta energético y monetario;
- tolerancia;
- explicaciones candidatas;
- estado y revisión humana.

No declara error del comercializador automáticamente.

### `HourlyEnergyProfile`

Agregación por hora local con:

- clasificación de día;
- cobertura y número de días;
- consumo, FV, red y batería en kWh;
- SOC inicial y final;
- P50, P90, P95 y máximo de potencia;
- versión del método.

### `ApplianceProfile`

- nombre y categoría;
- potencia y pico declarados o medidos;
- duración;
- flexibilidad;
- supervisión;
- ventanas permitidas;
- prioridad;
- fuente y confianza.

Un perfil declarado no equivale a identificación automática del equipo en la curva agregada.

### `LoadRecommendation`

- equipo o clase de carga;
- fecha de vigencia;
- ventana recomendada y ventanas evitadas;
- delta esperado de red, costo y SOC como intervalo;
- restricciones;
- evidencias;
- confianza;
- estado y caducidad.

### `ScenarioDefinition`

- baseline seleccionado;
- cambios solicitados;
- supuestos;
- restricciones;
- perfiles y versiones aplicables.

### `ScenarioRun`

- checksum del baseline;
- resultados baseline y escenario;
- delta energético, económico y de SOC;
- violaciones de restricciones;
- incertidumbre;
- versión del motor.

### `EconomicAIInterpretation`

Especialización de interpretación IA:

- referencias a estimaciones, perfiles, recomendaciones o escenarios;
- cifras verificadas contra el envelope;
- supuestos citados;
- lenguaje técnico y/o doméstico;
- validación de no garantía y no identificación indebida.

## Relaciones mínimas

```text
Plant
  ├── ImportBatch → Samples → CanonicalSample
  ├── Episode → Evidence → AIInterpretation
  ├── BillingCycle
  │     ├── InvoiceDocument → InvoiceLine
  │     ├── TariffProfile
  │     ├── BillingEstimate
  │     └── BillingReconciliation
  ├── HourlyEnergyProfile
  ├── ApplianceProfile
  ├── LoadRecommendation
  └── ScenarioDefinition → ScenarioRun → EconomicAIInterpretation
```

## Convenciones económicas

- COP persistido como centavos enteros.
- Decimales se preservan hasta el punto de redondeo definido.
- Potencia y energía nunca comparten el mismo campo.
- Todo monto cita perfil, periodo y versión.
- Forecast siempre incluye intervalo o una razón para no producirlo.
- La factura oficial se conserva separada de la estimación.
- El medidor fiscal, cuando exista, se conserva separado de SolarMAN.
- Las recomendaciones no modifican muestras ni configuración.

## Versionado

Cambios incompatibles exigen nueva versión de parser, schema, regla, perfil tarifario o motor de escenario. Los análisis históricos no se sobrescriben; se regeneran en una nueva ejecución.

Un cambio de tarifa o vigencia crea un nuevo `TariffProfile`; nunca modifica retroactivamente el perfil utilizado por una ejecución cerrada.
