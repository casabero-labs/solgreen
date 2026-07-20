# Changelog

Todas las versiones siguen [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Reconciliation R0

- Auditoría del estado real frente a `estandar-casabero`.
- README, Loop Registry y Next Steps reconciliados con main.
- Timeline, episodios, reglas, IA, persistencia y deploy reclasificados según evidencia.
- Reglas seed marcadas como catálogo experimental hasta contar con evaluadores determinísticos.
- IA bloqueada para diagnóstico real mientras no existan evidencias estructuradas y reglas evaluadas.
- PR económico #8 reconocido como divergido y pendiente de rebase.

### Riesgos conocidos

- El agrupador actual separa por gaps y no constituye todavía un detector de episodios diagnósticos.
- El motor de métricas físicas aún no existe.
- Los golden cases del 17 y 19 de julio todavía no se ejecutan en CI.
- La persistencia y el deploy requieren evidencia operativa documentada.

## [0.1.0] - 2026-07-20

### Loop I1 — Importación reproducible

Primera entrega funcional de Solgreen. Reconoce y parsea los dos formatos SolarMAN observados y produce un `ImportBatch` con hash SHA-256, metadata y reporte.

#### Added

- Contratos Pydantic v2 para flujo de planta, telemetría, importación y validez.
- Catálogo de 120 señales técnicas.
- Parsers CSV/XLSX para flujo de planta y telemetría.
- Detector de formato.
- Hashing SHA-256.
- Normalización temporal a UTC conservando origen.
- Perfiles de planta y red.
- CLI `solgreen import`.
- Reportes JSON y Markdown.
- Fixtures sintéticos reproducibles.
- ADR-004 para el contrato de señales.

#### Quality reportada en el cierre de I1

- 73 tests.
- 93,41 % de cobertura.
- Ruff, formatter y mypy strict declarados como correctos en el PR de cierre.

Estos valores corresponden al cierre histórico de I1 y no describen automáticamente el estado actual de main.

#### Limitaciones históricas

- Sin métricas físicas ni golden dataset privado.
- XLSX de telemetría tolera archivos parciales.
- Los datasets reales permanecen fuera de Git.

### Changed

- Build backend migrado de Hatchling a setuptools.
- Layout migrado de `src/solgreen/` a `solgreen/` plano.

### Security

- Seriales redactados antes de persistirse.
- Exports reales excluidos del repositorio.
