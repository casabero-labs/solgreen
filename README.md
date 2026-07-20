# Solgreen

**Solgreen** es un sistema científico de análisis, prevención y diagnóstico para plantas solares híbridas, asistido por IA pero gobernado por física, reglas determinísticas, estadística robusta y evidencia trazable.

## Propósito

Transformar exportaciones de SolarMAN y telemetría técnica del inversor en:

- datos canónicos reproducibles;
- indicadores de salud de paneles, MPPT, batería, inversor y red;
- episodios técnicos correlacionados;
- detección de anomalías y riesgos;
- visualizaciones D3.js verificables;
- interpretaciones de IA con evidencia enlazada;
- reportes técnicos para instaladores y mantenimiento preventivo.

## Principio rector

```text
Datos originales
  → validación y sincronización
  → cálculos físicos determinísticos
  → estadística robusta
  → episodios y evidencia
  → interpretación IA validada
  → decisión humana
```

La IA **no inventa hechos, no calcula severidad eléctrica y no cambia configuraciones**. Su papel es explicar, comparar hipótesis, relacionar documentación y convertir evidencia válida en recomendaciones comprensibles.

## Fuentes iniciales

Solgreen inicia con dos formatos SolarMAN:

1. **Flujo de planta**, 12 variables: producción, consumo, red, batería y SOC.
2. **Telemetría técnica del inversor**, 120 variables: MPPT, L1/L2, batería, BUS, temperaturas, estados, versiones y acumulados.

Los datasets reales no se versionan en Git. Se usan fixtures sintéticos y hashes de archivos privados como evidencia.

## Estado real

Solgreen está en **pre-alpha técnico**.

| Track | Estado |
|---|---|
| I1 Importación SolarMAN | Cerrado |
| Q2 Calidad de datos | Parcial |
| T3 Timeline canónico | Parcial |
| M4 Métricas físicas | No iniciado |
| E5 Eventos y episodios | Prototipo temporal |
| R6 Reglas determinísticas | Catálogo sin evaluadores completos |
| A7 IA | Experimental y bloqueada para diagnóstico real |
| P8 PostgreSQL | Primera versión |
| U9 UI / D3 | No iniciado |
| G10 PDF técnico | No iniciado |
| O11 Operación | Parcial y no verificada |
| ECO Factura Afinia y cargas | Diseñada, no fusionada |

La auditoría vigente está en [`docs/qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](docs/qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md).

> **Advertencia:** las reglas seed y la integración LLM no deben usarse todavía para emitir diagnósticos sobre una planta real. El siguiente paso obligatorio es el loop correctivo R0.

## Alcance objetivo

- carga manual de CSV/XLSX;
- reconocimiento automático del formato;
- normalización temporal y semántica;
- análisis determinístico y estadístico;
- explorador temporal D3.js;
- catálogo versionado de reglas;
- integración MiniMax, DeepSeek y proveedores compatibles;
- validador estricto de salidas LLM;
- generación de informes técnicos PDF;
- despliegue self-hosted con Coolify e Infisical.

## Documentación clave

- [`docs/product/00-idea.md`](docs/product/00-idea.md)
- [`docs/product/00-foundation-card.md`](docs/product/00-foundation-card.md)
- [`docs/domain/FOUNDATIONS.md`](docs/domain/FOUNDATIONS.md)
- [`docs/domain/DATA_CONTRACTS.md`](docs/domain/DATA_CONTRACTS.md)
- [`docs/domain/RULE_CATALOG.md`](docs/domain/RULE_CATALOG.md)
- [`docs/architecture/00-architecture.md`](docs/architecture/00-architecture.md)
- [`docs/phases/LOOP_REGISTRY.md`](docs/phases/LOOP_REGISTRY.md)
- [`docs/phases/NEXT_STEPS.md`](docs/phases/NEXT_STEPS.md)
- [`docs/qa_reports/TEST_PLAN.md`](docs/qa_reports/TEST_PLAN.md)

## Uso actual

```bash
uv sync --extra dev
uv pip install . --no-deps

uv run solgreen import -f tests/fixtures/flow_small.csv -o out/ --no-db
uv run solgreen import -f tests/fixtures/telemetry_small.csv -o out/ --no-db
```

La alineación, persistencia y proveedores LLM existen como superficies experimentales. No deben interpretarse como validación científica del pipeline.

## Desarrollo

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest
```

Stack actual: Python 3.12, Pydantic v2, Polars, openpyxl, Typer, PyYAML, PostgreSQL, FastAPI, pytest, Ruff y mypy.

## Metodología

Este proyecto aplica obligatoriamente `casabero-labs/estandar-casabero`:

```text
DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT
```

- cambios pequeños, reversibles y verificables;
- arquitectura por contratos;
- fundamentos de dominio antes que implementación;
- documentación y tests como evidencia;
- secretos fuera del repositorio;
- IA con referencias estructuradas;
- ninguna recomendación operativa presentada como certeza sin fuente, evidencia y revisión humana.
