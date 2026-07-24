# Plan ejecutable — Solgreen

## Baseline estable

- Rama: `main`
- SHA de reconciliación: `5cfb9fbb803da1f46d7ac50297c30b1fa96f3ff8`
- Auditoría: [`../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md)

## Línea activa

- Rama: `develop/solgreen-unified`
- Epic: #26
- Pull request activo: #31 (U2.2a temporal integration)
- Política: un solo PR activo contra `main`
- Roadmap: [`UNIFIED_DEVELOPMENT_LINE.md`](UNIFIED_DEVELOPMENT_LINE.md)
- QA report U1: [`../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md`](../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md)

El PR económico #8 fue cerrado como supersedido. Su fundación E0 fue absorbida en esta línea y no continúa como pista separada. El PR #27 (línea unificada) fue mergeado a `main`.

## Estado U0

Técnicamente verificado en la línea unificada; pendiente de revisión humana
visual y funcional. Evidencia:
[`../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md`](../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md).

## Estado U1 — ENGINEERING CLOSED

### Verificado en la línea unificada

- semántica de cero y estado (cero medido preservado, estado textual conservado);
- dimensiones de calidad separadas (completeness, temporal_coverage,
  duplicate_integrity, plausibility_score, consistency_score);
- plausibilidad universal (NaN/Inf, SOC 0–100, temperatura ≥ −273.15 °C)
  y rangos configurables por perfil;
- consistencia entre fuentes solo con pares declarados en perfil;
- parser ISO 8601 puro, testeado, con validación antes de side effects;
- formato global Python normalizado (`ruff format .`);
- `package-lock.json` versionado, `npm ci` reproducible;
- reglas seed explícitamente `planned` (ninguna dispara por presencia
  de señales); evaluadores científicos diferidos a U3;
- gate LLM: sin regla fired con evidencia, no se llama al proveedor.

### Comandos de desarrollo

#### Backend

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest --cov=solgreen --cov-fail-under=80
```

#### Frontend

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run typecheck
npm run test
npm run build
```

### Pendiente o bloqueado

- eventos científicos y evaluadores determinísticos (U3);
- golden cases privados;
- endpoints de frontend;
- motor tarifario;
- IA validada;
- PDF y deploy verificable.

El issue #21 permanece abierto para detección científica de eventos (U3).
Los issues #24 y #25 están resueltos.
El issue #20 sigue abierto para evaluadores U3.

## Estado U2.1 — ENGINEERING COMPLETE (PR #27, merged)

- PowerSignProfile con per-direction evidence status (ADR-009).
- Normalización direccional implementada (grid_import, grid_export, battery_charge, battery_discharge, pv_generation, load_consumption).
- Profile registry con seeds de producción y telemetría.
- SOLARMAN operational sync implementado.
- CI corre en PRs a `main` y `develop/solgreen-unified`.

## Estado U2.2a — ACTIVE (PR #31)

- `solgreen/energy/integration.py`: `DirectionalPowerObservation`, `IntegrationProfile`, `EnergyInterval`, `EnergySummary`, `IntegrationResult`.
- Integración trapezoidal W→Wh para series homogéneas direccionales.
- Sample semantics `instantaneous` como único soportado.
- Política de gaps explícita: missing, excluded_nonfinite, excluded_zero_duration, excluded_unconfirmed_sign.
- Boundary accounting: leading y trailing gaps cuentan como missing.

## Próximo paso exacto

**U2.3a** — Grid import/export energy metrics and persistence contracts.
Métricas de red (import/export), sin billing, sin tarifas, sin frontend.

Evidencia U2.2b:
- [`solgreen/integrations/solarman/energy_runtime.py`](../../solgreen/integrations/solarman/energy_runtime.py)
- [`tests/unit/test_energy/test_energy_runtime.py`](../../tests/unit/test_energy/test_energy_runtime.py)
- [`docs/qa_reports/U2_2B_SOLARMAN_ENERGY_RUNTIME_RESULTS_2026-07-24.md`](../qa_reports/U2_2B_SOLARMAN_ENERGY_RUNTIME_RESULTS_2026-07-24.md)
