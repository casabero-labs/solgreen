# Changelog

Todas las versiones siguen [Semantic Versioning](https://semver.org/).

## [Unreleased]

### U2.0 — Energy semantics, sign profiles and integration contract discovery

#### Added

- `docs/domain/ENERGY_SEMANTICS.md` — Complete signal inventory (23+
  signals), AC/DC matrix, authority hierarchy, sign conventions,
  conceptual contracts for PowerSignProfile, directional normalization,
  and temporal integration.
- `docs/decisions/ADR-008-energy-integration-and-sign-profiles.md` —
  Architectural decision establishing versioned sign profiles,
  directional magnitude contracts, temporal integration dependencies,
  gap and coverage policies, and human gates. Status: Proposed.
- `docs/qa_reports/U2_ENERGY_DISCOVERY_2026-07-21.md` — Discovery QA
  report documenting signal inventory, authority matrix, sign matrix,
  uncertainties, risks, proposed contracts, gap policy, coverage policy,
  and U2.1–U2.7 implementation plan.

#### Discovered

- 7 power signals in CanonicalSample: 6 provisional, 1 unknown sign convention.
- 16+ additional power/energy signals available but not yet in CanonicalSample.
- PV power is DC (`telemetry_pv_power_w` from MPPT) while flow production
  is AC — cannot be directly compared without inverter efficiency.
- `flow_battery_w` documented as negative=charge, positive=discharge but
  PlantFlowSample claims parser normalizes while parser does not.
- `telemetry_battery_power_w` sign convention is completely unknown.
- No sign has been confirmed with human gate evidence.
- No Wh or kWh has been calculated.

#### Changed

- `docs/phases/LOOP_REGISTRY.md` — U2 status from NEXT_PLANNED to
  DISCOVERY_COMPLETE_HUMAN_GATE_PENDING; added U2.0 entry.
- `docs/phases/NEXT_STEPS.md` — Updated next step to U2.1 with human gate
  dependencies.
- `docs/phases/UNIFIED_DEVELOPMENT_LINE.md` — U2 status updated; U2.0
  content added with artifacts and U2.1–U2.7 plan.
- `docs/qa_reports/TEST_PLAN.md` — Added U2 section with test plans
  for U2.0–U2.7.

#### Known limitations

- No PowerSignProfile implementation or sign normalization (U2.1).
- No temporal integration W→Wh (U2.2).
- No directional energy metrics (U2.3–U2.5).
- No physical balance equations.
- All grid and battery signs remain provisional or unknown.
- Human gates for sign confirmation not yet executed.

### U1 — Calidad avanzada, semántica y safety gates

#### Added

- `get_text(canonical_name)` en `InverterTelemetrySample` para preservar
  señales textuales independientemente del tipo numérico.
- `QualityDimensions` (completeness, temporal_coverage,
  duplicate_integrity, plausibility_score, consistency_score).
- `QualityResult.dimensions` manteniendo `quality_score` como campo
  serializado.
- `MeasurementPlausibilityProfile`, `MeasurementRange`, `PlausibilityFinding`
  y `PlausibilityResult` para plausibilidad basada en perfil.
- `ConsistencyPair`, `MeasurementConsistencyProfile` y `ConsistencyResult`
  para consistencia entre fuentes basada en perfil.
- Parser `parse_iso_duration(value: str) -> timedelta` con soporte ISO 8601
  (D/H/M/S + fraccionales hasta 6 dígitos).
- `RuleImplementationStatus`, `RuleEvaluationOutcome`,
  `RuleEvaluatorRegistry`, `eligible_fired_rules` y `evaluate_rule_catalog`
  para evaluación defensiva de reglas.
- `apply_consistency_to_dimensions(dimensions, canonical_samples, profile)`
  como función separada del análisis de una sola fuente.
- `docs/qa_reports/U1_DATA_QUALITY_RESULTS_2026-07-21.md`.

#### Changed

- `telemetry_grid_power_w` ahora se alimenta de
  `total_active_power_of_the_grid_w` (no `potencia_total_ca_w`).
- `telemetry_inverter_state` usa `get_text` en ambas rutas
  (merged y telemetry-only).
- `compute_quality_score` (single-float) reemplazado por
  `compute_temporal_dimensions` y `aggregate_quality_score` con
  pesos nombrados (`DUPLICATE_INTEGRITY_WEIGHT=0.60`,
  `TEMPORAL_COVERAGE_WEIGHT=0.40`).
- Calidad temporal: huecos ponderados por duración, no por cantidad.
- CLI `import`: tolerancia se valida antes de `mkdir`, `_build_repository`,
  `_build_llm_provider` y `_parse_single_file`.
- Formato normalizado en todo el repositorio (`ruff format .`).
- CI usa `ruff format --check --diff .` (global, no incremental).
- CI usa `npm ci` en lugar de `npm install`.
- Documentación canónica reconciliada con el estado ENGINEERING_CLOSED de U1.

#### Fixed

- `_pv_power`: `pv1 or pv2` reemplazado por ramas `is not None` explícitas.
- `compute_quality_score(total_rows=0)` ya no devuelve 1.0.
- `_parse_iso_duration` reemplazado por parser propio y testeado;
  mypy override eliminado.
- `_evaluate_rules` eliminado; ya no dispara reglas por presencia de
  señales. Cinco seed rules producen `not_evaluable`.
- `PlausibilityResult` invariante: `evaluated_count == passed_count + failed_count`.
- `ConsistencyResult` invariante: mismo patrón.

#### Safety

- Seed rules declaradas `implementation_status=planned`.
- `evaluate_rule_catalog` con registro vacío de producción → 0 RuleExecution
  persistidos para seed rules.
- `eligible_fired_rules` filtra fired=True con evidence no vacía.
- `_run_llm_interpretation` salta sin evidencia elegible:
  sin prompt, sin `provider.complete`, sin persistencia.
- CLI reporta: `LLM skipped: no validated fired-rule evidence`.

#### Known limitations

- Sin motor de energía W→Wh/kWh (U2).
- Sin evaluadores científicos de reglas (U3).
- Sin detección de eventos con ventanas antes/durante/después (U3).
- Sin perfiles reales de plausibilidad o consistencia para Casabero.
- Sin confirmación de signos de red y batería.
- Frontend demo, no conectado.
- #20 y #21 permanecen abiertos para U3.

- R0 fusionado como baseline estable.
- Desarrollo consolidado en `develop/solgreen-unified` con un solo PR activo.
- PR económico #8 cerrado como supersedido y fundación E0 absorbida.
- Dominio, ADR, diccionario Afinia, workflows, perfil histórico y test plan económico integrados.
- Primera aplicación `apps/web` con React, TypeScript, Vite y D3.
- Navegación Planta, Datos y Economía.
- Periodos demostrativos 24h, 7d y 30d.
- Modo oscuro global.
- Gráfica D3 con tabla alternativa accesible.
- Datos demo persistentemente identificados.
- Bloqueo explícito de COP sin perfil tarifario vigente.
- Acción de importación web deshabilitada hasta contar con API y E2E Human-First.
- Arquitectura y test plan frontend añadidos.
- CI ampliada con typecheck, tests, build y guardas Showcase Ink.

### Reconciliation R0

- Auditoría del estado real frente a `estandar-casabero`.
- README, Loop Registry y Next Steps reconciliados con main.
- Timeline, episodios, reglas, IA, persistencia y deploy reclasificados según evidencia.
- Reglas seed marcadas como catálogo experimental hasta contar con evaluadores determinísticos.
- IA bloqueada para diagnóstico real mientras no existan evidencias estructuradas y reglas evaluadas.
- CI documental y privacidad restauradas.

### Riesgos conocidos

- El agrupador actual separa por gaps y no constituye todavía un detector de episodios diagnósticos.
- El motor de métricas físicas aún no existe.
- Los golden cases del 17 y 19 de julio todavía no se ejecutan en CI.
- La persistencia y el deploy requieren evidencia operativa documentada.
- El frontend U0 usa datos demostrativos y aún no consume la API.
- El perfil Afinia versionado en Git es referencia histórica, no tarifa vigente.

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
