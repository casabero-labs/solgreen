# Arquitectura de Solgreen

## Vista general

```text
React + D3.js
      ↓ REST/SSE
FastAPI API
      ↓
Servicios de dominio
      ├── ImportService
      ├── QualityService
      ├── TimelineService
      ├── AnalysisService
      ├── EpisodeService
      ├── BillingService
      ├── ConsumptionProfileService
      ├── LoadOptimizationService
      ├── ScenarioService
      ├── AIInterpretationService
      └── ReportService
      ↓
Repositorios / colas / storage
      ↓
PostgreSQL + object storage + workers
```

## Monorepo objetivo

```text
apps/
  web/
services/
  api/
  analysis-worker/
packages/
  contracts/
  rules/
  billing/
  optimization/
  ui/
  llm-providers/
config/
  grid-profiles/
  plant-profiles/
  tariff-profiles/
contracts/
  schemas/
rules/
docs/
```

La estructura actual del motor Python permanece válida mientras evoluciona incrementalmente. Este documento describe el destino arquitectónico, no obliga a una migración masiva durante L2.

## Principios

- capas y contratos;
- funciones puras para cálculos;
- reglas versionadas como datos;
- jobs idempotentes;
- originales inmutables;
- análisis reejecutable;
- eventos y auditoría desde el diseño;
- proveedor IA intercambiable;
- motores técnicos y económicos separados por contratos;
- perfiles con fuente y vigencia;
- ningún control automático en el MVP.

## Regla de dependencias

```text
controllers → services → repositories → models/contracts
```

Para los motores de análisis:

```text
QualityService
      ↓
TimelineService
      ↓
AnalysisService
      ├── EpisodeService
      ├── ConsumptionProfileService
      │       ├── BillingService
      │       └── LoadOptimizationService
      │                 ↓
      │            ScenarioService
      └─────────────────┘
              ↓
AIInterpretationService
              ↓
ReportService
```

La flecha expresa dependencia de resultados confiables, no imports directos entre implementaciones. Cada servicio consume interfaces y contratos versionados.

## Servicios técnicos

### `ImportService`

Detección, hash, parser, normalización y lineage.

No conoce tarifas, reglas económicas ni proveedores IA.

### `QualityService`

Cobertura, huecos, duplicados, plausibilidad y score.

Produce flags consumibles por todos los motores. No altera muestras originales.

### `TimelineService`

Alineación temporal con tolerancias y procedencia.

Expone una vista canónica con signos y unidades explícitos.

### `AnalysisService`

Métricas físicas, integración de energía, estadística y reglas.

Es la autoridad para transformar W en kWh. `BillingService` no reimplementa integración temporal.

### `EpisodeService`

Agrupación temporal y causal de eventos.

La severidad eléctrica permanece separada de oportunidades económicas.

## Servicios económicos

### `BillingService`

Responsabilidades:

- cargar y validar `TariffProfile`;
- calcular factura determinística;
- proyectar ciclo con intervalos;
- conciliar estimación y factura;
- conservar traza de fórmula y redondeo.

Entradas:

- energía integrada desde `AnalysisService`;
- ciclo;
- perfil tarifario;
- líneas de factura normalizadas.

No lee archivos SolarMAN directamente, no identifica electrodomésticos y no llama al LLM para aritmética.

### `ConsumptionProfileService`

Responsabilidades:

- agregar energía por hora local;
- calcular percentiles y cobertura;
- comparar clases de día y periodos;
- localizar ventanas críticas;
- producir cadenas temporales de causa compatible.

Depende de timeline y energía canónica, no de la UI.

### `LoadOptimizationService`

Responsabilidades:

- evaluar ventanas candidatas;
- aplicar reserva, potencia, duración, confort y supervisión;
- comparar baseline frente a desplazamiento;
- producir recomendaciones con intervalos y caducidad.

No controla equipos. Sin `ApplianceProfile` o medición por circuito, no afirma identidad de una carga observada.

### `ScenarioService`

Responsabilidades:

- clonar lógicamente un baseline inmutable;
- aplicar cambios declarativos;
- validar restricciones;
- ejecutar el mismo motor sobre baseline y escenario;
- reportar delta e incertidumbre.

Escenarios AGPE futuros usan perfiles separados y nunca contaminan el modo actual.

## Servicios transversales

### `AIInterpretationService`

Redacción, proveedor, validación y consenso.

Recibe envelopes de hechos técnicos o económicos. No recibe autoridad para:

- crear mediciones;
- modificar severidad;
- calcular facturas;
- alterar recomendaciones;
- inventar tarifas;
- identificar electrodomésticos sin evidencia.

### `ReportService`

Reportes técnicos y económicos versionados y compartibles.

Aplica redacción distinta según audiencia:

- propietario;
- instalador;
- análisis privado;
- informe compartido.

## Interfaces sugeridas

```python
class IEnergyIntegrationService(Protocol):
    def integrate_grid_import(...): ...

class IBillingService(Protocol):
    def estimate_cycle(...): ...
    def reconcile_invoice(...): ...

class IConsumptionProfileService(Protocol):
    def build_hourly_profile(...): ...

class ILoadOptimizationService(Protocol):
    def recommend_windows(...): ...

class IScenarioService(Protocol):
    def run(...): ...
```

Las firmas concretas se cierran en E1-E4. Ningún controller debe conocer fórmulas internas.

## Persistencia

Entidades técnicas y económicas comparten `plant_id` y `analysis_run_id`, pero permanecen separadas:

- originales en object storage privado;
- muestras y timeline en almacenamiento analítico;
- episodios y conciliaciones en DB operacional;
- perfiles versionados en DB/config con fuente;
- outputs IA con input hash y validación;
- reportes como artefactos inmutables.

## Jobs

Jobs candidatos:

- `import_file`;
- `assess_quality`;
- `build_timeline`;
- `compute_metrics`;
- `detect_episodes`;
- `extract_invoice`;
- `estimate_billing_cycle`;
- `build_hourly_profiles`;
- `generate_load_recommendations`;
- `run_scenario`;
- `interpret_analysis`;
- `render_report`.

Cada job debe ser idempotente por checksum de inputs, versión y configuración.

## Seguridad

- originales privados;
- factura completa nunca enviada al LLM;
- claves de proveedores en Infisical;
- perfiles tarifarios requieren fuente y revisión;
- seriales, cuenta, NIC, dirección y medidor redactados;
- recomendaciones no producen writes al inversor;
- futuras escrituras exigirán un diseño independiente con scopes, auditoría y `dryRun`.

## Estrategia incremental

1. L2 sigue siendo el próximo loop.
2. E0 integra fundamentos y contratos documentales.
3. E1 puede modelar perfiles y facturas sin tocar parsers SolarMAN.
4. E2 y E3 esperan L3/L4 para consumir energía confiable.
5. E4 espera perfiles horarios y restricciones.
6. E5 reutiliza L8 para IA validada.

Esta estrategia evita convertir el importador ya estable en una navaja suiza con cables pelados.
