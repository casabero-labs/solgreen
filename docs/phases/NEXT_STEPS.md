# Plan ejecutable

## Estado al cierre de L1

L1 — Importación reproducible — cerrado el 2026-07-20.
Cinco PRs mergeados a `main`:

| PR    | Iteración | Contenido                                                                                                            |
| ----- | --------- | -------------------------------------------------------------------------------------------------------------------- |
| #1    | 1         | Scaffolding (uv + py3.12) + contratos Pydantic v2 (PlantFlow, InverterTelemetry, ImportBatch, SignalSpecs ×120).     |
| #2    | 2         | Hashing SHA-256 + detector de formato + fixtures CSV sintéticos reproducibles.                                       |
| #3    | 3         | Parser XLSX/CSV del flujo de planta con normalización de timestamps a UTC por fila.                                   |
| #4    | 4         | Parser XLSX/CSV de telemetría (120 cols) con mapping `ORIGINAL_ES_TO_CANONICAL`.                                     |
| #5    | 5         | Profile loaders (plant/grid YAML) + CLI `solgreen import` + reporter JSON/Markdown.                                  |

Ver [`CHANGELOG.md`](../../CHANGELOG.md) y [`LOOP_REGISTRY.md`](LOOP_REGISTRY.md).

## Próximo loop ejecutable

L2 — Data quality: huecos, duplicados, SOC imposible, signo contradictorio, score.
Salida: módulo `solgreen/quality/` con reglas puras + extensión de `InverterTelemetrySample`
y `PlantFlowSample` con campos `quality_score` y `quality_flags`.

Stop condition: los golden cases del 17 y 19 de julio quedan correctamente
etiquetados sobre los fixtures sintéticos. Validación con archivos reales
queda para cuando estén disponibles fuera del repo.

## Fase 0 — Freeze documental

- revisar Idea Brief;
- confirmar perfil real de planta;
- confirmar límites de batería y red;
- cerrar schemas;
- registrar ADRs.

## Fase 1 — Importer core

Entregables:

- detector de formato;
- parser XLSX flujo de planta;
- parser CSV telemetría;
- hash y metadata;
- pruebas con fixtures sintéticos;
- reporte de importación.

## Fase 2 — Data quality

- huecos;
- duplicados;
- saltos SOC;
- temperaturas inválidas;
- signos contradictorios;
- score y UI.

## Fase 3 — Timeline

- modelo canónico;
- join por tolerancia;
- lineage;
- API temporal;
- downsampling.

## Fase 4 — Análisis determinístico

- balance;
- batería;
- PV/MPPT;
- red;
- estados;
- reglas v0.1.

## Fase 5 — Episodios y D3

- agrupador;
- timeline;
- visor contextual;
- heatmaps;
- comparadores.

## Fase 6 — IA

- adapters;
- prompts versionados;
- schemas;
- validadores;
- consenso para severidad alta.

## Fase 7 — Reportes

- plantillas;
- generación PDF;
- redacción de secretos;
- anexos.

## Fase 8 — Producción

- Butterbase/PostgreSQL;
- Coolify;
- Infisical;
- observabilidad;
- backup/restore;
- hardening.

## Próximo prompt ejecutable

Implementar únicamente L1: importación reproducible, sin UI avanzada, reglas ni IA.
