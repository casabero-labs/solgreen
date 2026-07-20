# Solgreen

**Solgreen** es un sistema científico de análisis, prevención y diagnóstico para plantas solares híbridas, asistido por IA pero gobernado por física, reglas determinísticas, estadística robusta y evidencia trazable.

## Propósito

Transformar exportaciones de SolarMAN, telemetría técnica del inversor y documentos económicos en:

- datos canónicos reproducibles;
- indicadores de salud de paneles, MPPT, batería, inversor y red;
- episodios técnicos correlacionados;
- detección de anomalías y riesgos;
- visualizaciones D3.js verificables;
- interpretaciones de IA con evidencia enlazada;
- reportes técnicos para instaladores y mantenimiento preventivo;
- estimación y conciliación de facturas;
- proyección económica con incertidumbre;
- perfiles de consumo, producción y compra por hora;
- recomendaciones conservadoras de desplazamiento de cargas;
- simulaciones `what-if` sin control automático del sistema.

## Principio rector

```text
Datos originales
  → validación y sincronización
  → cálculos físicos y económicos determinísticos
  → estadística robusta
  → episodios, perfiles y evidencia
  → interpretación IA validada
  → decisión humana
```

La IA **no inventa hechos, no calcula la severidad eléctrica, no calcula facturas y no cambia configuraciones**. Su papel es explicar, comparar hipótesis, relacionar documentación y convertir evidencia en recomendaciones comprensibles.

## Fuentes iniciales

Solgreen inicia con dos formatos SolarMAN:

1. **Flujo de planta**, 12 variables: producción, consumo, red, batería y SOC.
2. **Telemetría técnica del inversor**, 120 variables: MPPT, L1/L2, batería, BUS, temperaturas, estados, versiones y acumulados.

La pista económica añade de forma incremental:

3. **Facturas y perfiles tarifarios versionados**, siempre subordinados al recibo oficial, vigencia y revisión humana.
4. **Catálogo doméstico de cargas**, declarado por el usuario o medido en el futuro por enchufes y circuitos.

Los datasets y recibos reales no se versionan en Git. Se usarán fixtures sintéticos, hashes y golden cases privados como evidencia.

## Alcance inicial

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

## Pista económica planificada

La inteligencia económica se desarrolla como una pista paralela que **no desplaza L2 ni contamina el diagnóstico eléctrico**:

- motor de factura parametrizado;
- conciliación SolarMAN frente a factura y medidor fiscal;
- forecast P10/P50/P90;
- análisis horario en kWh;
- recomendaciones de cargas con restricciones;
- simulador de escenarios;
- explicación IA sobre resultados existentes.

Su implementación confiable depende de calidad de datos, timeline canónico y métricas físicas. Los valores históricos de recibos solo son objetivos de regresión, nunca tarifas vigentes.

## Documentación clave

- [`docs/product/00-idea.md`](docs/product/00-idea.md)
- [`docs/product/00-foundation-card.md`](docs/product/00-foundation-card.md)
- [`docs/product/04-economic-intelligence-workflows.md`](docs/product/04-economic-intelligence-workflows.md)
- [`docs/domain/FOUNDATIONS.md`](docs/domain/FOUNDATIONS.md)
- [`docs/domain/DATA_CONTRACTS.md`](docs/domain/DATA_CONTRACTS.md)
- [`docs/domain/RULE_CATALOG.md`](docs/domain/RULE_CATALOG.md)
- [`docs/domain/ECONOMIC_INTELLIGENCE.md`](docs/domain/ECONOMIC_INTELLIGENCE.md)
- [`docs/domain/data-dictionary/afinia-billing.md`](docs/domain/data-dictionary/afinia-billing.md)
- [`docs/architecture/00-architecture.md`](docs/architecture/00-architecture.md)
- [`docs/decisions/ADR-005-economic-intelligence-deterministic-first.md`](docs/decisions/ADR-005-economic-intelligence-deterministic-first.md)
- [`docs/phases/LOOP_REGISTRY.md`](docs/phases/LOOP_REGISTRY.md)
- [`docs/phases/NEXT_STEPS.md`](docs/phases/NEXT_STEPS.md)
- [`docs/qa_reports/TEST_PLAN.md`](docs/qa_reports/TEST_PLAN.md)
- [`docs/qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md`](docs/qa_reports/ECONOMIC_INTELLIGENCE_TEST_PLAN.md)

## Estado

**Loop L1 — Importación reproducible CERRADO** (5 PRs mergeados, ver `CHANGELOG.md`).

L2 — Data quality (huecos, duplicados, SOC imposible) pendiente y permanece como próximo loop técnico.

La fundación documental **E0 — Inteligencia económica** está integrada en una pista paralela. E1+ no inicia hasta cerrar sus dependencias declaradas.

L3+ — Timeline canónico, métricas físicas, reglas, episodios, IA, UI, reportes y deploy. Ver `docs/phases/LOOP_REGISTRY.md`.

## Uso

```bash
# 1) Instalar (entrada por CLI requiere wheel, no editable)
uv sync --extra dev
uv pip install . --no-deps

# 2) Importar un archivo SolarMAN
uv run solgreen import -f tests/fixtures/flow_small.csv -o out/
# Genera:
#   out/flow_small.import.json   (batch + calidad + validez)
#   out/flow_small.import.md     (reporte humano)

uv run solgreen import -f tests/fixtures/telemetry_small.csv -o out/
#   out/telemetry_small.import.json
#   out/telemetry_small.import.md
```

## Desarrollo

```bash
# requisitos: Python 3.12+, uv 0.11+
uv sync --extra dev
uv run pytest            # 73 tests, cobertura >= 80% (actual 93.41%)
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy solgreen     # type-check estricto
```

Stack: Python 3.12, Pydantic v2, Polars, openpyxl, typer, PyYAML, pytest, ruff, mypy. Ver `pyproject.toml`, `ADR-003` (Python engine), `ADR-004` (signals dict) y `ADR-005` (economía deterministic-first).

## Reglas del repositorio

Este proyecto sigue `casabero-labs/estandar-casabero`.

- cambios pequeños y verificables;
- arquitectura por contratos;
- secretos solo en Infisical;
- documentación y tests como evidencia;
- IA con salidas estructuradas y referencias exactas;
- ninguna recomendación operativa o económica se presenta como certeza sin fuente, vigencia, supuestos y confianza explícitas.
