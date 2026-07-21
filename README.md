# Solgreen

**Solgreen** es un sistema científico y económico para analizar plantas solares híbridas. Convierte telemetría SolarMAN, datos del inversor y facturas en resultados reproducibles, asistidos por IA pero gobernados por física, reglas determinísticas, perfiles versionados y evidencia trazable.

## Propósito

Transformar datos técnicos y económicos en:

- importaciones canónicas reproducibles;
- indicadores de calidad y cobertura;
- métricas físicas de paneles, MPPT, batería, inversor y red;
- eventos correlacionados con evidencia;
- análisis de factura Afinia y perfiles horarios;
- recomendaciones de cargas con restricciones;
- visualizaciones React + D3 verificables;
- interpretaciones IA que no alteran cálculos;
- reportes técnicos para mantenimiento y decisión humana.

## Principio rector

```text
Datos originales
  → calidad y sincronización
  → cálculos físicos y económicos determinísticos
  → eventos, reglas y evidencia
  → visualización Showcase Ink
  → interpretación IA validada
  → decisión humana
```

La IA no inventa hechos, no calcula energía, factura, subsidio o severidad, y no cambia configuraciones.

## Línea única de desarrollo

Solgreen se consolida en una sola línea:

```text
main → develop/solgreen-unified → un único PR activo
```

- `main` conserva estados verificados.
- `develop/solgreen-unified` integra backend, motor científico, economía, frontend, IA, reportes y operación.
- No se mantienen pistas funcionales paralelas.
- El roadmap canónico está en [`docs/phases/UNIFIED_DEVELOPMENT_LINE.md`](docs/phases/UNIFIED_DEVELOPMENT_LINE.md).

## Estado

Solgreen está en **pre-alpha técnico**.

| Loop unificado | Resultado | Estado |
|---|---|---|---|
| U0 | Fundación única, economía E0 y frontend Showcase Ink | TECHNICALLY VERIFIED, HUMAN GATE PENDING |
| U1 | Calidad avanzada, semántica y safety gates | ENGINEERING CLOSED |
| U2 | Energía y métricas físicas | NEXT PLANNED |
| U3 | Eventos, reglas y golden cases | PLANNED |
| U4 | Frontend conectado y Human-First E2E | PLANNED |
| U5 | Motor económico Afinia y cargas | FOUNDATION ABSORBED |
| U6 | IA validada con evidencias estables | BLOCKED BY U3 |
| U7 | PDF, deploy y operación | PLANNED |

La auditoría del baseline está en [`docs/qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](docs/qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md).

> Las reglas seed, los episodios actuales y la integración LLM son experimentales. No deben emitir diagnósticos reales hasta cerrar U3 y sus golden cases. Las seed rules están explícitamente marcadas como `planned` (no implementadas); el LLM se omite cuando no existe evidencia de reglas fired validada.

## Frontend

La primera vertical vive en [`apps/web`](apps/web) y aplica exclusivamente **Casabero Showcase Ink**:

- Ink Console para dashboard y análisis;
- Ink Form para importación, filtros y escenarios;
- Ink Editorial para reportes dentro de la aplicación.

Incluye:

- React + TypeScript + Vite;
- D3 modular para escalas y paths;
- navegación Planta, Datos y Economía;
- periodos 24h, 7d y 30d;
- modo oscuro global;
- gráfica con tabla alternativa;
- estados estructurales y accesibles;
- bloqueo explícito de cifras COP sin tarifa vigente;
- datos demostrativos persistentemente señalados.

No incluye todavía carga web real ni conexión con análisis de planta. La interfaz no finge esas capacidades.

## Inteligencia económica

La fundación Afinia está integrada en la misma línea:

- [`docs/domain/ECONOMIC_INTELLIGENCE.md`](docs/domain/ECONOMIC_INTELLIGENCE.md)
- [`docs/domain/data-dictionary/afinia-billing.md`](docs/domain/data-dictionary/afinia-billing.md)
- [`docs/decisions/ADR-005-economic-intelligence-deterministic-first.md`](docs/decisions/ADR-005-economic-intelligence-deterministic-first.md)
- [`docs/product/04-economic-intelligence-workflows.md`](docs/product/04-economic-intelligence-workflows.md)
- [`docs/qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md`](docs/qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md)

La factura oficial y el medidor fiscal conservan autoridad. Los perfiles históricos no representan tarifas vigentes.

## Fuentes iniciales

1. Flujo de planta SolarMAN, 12 variables.
2. Telemetría técnica del inversor, 120 variables.
3. Facturas y perfiles tarifarios privados, versionados y redactados.

Los archivos reales permanecen fuera de Git. El repositorio usa fixtures sintéticos y hashes.

## Arquitectura

```text
apps/web React + D3
        ↓ REST/SSE
FastAPI API
        ↓
servicios determinísticos de importación, calidad, timeline,
métricas, eventos, economía, IA y reportes
        ↓
PostgreSQL + object storage + workers
```

## Desarrollo backend

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest --cov=solgreen --cov-fail-under=80
```

Uso actual de importación:

```bash
uv pip install . --no-deps
uv run solgreen import -f tests/fixtures/flow_small.csv -o out/ --no-db
uv run solgreen import -f tests/fixtures/telemetry_small.csv -o out/ --no-db
```

## Desarrollo frontend

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run typecheck
npm run test
npm run build
npm run dev
```

El `package-lock.json` está versionado para instalaciones reproducibles.

## Documentación clave

- [`AGENTS.md`](AGENTS.md)
- [`docs/domain/FOUNDATIONS.md`](docs/domain/FOUNDATIONS.md)
- [`docs/architecture/00-architecture.md`](docs/architecture/00-architecture.md)
- [`docs/frontend/FRONTEND_ARCHITECTURE.md`](docs/frontend/FRONTEND_ARCHITECTURE.md)
- [`docs/phases/UNIFIED_DEVELOPMENT_LINE.md`](docs/phases/UNIFIED_DEVELOPMENT_LINE.md)
- [`docs/phases/LOOP_REGISTRY.md`](docs/phases/LOOP_REGISTRY.md)
- [`docs/phases/NEXT_STEPS.md`](docs/phases/NEXT_STEPS.md)
- [`docs/qa_reports/TEST_PLAN.md`](docs/qa_reports/TEST_PLAN.md)
- [`docs/qa_reports/FRONTEND_FOUNDATION_TEST_PLAN.md`](docs/qa_reports/FRONTEND_FOUNDATION_TEST_PLAN.md)

## Metodología

```text
DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT
```

Código, tests y documentación avanzan juntos. Ningún flujo crítico se cierra sin evidencia Human-First y ninguna recomendación operativa se presenta como certeza sin fuente, cobertura, límites y revisión humana.
