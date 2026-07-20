# Changelog

Todas las versiones siguen [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-20

### Loop L1 — Importación reproducible

Primera entrega funcional de Solgreen. Reconoce y parsea los dos formatos
SolarMAN observados (flujo de planta, telemetría técnica) sin UI ni IA, y
produce un `ImportBatch` con hash SHA-256, metadata y reporte.

#### Added

- **Contratos Pydantic v2** en `solgreen/contracts/`:
  - `PlantFlowSample` con las 12 columnas canónicas del flujo de planta y SOC
    acotado a 0–100.
  - `InverterTelemetrySample` con `signals: dict[str, float|str|None]`
    validado contra `SIGNAL_SPECS` (120 entradas).
  - `ImportBatch`, `ImportMetadata`, `QualitySummary` con validación
    regex de SHA-256 y semver.
  - `ValidityFlags` + `ValidityReason` para distinguir
    `null` vs `0` vs `not_applicable` vs `suppressed`.
- **Parsers** en `solgreen/importer/parsers/`:
  - `solarman_flow_csv.py` + `solarman_flow_xlsx.py`
  - `solarman_telemetry_csv.py` + `solarman_telemetry_xlsx.py`
  - `registry.py` con `parse_with` / `iter_with` que selecciona parser por
    `SourceType` + extensión.
- **Detector de formato** en `solgreen/importer/detector.py` que reconoce
  los dos formatos por heurística de header (5 / 6 columnas discriminantes).
- **Hashing** en `solgreen/core/hashing.py` con streaming por chunks de 1 MiB.
- **Normalización de tiempo** en `solgreen/core/time.py` que respeta la
  `Zona horaria` por fila y devuelve `(original, utc, label)`.
- **Profiles** en `solgreen/profiles/`: carga `config/plant-profiles/*.yaml`
  y `config/grid-profiles/*.yaml` con alias generator camelCase → snake_case.
- **CLI `solgreen`** con typer:
  - `solgreen --version`
  - `solgreen import -f file.csv -o out/ --plant-id casabero`
- **Reporter** en `solgreen/importer/reporter.py` que escribe
  `<stem>.import.json` + `<stem>.import.md` por archivo.
- **Fixtures sintéticos** en `tests/fixtures/` reproducibles por
  `tests/fixtures/_generate.py` con semilla RNG fija.
- **ADR-004** que explica por qué `signals` es `dict` y no 120 atributos.

#### Quality

- 73 tests unitarios + integration
- 93.41 % de cobertura
- ruff check + format
- mypy strict (27 source files)
- CI con 2 jobs: `python` (uv + ruff + mypy + pytest) y `documentation`
  (valida docs obligatorios y rechaza exports privados reales)

#### Limitaciones conocidas

- El entry point `solgreen` requiere `pip install .` (no `-e`) en este
  entorno por un quirk de uv + editable install + src-layout. Migrado
  a flat layout en iter 5.
- Sin análisis de calidad de datos (huecos, duplicados, SOC imposible).
  Entra en L2.
- Sin reglas, episodios, IA, UI, DB. L3 en adelante.
- Sin golden dataset privado; SOLO fixtures sintéticos en repo.
- XLSX sin validación estricta de número de columnas en telemetría para
  tolerar archivos truncados; el parser de flow sí exige exactamente 12.

### Changed

- Build backend migrado de `hatchling` a `setuptools`.
- Layout migrado de `src/solgreen/` a `solgreen/` plano.

### Security

- Seriales siempre redactados como `redacted:XXXX` antes de persistirse.
- `tests/fixtures/` es la única ruta donde se permiten `.csv` sintéticos
  en CI; exports reales SolarMAN excluidos por `.gitignore` y por el job
  `documentation` del workflow.