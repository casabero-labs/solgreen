# Línea única de desarrollo — Solgreen

## 1. Decisión

Solgreen se desarrolla mediante una sola línea canónica:

```text
main
  └── develop/solgreen-unified
        └── un único PR activo contra main
```

`main` contiene únicamente estados verificados. `develop/solgreen-unified` integra de forma ordenada backend, motor científico, economía, frontend, IA, reportes y operación.

No se crean ramas independientes por pista mientras esta integración esté activa. Una excepción requiere un hotfix de producción documentado y reversible.

## 2. Razón

La separación anterior produjo:

- documentación económica divergida;
- fases técnicas cerradas nominalmente antes de validar su comportamiento científico;
- roadmap distinto entre README, Loop Registry y código;
- frontend postergado como una pista aislada;
- múltiples PRs cortos sin una visión de producto compartida.

La línea única no significa mezclar todo en un commit. Significa mantener una sola secuencia de producto con loops pequeños, verificados y dependencias explícitas.

## 3. Regla de integración

Cada loop dentro del PR unificado debe:

1. partir del último SHA verde de la rama;
2. declarar `GOAL`, `CONTEXT`, `ACTION`, `FEEDBACK`, `STOP CONDITION`, `HUMAN GATE` y `ROLLBACK`;
3. cambiar una capacidad coherente;
4. mantener el PR desplegable o explícitamente bloqueado;
5. actualizar código, tests y documentación juntos;
6. no presentar superficies experimentales como terminadas.

## 4. Secuencia U0–U7

| Loop | Resultado | Dependencias | Estado |
|---|---|---|---|---|
| U0 | Fundación unificada y frontend Showcase Ink ejecutable | R0 | TECHNICALLY_VERIFIED_HUMAN_GATE |
| U1 | Calidad, semántica y safety gates | U0, #21 | ENGINEERING_CLOSED |
| U2 | Energía y métricas físicas | U1 | NEXT_PLANNED |
| U3 | Eventos, reglas y golden cases | U2, #20 | PLANNED |
| U4 | Frontend conectado y flujos human-first | U3 | PLANNED |
| U5 | Inteligencia económica Afinia | U2, U4 | FOUNDATION_ABSORBED |
| U6 | IA validada con evidencias estables | U3, #22 | BLOCKED |
| U7 | PDF, deploy y operación verificable | U4, U5, U6 | PLANNED |

## 5. U0 — Fundación unificada

### Goal

Crear una sola fuente de verdad y una primera vertical frontend real que no prometa funciones inexistentes.

### Entregables

- fundación económica Afinia absorbida desde el PR #8;
- ADR deterministic-first;
- diccionario de facturación;
- test plan económico;
- aplicación React + TypeScript + Vite;
- visualización D3 con tabla alternativa;
- navegación Planta, Datos y Economía;
- modo oscuro global;
- datos demostrativos etiquetados;
- acción de importación bloqueada hasta contar con API y E2E;
- CI Python, frontend, documentación y privacidad;
- arquitectura frontend Showcase Ink;
- un solo PR activo.

### Feedback

```text
Python: Ruff + mypy + pytest
Frontend: TypeScript + Vitest + Vite build
Docs: archivos canónicos y privacidad
Humano: revisión del flujo, alcance y jerarquía
```

Evidencia técnica: [`../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md`](../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md).

### Stop condition

- CI completa en verde;
- frontend abre y permite navegar/cambiar periodo;
- no presenta datos demo como reales;
- no presenta COP vigente sin perfil;
- D3 tiene tabla alternativa;
- README, arquitectura, Loop Registry y Next Steps coinciden;
- PR #8 cerrado como supersedido;
- un solo PR de producto abierto.

La condición técnica está cumplida. El cierre definitivo espera revisión humana.

### Human gate

Revisión visual y funcional antes de marcar U0 cerrado. El frontend aún no constituye validación de una planta real.

### Rollback

Cerrar el PR unificado. `main` conserva R0 sin el frontend ni la integración económica.

## 6. U1 — Calidad, semántica y safety gates

### Goal

Garantizar que los datos canónicos tengan una semántica correcta, calidad
físicamente razonable y safety gates operativos antes de calcular energía,
detectar eventos o conectar datos reales al frontend.

