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

La IA **no inventa hechos, no calcula la severidad eléctrica y no cambia configuraciones**. Su papel es explicar, comparar hipótesis, relacionar documentación y convertir evidencia en recomendaciones comprensibles.

## Fuentes iniciales

Solgreen inicia con dos formatos SolarMAN:

1. **Flujo de planta**, 12 variables: producción, consumo, red, batería y SOC.
2. **Telemetría técnica del inversor**, 120 variables: MPPT, L1/L2, batería, BUS, temperaturas, estados, versiones y acumulados.

Los datasets reales no se versionan en Git. Se usarán fixtures sintéticos y hashes de los archivos privados como evidencia.

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

## Estado

**Loop L1 — Importación reproducible** en curso (PR por iteración). L0 foundation freeze cerrado.

## Desarrollo

```bash
# requisitos: Python 3.12+, uv 0.11+
uv sync --extra dev
uv run pytest          # 18+ tests, cobertura >= 80%
uv run ruff check .    # lint
uv run ruff format .   # format
uv run mypy src        # type-check estricto
```

Stack: Python 3.12, Pydantic v2, Polars, openpyxl, typer, PyYAML, pytest, ruff, mypy. Ver `pyproject.toml` y ADR-003.

## Reglas del repositorio

Este proyecto sigue `casabero-labs/estandar-casabero`.

- cambios pequeños y verificables;
- arquitectura por contratos;
- secretos solo en Infisical;
- documentación y tests como evidencia;
- IA con salidas estructuradas y referencias exactas;
- ninguna recomendación operativa se presenta como certeza sin fuente y confianza explícitas.
