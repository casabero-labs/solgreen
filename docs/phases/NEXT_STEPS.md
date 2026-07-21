# Plan ejecutable — Solgreen

## Baseline estable

- Rama: `main`
- SHA de reconciliación R0: `1f70674f0a0d835c8933dc23f38f46f798a6facb`
- Auditoría: [`../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md)

## Línea activa

- Rama: `develop/solgreen-unified`
- Epic: #26
- Pull request único: #27
- Política: un solo PR activo contra `main`
- Roadmap: [`UNIFIED_DEVELOPMENT_LINE.md`](UNIFIED_DEVELOPMENT_LINE.md)
- QA report U1: [`../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md`](../qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md)

El PR económico #8 fue cerrado como supersedido. Su fundación E0 fue absorbida en esta línea y no continúa como pista separada.

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

- motor de energía W→Wh/kWh (U2);
- eventos científicos y evaluadores determinísticos (U3);
- golden cases privados;
- endpoints de frontend;
- motor tarifario;
- IA validada;
- PDF y deploy verificable.

El issue #21 permanece abierto para detección científica de eventos (U3).
Los issues #24 y #25 están resueltos en la rama; pendientes de merge a main.
El issue #20 sigue abierto para evaluadores U3.

## Próximo paso exacto

**U2.0** — Energy semantics, sign profiles and integration contract discovery.