### Entregables

**U1.1 — Semántica de cero y estado:**
- `_pv_power` preserva 0.0 medido (no colapsa a None).
- `get_text(canonical_name) -> str | None` para señales textuales.
- `telemetry_inverter_state` preservado como `str | None` en merged y
  telemetry-only.
- Sin conversión de cero en ausencia, apagado o falla.

**U1.2 — Calidad temporal y dimensiones:**
- `QualityDimensions` (completeness, temporal_coverage,
  duplicate_integrity, plausibility_score, consistency_score).
- `QualityResult.quality_score` conservado como campo serializado.
- `compute_temporal_dimensions` y `aggregate_quality_score` con pesos
  nombrados: `DUPLICATE_INTEGRITY_WEIGHT=0.60`,
  `TEMPORAL_COVERAGE_WEIGHT=0.40`.
- `missing_duration = Σ max(gap_duration − expected_interval, 0)`.
- `temporal_coverage = covered_duration / analysis_span`.
- Lote vacío: completeness=0.0, temporal_coverage=0.0, quality_score=0.0.
- Sin ventana temporal explícita (profile.window) aún.

**U1.3 — Plausibilidad:**
- Valores no finitos (NaN, +Inf, −Inf) → finding inmediato.
- SOC universal [0, 100] → evaluated+passed dentro del rango,
  evaluated+failed fuera.
- Temperatura < −273.15 °C → failed; temperatura válida sin perfil →
  not_configured.
- Rangos configurados por perfil (MeasurementPlausibilityProfile) para
  voltaje, frecuencia, temperatura. Sin hardcode de límites operativos
  (normalMinSocPct, overvoltageV, etc.).
- Sin máximo de temperatura genérico (podría ser evento real).
- Sin peso inventado para plausibilidad en score global.

**U1.3.1 — Contabilidad correcta:**
- evaluated_count == passed_count + failed_count.
- score is None ⇔ evaluated_count == 0.
- score == passed_count / evaluated_count.
- Invariante validado via Pydantic model_validator.

**U1.4.0 — Corrección de timeline:**
- `telemetry_grid_power_w` ahora usa `total_active_power_of_the_grid_w`
  (no `potencia_total_ca_w`).
- `telemetry_inverter_state` en telemetry-only usa `get_text`.

**U1.4 — Consistencia entre fuentes:**
- `ConsistencyPair`, `MeasurementConsistencyProfile`.
- Solo muestras `source=merged`.
- Tolerancia: `max(absolute_tolerance, relative_tolerance × max(|a|,|b|))`.
- SOC flow↔telemetry como único par seguro probado; sin comparaciones
  automáticas de potencia.
- Score = passed/evaluated; skipped contadores no participan.

**U1.5.0 — Parser ISO 8601:**
- `parse_iso_duration(value: str) -> timedelta`.
- Soporte: D, H, M, S + fraccionales hasta 6 dígitos.
- Rechazo de PT0S, negativos, meses/años, formatos humanos, minúsculas,
  basura al final, precisión excedida.
- Validación antes de side effects en CLI.

**U1.5.1 — Formato global:**
- `ruff format .` sobre 14 archivos, AST equivalente.
- CI gate global: `ruff format --check --diff .`.

**U1.5.2 — npm reproducible:**
- `package-lock.json` versionado.
- CI usa `npm ci`.
- CI exige presencia de `package-lock.json`.

**U1.6 — Rule evaluation y LLM gate:**
- `RuleImplementationStatus` (planned/implemented).
- `RuleEvaluationOutcome` con invariantes (not_evaluable sin execution,
  fired con evidence no vacía).
- `evaluate_rule_catalog` con registro vacío de producción.
- `eligible_fired_rules`:
  - fired=False → excluida.
  - fired=True sin evidence → excluida.
  - fired=True con evidence → elegible.
- Seed rules (DATA-001, BAT-001, PV-001, GRID-003, INV-002):
  `planned`, cinco outcomes `not_evaluable`, 0 ejecuciones persistidas.
- LLM no invocado sin reglas elegibles; mensaje
  `LLM skipped: no validated fired-rule evidence`.

### Feedback

