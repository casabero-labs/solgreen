# U1 — Data quality, semantics and safety gates

## Identificación

- Fecha: 2026-07-21
- Línea: `develop/solgreen-unified`
- PR: #27
- SHA final: `9c76912f7953d0b0d6a9da1a75e9c515370e5965`
- CI push final: run #123
- CI PR final: run #124

## Objetivo

Garantizar que los datos canónicos tengan una semántica correcta, calidad
físicamente razonable y safety gates operativos antes de calcular energía,
detectar eventos o conectar datos reales al frontend.

## Baseline inicial

- R0 fusionado en `main@1f70674`.
- U0 técnicamente verificado (human gate pendiente).
- 219 tests, cobertura 88.87%.
- `ruff format --check` fallaba en 19 archivos.
- `python-dateutil.isoparser().parse_timedelta()` roto (#24).
- `_evaluate_rules` disparaba reglas por presencia de señales.

## Subbloques ejecutados

| Bloque | SHA | Archivos | Tests |
|---|---|---|---|
| U1.1 — Cero y estado | `a6dcc12` | 4 | +10 |
| U1.1 (style) | `209f442` | 1 | 0 |
| U1.2 — Dimensiones temporales | `8582598` | 8 | +34 |
| U1.3 — Plausibilidad | `0d79f04` | 5 | +40 |
| U1.3.1 — Contabilidad | `519db8a` | 4 | +10 |
| U1.4.0 — Timeline semántica | `175bab0` | 3 | +7 |
| U1.4 — Consistencia fuentes | `cfb30b3` | 3 | +46 |
| U1.5.0 — Parser ISO | `9f4c19d` | 4 | +32 |
| U1.5.0a — CLI tolerancia | `927750f`+`49391d5` | 4 | +15 |
| U1.5.1 — Formato global | `3a365a5`+`9102b99` | 16 | 0 |
| U1.5.2 — npm lockfile | `e55237c`+`89cddad`+`df4b511` | 2 | 0 |
| U1.6 — Rule evaluation gate | `7485b25`+`9c76912` | 7 | +34 |

## Contratos creados

| Archivo | Propósito |
|---|---|
| `solgreen/quality/_plausibility_types.py` | PlausibilityFinding, MeasurementRange, PlausibilityResult |
| `solgreen/quality/_consistency_types.py` | ConsistencyPair, ConsistencyResult |
| `solgreen/quality/plausibility.py` | Evaluador puro de plausibilidad |
| `solgreen/quality/consistency.py` | Evaluador puro de consistencia |
| `solgreen/timeline/duration.py` | Parser ISO 8601 puro (± microsegundos) |
| `solgreen/diagnostics/rule_evaluation.py` | Outcomes, evaluadores, registry, gate |

## Bugs corregidos

- `_pv_power` convertía 0.0 → None (cero medido perdido).
- `telemetry_inverter_state` se asignaba via `get_float` en lugar de
  `get_text` (estado textual perdido en merged).
- `telemetry_grid_power_w` se alimentaba de `potencia_total_ca_w`
  en lugar de `total_active_power_of_the_grid_w`.
- `compute_quality_score(total_rows=0)` devolvía 1.0.
- Huecos ponderados por cantidad, no por duración.
- `_parse_iso_duration` usaba `isoparser().parse_timedelta()` (inexistente).
- `_evaluate_rules` disparaba reglas por presencia de señales.

## Decisiones científicas

- **Cero medido** se conserva como 0.0, no se convierte en None.
- **Estado textual** se conserva via `get_text(canonical_name) -> str | None`.
- **SOC universal [0, 100]** es regla completa para SOC sin perfil.
- **Temperatura universal** solo mínimo absoluto (−273.15 °C).
  Sin máximo genérico (podría ser evento real).
- **PlausibilityScore** no modifica `aggregate_quality_score`:
  peso de plausibilidad no inventado.
- **ConsistencyScore** comparación solo entre pares declarados
  en perfil explícito. Sin automático entre señales de potencia.
- **Tolerancia de consistencia** usa `max(absoluta, relativa * max(|a|,|b|))`.
- **Evaluación de reglas**: seed rules → `planned` → `not_evaluable`.
  Sin evaluador real = no RuleExecution persistido.
- **Gate LLM**: sin fired rule con evidencia, no se llama `provider.complete`.

## Tests

- **Total:** 442 tests unitarios y de integración.
- **Cobertura:** 90.78 %.
- **Distribución:**
  - 58 archivos fuente Python.
  - 42 archivos de test.
  - 34 tests de calidad (U1.2–U1.4).
  - 11 tests CLI de tolerancia (U1.5.0a).
  - 32 tests de parser ISO (U1.5.0).
  - 34 tests de rule evaluation + LLM gate (U1.6).
  - 50 tests de plausibilidad (U1.3–U1.3.1).
  - 8 integración DB + smoke (skipped sin base de datos).
- **Fixtures:** sintéticos, sin datos reales SolarMAN en el repo.

## Checks de privacidad

- No se introdujeron nuevos exports privados.
- `grep -rn 'All required signals present' solgreen` → sin matches.
- `grep -rn 'len(available) == len(rule.signals_required)'` → vacío.
- `package-lock.json` sin rutas locales ni tokens.
- Seriales redactados mantenidos.

## Comportamiento del catálogo seed

5 reglas seed (DATA-001, BAT-001, PV-001, GRID-003, INV-002):
- Todas `implementation_status = planned`.
- `evaluate_rule_catalog` produce 5 outcomes `not_evaluable`.
- 0 RuleExecution persistidos.
- 0 reglas fired.
- Sin evidencia fabricada.
- LLM skipped sin reglas elegibles.

## Comportamiento del gate LLM

- `eligible_fired_rules` filtra: fired=True + evidence no vacía.
- Si no hay evidencia elegible: no se construye prompt, no se llama
  `provider.complete`, no se persiste interpretación.
- CLI informa: `LLM skipped: no validated fired-rule evidence`.

## Resultados de verificación

| Check | Resultado |
|---|---|
| `ruff check .` | All checks passed |
| `ruff format --check .` | 99 files already formatted |
| `mypy solgreen` | 57 files, 0 issues |
| `pytest --cov --cov-fail-under=80` | 442 passed, 90.78% |
| Frontend `npm ci` | 200 packages |
| Frontend `typecheck` | ✓ |
| Frontend `test` | 4/4 |
| Frontend `build` | 190 KB JS, 14 KB CSS |

## Comandos de reproducibilidad

```bash
# Python
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest --cov=solgreen --cov-fail-under=80

# Frontend
cd apps/web
npm ci --no-audit --no-fund
npm run typecheck
npm run test
npm run build
```

## Matriz de dimensiones de calidad

| Dimensión | Implementada | En score global | Requiere perfil real |
|---|---|---|---|
| completeness | Sí | No (None sin expectativa) | No |
| temporal_coverage | Sí | Sí (peso 0.40) | No |
| duplicate_integrity | Sí | Sí (peso 0.60) | No |
| plausibility_score | Sí | No (reservado) | Parcialmente |
| consistency_score | Sí | No (reservado) | Sí |
| confidence | Separada de severidad | No | Sí |
| severity | No calculada por calidad | No | Requiere reglas |

## Archivos y módulos principales

- `solgreen/quality/_types.py` — QualityDimensions, QualityResult
- `solgreen/quality/score.py` — compute_temporal_dimensions, aggregate_quality_score
- `solgreen/quality/_plausibility_types.py` — PlausibilityFinding, PlausibilityResult
- `solgreen/quality/plausibility.py` — evaluate_inverter_telemetry, evaluate_plant_flow
- `solgreen/quality/_consistency_types.py` — ConsistencyPair, ConsistencyResult
- `solgreen/quality/consistency.py` — evaluate_consistency, apply_consistency_to_dimensions
- `solgreen/timeline/duration.py` — parse_iso_duration
- `solgreen/diagnostics/rule_evaluation.py` — evaluate_rule_catalog, eligible_fired_rules
- `solgreen/diagnostics/rule.py` — RuleImplementationStatus, RuleExecution
- `solgreen/timeline/join.py` — join_by_tolerance (grid fix)
- `solgreen/timeline/canonical.py` — CanonicalSample (grid description)

## Limitaciones

- El frontend usa datos demostrativos; no existe importación web real
  ni API de análisis conectada.
- No existe motor de energía W→Wh/kWh (U2).
- Signos de red y batería no están confirmados para la instalación real.
- No existen perfiles reales de plausibilidad o consistencia para Casabero.
- No existen pares automáticos de potencia entre fuentes (flow vs telemetry).
- El agrupador actual por gaps no es detector científico de eventos.
- El `#21` permanece abierto para detección científica de eventos U3.
- Los evaluadores científicos y algoritmos de reglas no existen (U3).
- El `#20` permanece abierto.
- No se ejecutan golden cases privados en CI.
- No existe motor tarifario vigente.
- No existe diagnóstico IA real.
- No existe control del inversor (AFCI, actualizaciones).
- No existe PDF ni deploy productivo.
- U0 conserva human gate visual (revisión pendiente del propietario).
- Merge sigue siendo human gate.

## Issues relacionados

| Issue | Relación | Estado |
|---|---|---|
| #20 | Evaluadores determinísticos | Abierto; U1.6 neutraliza el comportamiento inseguro |
| #21 | Semántica timeline y eventos | Abierto; cero/status resuelto en rama |
| #24 | Parser ISO duración | Resuelto en rama; pendiente merge a main |
| #25 | Formato global Python | Resuelto en rama; pendiente merge a main |
| #26 | Epic línea unificada | Abierto; U1 cerrado técnicamente |

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

## Próximo paso exacto

**U2.0** — Energy semantics, sign profiles and integration contract discovery.
