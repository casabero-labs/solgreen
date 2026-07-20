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
  ui/
  llm-providers/
config/
  grid-profiles/
  plant-profiles/
contracts/
  schemas/
rules/
docs/
```

## Principios

- capas y contratos;
- funciones puras para cálculos;
- reglas versionadas como datos;
- jobs idempotentes;
- originales inmutables;
- análisis reejecutable;
- eventos y auditoría desde el diseño;
- proveedor IA intercambiable.

## Servicios

### ImportService

Detección, hash, parser, normalización y lineage.

### QualityService

Cobertura, huecos, duplicados, plausibilidad y score.

### TimelineService

Alineación temporal con tolerancias y procedencia.

### AnalysisService

Métricas físicas, estadística y reglas.

### EpisodeService

Agrupación temporal y causal de eventos.

### AIInterpretationService

Redacción, proveedor, validación y consenso.

### ReportService

Reportes técnicos versionados y compartibles.
