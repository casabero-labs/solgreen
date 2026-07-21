# Loop Registry — Solgreen

## Metodología

Solgreen aplica `casabero-labs/estandar-casabero`:

```text
DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT
```

Cada loop declara `GOAL`, `CONTEXT`, `ACTION`, `FEEDBACK`, `STOP CONDITION`, `HUMAN GATE`, `ROLLBACK` y próximo paso exacto.

## Gobernanza de desarrollo

```text
main → develop/solgreen-unified → un único PR activo
```

- `main` es la fuente estable.
- La rama unificada integra todas las capacidades.
- Los issues son loops o bloqueadores, no ramas alternativas.
- No abrir pistas paralelas de frontend, economía, diagnóstico o IA.
- Documento canónico: [`UNIFIED_DEVELOPMENT_LINE.md`](UNIFIED_DEVELOPMENT_LINE.md).

## Feedback disponible

- schemas SolarMAN;
- fixtures sintéticos;
- datasets y facturas privadas fuera de Git;
- golden cases del 17 y 19 de julio;
- tests Python y frontend;
- CI;
- revisión Human-First;
- revisión del propietario;
- diagnóstico del instalador;
- perfiles oficiales cuando estén disponibles.

## Comandos de verificación

### Backend

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest --cov=solgreen --cov-fail-under=80
```

### Frontend

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run typecheck
npm run test
npm run build
```

## Human gates

- perfil real de planta;
- signos de red y batería;
- límites de batería, inversor y red;
- severidad crítica;
- confirmación de causa;
- perfil tarifario vigente;
- corrección de factura extraída;
- merge;
- reportes compartidos;
- deploy;
- cualquier escritura sobre equipos;
- cierre de flujos críticos de UI.

## Estado oficial unificado

| Loop | Objetivo | Feedback principal | Stop condition | Estado |
|---|---|---|---|---|---|
| R0 | Reconciliar baseline y safety gates | CI y auditoría | estado documental coincide con código | CLOSED |
| U0 | Integrar economía y frontend Showcase Ink | TS, Vitest, build, docs | primera vertical ejecutable y honesta | TECHNICALLY_VERIFIED_HUMAN_GATE |
| U1 | Calidad avanzada y semántica | fixtures y tests | cero, status, plausibilidad, consistencia y safety gates | ENGINEERING_CLOSED |
| U2 | Energía y métricas físicas | fórmulas y golden manuales | W→kWh y balance reproducibles | NEXT_PLANNED |
| U3 | Eventos, reglas y evidencia | golden 17/19 | eventos científicos y reglas reales | PLANNED |
| U4 | Frontend conectado | Playwright Human-First | carga, timeline y episodios utilizables | PLANNED |
| U5 | Afinia, cargas y escenarios | golden billing | factura y horarios reproducibles | FOUNDATION_ABSORBED |
| U6 | IA validada | adversarial tests | cero respuesta inválida aceptada | BLOCKED_BY_U3 |
| U7 | PDF y operación | deploy, SHA, health | flujo desplegado y reversible | PLANNED |

## Bloqueadores vinculados

- #20: evaluadores determinísticos;
- #21: semántica del timeline y eventos;
- #22: evidencias y validador IA;
- #24: parser ISO de duración;
- #25: baseline global de formato;
- #26: epic de línea unificada.

## Loop cerrado

# U1 — Calidad, semántica y safety gates

## Goal

Garantizar que los datos canónicos tengan una semántica correcta, calidad
físicamente razonable y safety gates operativos antes de calcular energía,
detectar eventos o conectar datos reales al frontend.

## Context

- U0 técnicamente verificado (human gate pendiente).
- `_pv_power` perdía cero medido; estado textual se troncaba a None en merged.
- `compute_quality_score(total_rows=0)` devolvía 1.0.
- `_parse_iso_duration` roto (#24).
- `_evaluate_rules` activaba reglas por presencia de señales.
- Formato global sin normalizar (#25).

## Actions ejecutadas

1. U1.1: semántica de cero y estado (get_text, _pv_power fix, calidad temporal).
2. U1.2: QualityDimensions aditivas, cobertura temporal por duración, lote vacío→0.
3. U1.3: plausibilidad universal (NaN, SOC, temperatura absoluta) + perfil.
4. U1.3.1: contabilidad passed/failed/evaluated con invariante Pydantic.
5. U1.4.0: corrección de telemetry_grid_power_w e inverter_state en telemetry-only.
6. U1.4: consistencia entre fuentes basada en perfil (solo SOC probado).
7. U1.5.0–a: parser ISO puro, validación antes de side effects, CLI tests.
8. U1.5.1: ruff format global, CI gate global.
9. U1.5.2: package-lock.json versionado, npm ci en CI.
10. U1.6: estados de reglas (not_evaluable/evaluated_not_fired/fired), gate LLM.

## Feedback

- Ruff + mypy + pytest + cobertura ≥ 80%.
- Frontend npm ci + typecheck + test + build.
- 442 tests, 90.78% cobertura.
- CI push #123 y PR #124 verdes.
- Gate global de formato.
- Zero RuleExecution falsas.
- LLM omitido sin evidencia.
- Documentación reconciliada.

## Stop condition cumplida

- Cero medido preservado en todas las rutas.
- Estados textuales sobreviven al join.
- Lote vacío no obtiene score perfecto.
- Huecos ponderados por duración.
- Plausibilidad física con tests positivos y negativos.
- Límites desde perfiles (o not_configured).
- Consistencia entre fuentes produce evidencia estructurada.
- Parser ISO corregido (#24).
- Formato global normalizado (#25).
- Ruff, format, mypy, pytest green; cobertura 90.78%.
- Seed rules not_evaluable; 0 RuleExecution falsas.
- LLM no invocado sin evidencia.
- CI completa verde.
- Documentación reconciliada.

## Human gates pendientes

- Revisión visual y funcional U0.
- Signos reales de red y batería.
- Perfiles de plausibilidad y consistencia para Casabero.
- Límites técnicos de equipos.
- Algoritmos y umbrales de reglas U3.
- Golden cases.
- Merge a main.

## Rollback

Revertir commits U1 en `develop/solgreen-unified`. Main conserva R0 + U0.

## Próximo loop exacto

U2: energía, métricas físicas y signos.
