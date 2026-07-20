# Graph Report - .  (2026-07-20)

## Corpus Check
- Corpus is ~19,437 words - fits in a single context window. You may not need a graph.

## Summary
- 790 nodes · 1329 edges · 75 communities (48 shown, 27 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 94 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- CLI and Core Commands
- Data Models and Exceptions
- Battery and Data Quality Research
- Schema Type Definitions
- AI and Deployment
- Grid Profile Validation
- JSON Schema Definitions
- Schema Structure
- Schema Validation Files
- UI Screens and Components
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67

## God Nodes (most connected - your core abstractions)
1. `RULE_CATALOG.md` - 31 edges
2. `SourceType` - 28 edges
3. `Idea Brief` - 27 edges
4. `CATALOG — UI Screens and Components` - 26 edges
5. `ValidityFlags` - 23 edges
6. `PlantFlowSample` - 20 edges
7. `InverterTelemetrySample` - 19 edges
8. `parse_timestamp()` - 17 edges
9. `detect_format()` - 16 edges
10. `HeaderMismatchError` - 16 edges

## Surprising Connections (you probably didn't know these)
- `FOUNDATIONS.md` --conceptually_related_to--> `CanonicalSample`  [INFERRED]
  AGENTS.md → docs/domain/DATA_CONTRACTS.md
- `L5 — Catalogo de reglas v0.1` --conceptually_related_to--> `RULE_CATALOG.md`  [INFERRED]
  docs/phases/LOOP_REGISTRY.md → AGENTS.md
- `test_build_import_metadata_uses_path_when_sha_not_provided()` --indirect_call--> `ImportMetadata`  [INFERRED]
  tests/unit/test_hashing.py → solgreen/contracts/import_batch.py
- `FOUNDATIONS.md` --conceptually_related_to--> `Severity Concept`  [EXTRACTED]
  AGENTS.md → docs/domain/FOUNDATIONS.md
- `FOUNDATIONS.md` --conceptually_related_to--> `Sign Conventions`  [EXTRACTED]
  AGENTS.md → docs/domain/FOUNDATIONS.md

## Import Cycles
- None detected.

## Communities (75 total, 27 thin omitted)

### Community 0 - "CLI and Core Commands"
Cohesion: 0.06
Nodes (80): callback, Deterministic-First Approach, help, is_eager, Option, Two SolarMAN Formats (flow 12-var, telemetry 120-var), Solgreen, import_file() (+72 more)

### Community 1 - "Data Models and Exceptions"
Cohesion: 0.08
Nodes (50): ABC, Exception, openpyxl, Polars, SourceType, CorruptFileError, HeaderMismatchError, ImportError (+42 more)

### Community 2 - "Battery and Data Quality Research"
Cohesion: 0.05
Nodes (47): Anomaly detection initial stage methods, Anomaly detection later stage methods, Battery analysis methods, Battery degradation indirect estimation limitation, Battery signals, casabero.test plant profile, Data quality dimensions, Data quality rules (+39 more)

### Community 3 - "Schema Type Definitions"
Cohesion: 0.06
Nodes (37): maximum, minimum, type, format, type, format, type, items (+29 more)

### Community 4 - "AI and Deployment"
Cohesion: 0.07
Nodes (28): AI Orchestration, AIInterpretationService, AnalysisService, Butterbase Auth/RBAC, Coolify Deployment, Data Pipeline, Architecture Overview, Data Pipeline Architecture (+20 more)

### Community 5 - "Grid Profile Validation"
Cohesion: 0.14
Nodes (24): SignalValue, _CamelModel, GridNominal, GridProfile, GridThresholds, load_grid_profile(), BaseModel, Path (+16 more)

### Community 6 - "JSON Schema Definitions"
Cohesion: 0.07
Nodes (30): items, type, issue, items, type, uniqueItems, type, additionalProperties (+22 more)

### Community 7 - "Schema Structure"
Cohesion: 0.07
Nodes (29): additionalProperties, properties, required, type, $defs, action, type, enum (+21 more)

### Community 8 - "Schema Validation Files"
Cohesion: 0.08
Nodes (26): items, type, additionalProperties, type, $id, items, type, $ref (+18 more)

### Community 9 - "UI Screens and Components"
Cohesion: 0.07
Nodes (27): CATALOG — UI Screens and Components, AiLabPage, BatteryPage, BeforeDuringAfterPanel, ConfidenceMeter, DataGapMarker, DataQualityPage, EpisodeDetailPage (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (26): 5 minute sampling hides transients, Async workers, Coolify deployment, FastAPI Python backend, Infisical secrets, MiniMax and DeepSeek behind gateway, Object storage, PostgreSQL Butterbase (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (23): RULE_CATALOG.md, BAT-001 — SOC bajo, BAT-003 — Carga elevada, BAT-004 — Descarga elevada, BAT-005 — Caida de voltaje bajo carga, BAT-006 — SOC estancado o recalibrado, CORR-001 — Episodio multicapa, DATA-001 — Intervalo ausente (+15 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (17): ADR-004 signals dict decision, casabero-labs/estandar-casabero, D3.js, Visualization Architecture, ImportBatch Contract, InverterTelemetrySample Contract, Loop L1 — Importación reproducible, Loop L2 — Data Quality (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (18): Agent prohibitions, Authority sources, Batch, Confidence depends on evidence and data quality, Required contract tests, Data quality limits diagnostic confidence, Deterministic-first AI-assisted, Facts inferences hypotheses are distinct types (+10 more)

### Community 14 - "Community 14"
Cohesion: 0.27
Nodes (16): build_import_metadata(), compute_sha256(), iter_chunks(), datetime, IO, Path, _sha256_bytes(), _sha256_path() (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.27
Nodes (15): detect_format(), _normalize_columns(), Path, _read_csv_header(), _read_xlsx_header(), flow_csv(), garbage_csv(), Path (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (14): _label_for(), parse_timestamp(), datetime, _resolve_zone(), TimestampParseError, test_parse_timestamp_empty_raises(), test_parse_timestamp_explicit_offset_wins_over_source_tz(), test_parse_timestamp_explicit_utc_zulu() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (11): ADR-002 — Originales inmutables, Originals Immutable, DATA_CONTRACTS.md, CanonicalSample, ImportBatch, PlantFlowSample, RuleExecution, SolarMAN Plant Flow Dictionary (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (11): GOLDEN_DATASETS — Test Datasets, GOLDEN-001 — FV Dropout July 17, GOLDEN-002 — Unstable Grid July 17, GOLDEN-003 — Deep Discharge and Restarts July 19, GOLDEN-004 — Corrupt/Desynchronized Data, GOLDEN-005 — Impossible SOC Jump, BAT-002 — Descarga profunda, DATA-003 — Salto SOC improbable (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.45
Nodes (10): Random, _format_timestamp(), main(), datetime, Path, Generate synthetic CSV fixtures for tests and development.  Usage:     uv run py, _synthetic_value(), write_flow_csv() (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.20
Nodes (10): properties, type, evidenceId, signal, sourceRef, unit, value, type (+2 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (10): required, confidence, endAt, episodeId, evidences, plantId, ruleRefs, severity (+2 more)

### Community 22 - "Community 22"
Cohesion: 0.20
Nodes (10): ADR-001 — Deterministic-first, Deterministic-first, FOUNDATIONS.md, AI Role Constraint, Data Quality Factors, Episode, Epistemological Hierarchy, Null vs Zero Distinction (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (10): INSTALLER_REPORTS — Report Requirements, LOOP_REGISTRY.md, L1 — Importacion reproducible, L10 — Operacion, L2 — Calidad de datos, L3 — Timeline canonico, L4 — Metricas fisicas, L5 — Catalogo de reglas v0.1 (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.25
Nodes (9): Evidence, Graphs must declare the question they answer, Hypothesis, Phase 7 Reports, Scientific method 10 steps, Report workflow, Technical review workflow, Flujos principales (+1 more)

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (9): MCP README — MCP Capabilities, compare_periods capability, get_episode capability, get_episode_evidence capability, get_plant_health capability, get_report_metadata capability, list_episodes capability, list_import_batches capability (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.25
Nodes (7): Motor científico: funciones puras, reglas versionadas, contratos explícitos, controllers → services → repositories → models, DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT, SEVERITY_CONFIDENCE.md, Confidence Factors, Presentation Rule, 00-foundation-card.md

### Community 27 - "Community 27"
Cohesion: 0.25
Nodes (8): AFCI protection, Agent capability contract, Agent prohibited actions in MVP, Agent read-only capabilities, No automatic inverter control in MVP, Phase 6 AI, AI interpretation workflow, Capacidades de agentes

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (8): Confidence, Confirmed cause, Episode, Phase 5 Episodes and D3, Regulated findings state machine, Rule, Severity, Analysis workflow

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (8): format, type, peakAt, timestamp, format, type, null, string

### Community 30 - "Community 30"
Cohesion: 0.29
Nodes (6): Rojo reservado para riesgo real, Datos ausentes con huecos visibles, Inferencias IA diferenciadas de mediciones, Planta saludable como primera pregunta UX, Contraste AA Accessibility, Zero Decorative Gradients Principle

### Community 31 - "Community 31"
Cohesion: 0.29
Nodes (7): Battery metrics, Data metrics, Grid metrics, Inverter metrics, Plant metrics, PV MPPT metrics, Catalogo de metricas

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (7): required, evidenceId, kind, signal, sourceRef, unit, value

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (7): AIInterpretation, LLM_GUARDRAILS.md, Allowed LLM Input, Multi-Provider Strategy, Required LLM Output, LLM Output Validations, L8 — IA validada

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (5): additionalProperties, $id, $schema, title, type

### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (5): enum, kind, calculated, measured, normalized

### Community 36 - "Community 36"
Cohesion: 0.40
Nodes (5): Episode, Severity Concept, Severity Levels, INCIDENT_RESPONSE — Incident Response Process, L6 — Episodios

### Community 37 - "Community 37"
Cohesion: 0.60
Nodes (4): Path, test_cli_import_flow_writes_reports(), test_cli_import_telemetry_writes_reports(), test_cli_import_unknown_format_fails()

### Community 38 - "Community 38"
Cohesion: 0.50
Nodes (4): $defs, evidence, additionalProperties, type

### Community 39 - "Community 39"
Cohesion: 0.67
Nodes (4): ADR-004 — Inverter Telemetry Signals Dict, InverterTelemetrySample signals dict model, InverterTelemetrySample, SolarMAN Inverter Telemetry Dictionary

## Knowledge Gaps
- **289 isolated node(s):** `$schema`, `$id`, `title`, `type`, `summary` (+284 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `openpyxl` connect `Data Models and Exceptions` to `CLI and Core Commands`, `Community 12`, `Community 15`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Polars` connect `Data Models and Exceptions` to `Community 12`, `AI and Deployment`, `Community 15`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `SourceType` connect `Data Models and Exceptions` to `CLI and Core Commands`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `RULE_CATALOG.md` (e.g. with `Severity Levels` and `L5 — Catalogo de reglas v0.1`) actually correct?**
  _`RULE_CATALOG.md` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SourceType` (e.g. with `ImportBatch` and `ImportMetadata`) actually correct?**
  _`SourceType` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ValidityFlags` (e.g. with `InverterTelemetrySample` and `SignalSpec`) actually correct?**
  _`ValidityFlags` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `$id`, `title` to the rest of the system?**
  _289 weakly-connected nodes found - possible documentation gaps or missing edges._