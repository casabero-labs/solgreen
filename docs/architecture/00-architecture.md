# Arquitectura de Solgreen

## Vista general

```text
React + TypeScript + D3
        ↓ REST/SSE
FastAPI API
        ↓
Servicios de dominio determinísticos
        ├── ImportService
        ├── QualityService
        ├── TimelineService
        ├── MetricsService
        ├── EventService
        ├── RuleService
        ├── EconomicService
        ├── AIInterpretationService
        └── ReportService
        ↓
Repositorios / colas / storage
        ↓
PostgreSQL + object storage + workers
```

## Línea única

La arquitectura y el roadmap avanzan sobre:

```text
main → develop/solgreen-unified → un único PR activo
```

No existen pistas separadas de diagnóstico, economía o frontend. Cada loop añade una capacidad coherente a la misma vertical, manteniendo dependencias explícitas y CI verde.

Documento canónico: [`../phases/UNIFIED_DEVELOPMENT_LINE.md`](../phases/UNIFIED_DEVELOPMENT_LINE.md).

## Estructura objetivo

```text
apps/
  web/                    # React, TypeScript, D3, Showcase Ink
solgreen/                 # paquete Python actual
  api.py                  # FastAPI
  contracts/
  core/
  importer/
  quality/
  timeline/
  diagnostics/
  economics/              # U5
  reports/                # U7
  db/
config/
  grid-profiles/
  plant-profiles/
  tariff-profiles/
docs/
  architecture/
  domain/
  frontend/
  phases/
  qa_reports/
  deployments/
tests/
```

Se evita una migración estructural masiva prematura. La extracción futura hacia `services/` o `packages/` requiere evidencia de necesidad y un loop propio.

## Principios

- dominio y normativa antes que implementación;
- capas y contratos explícitos;
- funciones puras para física y economía;
- reglas versionadas como datos y evaluadores determinísticos;
- jobs idempotentes;
- originales privados e inmutables;
- análisis reejecutable;
- lineage hacia fuente y versión;
- eventos y auditoría desde el diseño;
- proveedor IA intercambiable;
- frontend human-first;
- un solo estado de producto documentado.

## Flujo de datos

```text
archivo privado
  → hash y detección
  → parser y normalización
  → calidad y cobertura
  → timeline canónico
  → energía y métricas
  → eventos y reglas
  → economía y escenarios
  → evidencia estructurada
  → API
  → frontend Showcase Ink
  → IA validada opcional
  → PDF / decisión humana
```

## Servicios

### ImportService

Detección, hash, parser, normalización, redacción y lineage.

### QualityService

Orden, cobertura, huecos, duplicados, plausibilidad, consistencia y score. No interpola silenciosamente.

### TimelineService

Alineación temporal con tolerancias, procedencia de ambas fuentes y semántica correcta de cero y estados.

### MetricsService

Integración temporal W→Wh/kWh, balance, residual, batería, PV, red, percentiles y confianza.

### EventService

Separa segmentos operativos de eventos científicos. Construye ventanas antes, durante y después.

### RuleService

Ejecuta evaluadores versionados. Una señal presente nunca equivale a una regla activada.

### EconomicService

Contratos tarifarios, factura, conciliación, forecast, perfiles horarios, recomendaciones restringidas y escenarios. El LLM no ejecuta fórmulas económicas.

### AIInterpretationService

Consume únicamente resultados y evidencias válidos. Aplica IDs estables, exact coverage, validación y persistencia condicionada.

### ReportService

Genera reportes versionados y compartibles con política de privacidad, fuentes, supuestos y limitaciones.

## Frontend

Arquitectura específica: [`../frontend/FRONTEND_ARCHITECTURE.md`](../frontend/FRONTEND_ARCHITECTURE.md).

Decisiones:

- React gobierna estado, accesibilidad y composición;
- D3 calcula escalas, geometría y paths, no administra todo el DOM;
- Ink Console para análisis;
- Ink Form para flujos;
- Ink Editorial para reportes;
- toda gráfica crítica tiene tabla alternativa;
- datos demo y niveles epistemológicos se identifican de forma persistente;
- no se habilitan acciones sin contrato backend y flujo Human-First probado.

## Contratos API

Antes de conectar U4, cada endpoint debe declarar:

- request y response versionados;
- estado de job;
- errores accionables;
- paginación o ventana temporal;
- lineage y versión de análisis;
- cobertura y confianza;
- política de privacidad;
- idempotencia;
- autorización por planta.

No se exponen modelos de persistencia directamente como contrato de UI.

## Persistencia

PostgreSQL conserva:

- lotes de importación;
- muestras canónicas;
- métricas y eventos derivados;
- ejecuciones de reglas;
- evidencias;
- perfiles tarifarios y facturas normalizadas;
- escenarios;
- interpretaciones IA validadas;
- metadata de reportes.

Datos derivados son regenerables. Archivos originales permanecen en storage privado y no en Git.

## IA

```text
cálculo determinístico → evidence envelope → prompt versionado
→ proveedor → schema → validación → persistencia o rechazo
```

La IA nunca recibe secretos ni datasets completos cuando bastan resúmenes estructurados. No confirma causas, no modifica cifras y no controla equipos.

## Operación

El despliegue objetivo usa Coolify e Infisical:

- build y tests;
- backup antes de migración;
- deploy real, no restart;
- polling a estado final;
- SHA del contenedor;
- health público;
- smoke del flujo principal;
- rollback probado;
- evidencia en `docs/deployments/`.
