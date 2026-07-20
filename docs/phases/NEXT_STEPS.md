# Plan ejecutable

## Estado al cierre de L1

L1 — Importación reproducible — cerrado el 2026-07-20.
Cinco PRs mergeados a `main`:

| PR | Iteración | Contenido |
|---|---:|---|
| #1 | 1 | Scaffolding (uv + py3.12) + contratos Pydantic v2 (PlantFlow, InverterTelemetry, ImportBatch, SignalSpecs ×120). |
| #2 | 2 | Hashing SHA-256 + detector de formato + fixtures CSV sintéticos reproducibles. |
| #3 | 3 | Parser XLSX/CSV del flujo de planta con normalización de timestamps a UTC por fila. |
| #4 | 4 | Parser XLSX/CSV de telemetría (120 cols) con mapping `ORIGINAL_ES_TO_CANONICAL`. |
| #5 | 5 | Profile loaders (plant/grid YAML) + CLI `solgreen import` + reporter JSON/Markdown. |

Ver [`CHANGELOG.md`](../../CHANGELOG.md) y [`LOOP_REGISTRY.md`](LOOP_REGISTRY.md).

## Integración de inteligencia económica

Se añadió una pista paralela E0-E5 para:

- cálculo y conciliación de facturas;
- proyección con incertidumbre;
- consumo y compra por hora;
- recomendaciones de cargas;
- simulaciones;
- interpretación económica IA validada.

Esta pista no modifica el importador L1 ni cambia el próximo loop técnico. E2-E5 dependen explícitamente de calidad, timeline, energía integrada y guardrails IA.

Documentos principales:

- [`../domain/ECONOMIC_INTELLIGENCE.md`](../domain/ECONOMIC_INTELLIGENCE.md)
- [`../domain/data-dictionary/afinia-billing.md`](../domain/data-dictionary/afinia-billing.md)
- [`../product/04-economic-intelligence-workflows.md`](../product/04-economic-intelligence-workflows.md)
- [`../decisions/ADR-005-economic-intelligence-deterministic-first.md`](../decisions/ADR-005-economic-intelligence-deterministic-first.md)
- [`../qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md`](../qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md)

## Próximo loop ejecutable

### L2 — Data quality

**Objetivo:** detectar huecos, duplicados, SOC imposible, temperatura inválida, signo contradictorio y producir score de calidad.

**Salida:**

- módulo `solgreen/quality/` con reglas puras;
- contratos de flags y score sin romper L1;
- extensión compatible de reportes;
- fixtures sintéticos de golden cases;
- documentación de resultados.

**Stop condition:**

- golden cases del 17 y 19 de julio correctamente etiquetados sobre fixtures sintéticos;
- imports L1 siguen idempotentes;
- 73 tests existentes continúan pasando;
- nuevos tests de calidad pasan;
- cobertura total ≥ 80%;
- ruff, mypy y CI en verde.

La validación con archivos reales se ejecuta fuera del repositorio.

## Pista económica inmediata

E0 queda cerrado al aceptar el PR documental.

E1 puede planearse después de L2 o ejecutarse en una rama independiente porque solo crea contratos tarifarios y de factura. No debe tocar:

- parsers SolarMAN;
- modelos existentes sin estrategia compatible;
- reglas L2;
- CLI `solgreen import`;
- fixtures privados.

E2 y E3 permanecen bloqueados hasta contar con timeline y energía integrada confiables de L3/L4.

## Fase 0 — Freeze documental

- revisar Idea Brief;
- confirmar perfil real de planta;
- confirmar límites de batería y red;
- cerrar schemas;
- registrar ADRs;
- mantener perfiles tarifarios con fuente y vigencia.

## Fase 1 — Importer core

Estado: cerrado como L1.

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
- score y reporte;
- compatibilidad hacia atrás con L1.

## Fase 3 — Timeline

- modelo canónico;
- join por tolerancia;
- lineage;
- API temporal;
- downsampling.

## Fase 4 — Análisis determinístico

- balance;
- integración de energía;
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
- consenso para severidad alta;
- validación exacta de cifras económicas.

## Fase 7 — Reportes

- plantillas;
- generación PDF;
- redacción de secretos;
- anexos técnicos y económicos.

## Fase 8 — Producción

- Butterbase/PostgreSQL;
- Coolify;
- Infisical;
- observabilidad;
- backup/restore;
- hardening.

## Roadmap económico

### E1 — Contratos y perfiles

- Pydantic models económicos;
- validación de vigencia y fuente;
- centavos enteros;
- fixtures sintéticos;
- lectura manual primero, parser PDF después.

### E2 — Factura y forecast

- motor tarifario puro;
- conciliación;
- P10/P50/P90;
- golden tests privados.

### E3 — Perfiles horarios

- energía por hora local;
- percentiles;
- ventanas críticas;
- D3 y cobertura.

### E4 — Recomendaciones

- catálogo doméstico;
- restricciones;
- optimizador conservador;
- aceptación y feedback.

### E5 — Simulador e IA

- baseline inmutable;
- escenarios;
- deltas;
- explicación MiniMax/DeepSeek validada.

## Próximo prompt ejecutable

Implementar únicamente **L2 — Data quality**, preservando contratos y comportamiento de L1. No implementar todavía factura, recomendaciones, UI avanzada ni IA. El PR de E0 es documentación y arquitectura, no autorización para saltar dependencias.