```text
Python: Ruff + format + mypy + pytest + coverage ≥ 80%
Frontend: npm ci + TypeScript + Vitest + Vite build
Docs: QA report U1
Humano: revisión de signos, perfiles y umbrales
```

Evidencia técnica: [`../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md`](../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md).

### Stop condition

- Cero medido preservado en todas las rutas.
- Estados textuales sobreviven al merge.
- Lote vacío no obtiene score perfecto.
- Huecos ponderados por duración.
- Plausibilidad física con tests positivos y negativos.
- Límites desde perfiles (o not_configured).
- Consistencia: solo pares declarados, evidencia estructurada.
- Parser ISO corregido (#24).
- Formato global normalizado (#25).
- Ruff, format, mypy, pytest green; cobertura ≥ 80%.
- Seed rules not_evaluable; 0 RuleExecution falsas.
- LLM no invocado sin evidencia.
- CI completa verde.
- Documentación reconciliada.

La condición técnica está cumplida.

### Human gates
- Revisión visual y funcional U0.
- Signos reales de red y batería.
- Perfiles de plausibilidad y consistencia para Casabero.
- Límites técnicos de equipos.
- Algoritmos y umbrales de reglas U3.
- Golden cases.
- Merge a main.

### Rollback
Revertir commits U1 en `develop/solgreen-unified`. Main conserva R0 + U0.

### Próximo loop exacto
U2: energía, métricas físicas y perfiles de signo.

## 7. U2 — Energía y métricas

- integración temporal W→Wh/kWh;
- tratamiento de huecos;
- importación y exportación canónicas;
- carga y descarga de batería;
- balance y residual;
- cobertura y confianza;
- perfiles horarios locales;
- no mezclar potencia con energía.

## 8. U3 — Eventos y reglas

- segmentos operativos separados de eventos;
- ventanas antes, durante y después;
- dropout FV;
- pérdida y retorno de red;
- SOC bajo y descarga profunda;
- reinicios e inicializaciones;
- evaluadores determinísticos, no presencia de señales;
- golden cases privados del 17 y 19;
- evidencia estructurada estable.

## 9. U4 — Frontend conectado

- API contracts;
- carga CSV/XLSX;
- progreso real;
- timeline D3;
- filtros persistentes;
- episodios con evidencia;
- tablas alternativas;
- estados vacío, loading, error y parcial;
- E2E Human-First;
- telemetría de producto sin datos sensibles.

## 10. U5 — Economía Afinia

- `TariffProfile` y vigencia;
- factura normalizada;
- motor tarifario puro;
- subsidio parametrizado;
- conciliación;
- P10/P50/P90;
- perfil horario de compra;
- catálogo de cargas;
- recomendaciones restringidas;
- simulador `what-if`;
- escenarios AGPE separados del modo actual.

La factura oficial y el medidor fiscal conservan autoridad. El LLM no calcula dinero ni energía.

## 11. U6 — IA validada

- IDs de evidencia estables;
- exact coverage;
- rechazo de referencias inexistentes o cruzadas;
- rechazo de cifras nuevas;
- proveedor y modelo reales registrados;
- prompt versionado;
- coste y fallback auditables;
- cero persistencia de respuestas inválidas.

## 12. U7 — Reportes y operación

- PDF técnico reproducible;
- privacidad configurable;
- API y frontend desplegados;
- migraciones versionadas;
- Coolify con polling a estado final;
- SHA del contenedor;
- health público;
- smoke tests;
- rollback probado;
- evidencia en `docs/deployments/`.

## 13. Política de PRs

Durante la línea unificada:

- un único PR de producto abierto;
- los issues describen loops, bloqueadores y stop conditions;
- los commits son pequeños y temáticos dentro de la misma rama;
- un commit rojo no se considera checkpoint;
- no se fusiona parcialmente una pista incompleta;
- el PR permanece draft mientras el loop activo no cierre;
- `main` solo recibe squash cuando el conjunto integrado es coherente y verificable.

## 14. Estado actual + próximo paso exacto

**Estado actual:** R0 fusionado; economía E0 absorbida; U0 técnicamente verificado con human gate pendiente; U1 ENGINEERING_CLOSED con 442 tests y CI verde.

**Próximo paso exacto:** U2.0 — Energy semantics, sign profiles and integration contract discovery.
