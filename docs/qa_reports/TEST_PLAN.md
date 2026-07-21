# Plan de pruebas

## U2 — Energy semantics and metrics

### U2.0 — Discovery (documental)

- ENERGY_SEMANTICS.md exists and is complete.
- ADR-008 exists and status is Proposed.
- U2_ENERGY_DISCOVERY QA report exists.
- No assertions of confirmed sign without evidence.
- No energy (Wh/kWh) calculations.
- No code changes to production modules.
- Grid import/export terms only in conceptual context.
- ADR not marked Accepted while human gates pending.

### U2.1 — PowerSignProfile and directional normalization

- PowerSignProfile contract with all mandatory fields.
- normalize_sign pure function: same input + same profile = same output.
- status=unknown forbids normalization (raises or returns unavailable).
- status=provisional allows normalization with warning.
- status=confirmed allows full normalization.
- Directional fields never negative (invariant).
- Grid import/export never simultaneously positive for same net sample.
- Battery charge/discharge never simultaneously positive for same net sample.
- Unknown sign produces None in all directional fields.
- Zero measured preserved in appropriate directional field.
- profile_version and lineage recorded on normalization.

### U2.2 — Temporal integration

- integrate_power pure function with configurable method.
- All integration methods produce correct energy from synthetic fixtures.
- Zero-duration intervals excluded.
- NaN/Inf/None values excluded from integration.
- First/last point handling documented and tested.
- Gaps produce missing state, not assumed energy.
- Coverage computed as observed_duration / expected_duration.
- EnergyInterval fields validated per sample.
- EnergySummary aggregates correctly over window.

### U2.3–U2.5 — Directional metrics

- grid_import_wh computed from grid_import_w integration.
- grid_export_wh computed from grid_export_w integration.
- battery_charge_wh from battery_charge_w integration.
- battery_discharge_wh from battery_discharge_w integration.
- pv_generation_wh from pv_generation_w integration.
- load_consumption_wh from load_consumption_w integration.
- Hourly and daily aggregations correct.

### U2.6 — Coverage and profiles

- coverage_fraction < 1.0 handled correctly.
- Missing energy is unknown, not zero.
- Aggregation windows respect timezone.
- Hourly profile contains mean, P50, P90, P95, max.
- Day classification (weekday/weekend/holiday) applied correctly.

### U2.7 — Reconciliation

- Cumulative counter deltas match integrated energy within tolerance.
- Counter reset detection works.
- Reconciliation status: within_tolerance, review, unreconciled.
- Candidate explanations when reconciliation fails.

## U1 — Calidad, semántica y safety gates

### Cero y estado (U1.1)

- cero pv1 preservado como 0.0 (no None);
- cero pv2 preservado como 0.0;
- cero ambos summed como 0.0;
- estado textual preservado en merged;
- estado textual preservado en telemetry-only;
- get_text devuelve str, rechaza numéricos, strip;
- ausencia de estado produce None.

### Cobertura temporal (U1.2)

- lote vacío → completeness 0.0, temporal_coverage 0.0, quality_score 0.0;
- separación 5 min → coverage 1.0;
- separación 10 min → coverage 0.5;
- separación 60 min → coverage ≈ 0.083;
- jitter bajo gap_factor no penaliza;
- duplicados → duplicate_integrity < 1.0;
- completeness con expected_sample_count;
- model_dump() y model_dump_json() incluyen dimensions.

### Plausibilidad (U1.3)

- NaN, +Inf, −Inf → finding + evaluated+failed;
- SOC −1 y 101 → finding;
- SOC 0/50/100 → evaluated+passed;
- temperatura < −273.15 → finding;
- temperatura 80 sin perfil → not_configured;
- rango configurado dentro → passed, fuera → failed;
- perfil provisional conserva status y source;
- evaluated_count == passed_count + failed_count;
- score is None ⇔ evaluated_count == 0.

### Consistencia (U1.4)

- SOC igual → passed;
- SOC dentro de tolerancia absoluta → passed;
- SOC fuera → failed con finding OUTSIDE_TOLERANCE;
- tolerancia relativa funciona;
- None → skipped_missing;
- NaN/Inf → skipped_nonfinite;
- flow-only/telemetry-only ignorados;
- time_delta dentro → evaluado, fuera → skipped_alignment;
- evaluated == passed + failed.

### Parser ISO (U1.5.0)

- PT1S, PT5M, PT2M30S, PT1H, P1D, etc. → timedelta correcto;
- precisión microsegundos (PT0.123456S);
- PT0S, negativos, meses/años, human format, lowercase → rechazados;
- >6 decimales → rechazado.

### Side effects CLI (U1.5.0a)

- tolerancia inválida → exit_code != 0, no mkdir, no repo, no LLM;
- tolerancia válida → timeline generado.

### Formato global (U1.5.1)

- ruff format --check . pasa en todo el repositorio;
- AST equivalente antes/después.

### npm reproducible (U1.5.2)

- npm ci funciona, lockfile inalterado;
- CI usa npm ci;
- CI exige package-lock.json.

### Rule outcomes (U1.6)

- seed rules → not_evaluable con reason rule_not_implemented;
- 0 RuleExecution persistidos para seed;
- implemented sin señales → missing_required_signals;
- implemented sin evaluator → evaluator_not_registered;
- evaluator fired=false → evaluated_not_fired;
- evaluator fired=true con evidence → fired;
- invariantes de RuleEvaluationOutcome validados.

### Gate LLM (U1.6)

- fired=false o fired=true sin evidence → excluido;
- fired=true con evidence → elegible;
- LLM no llamado sin reglas elegibles;
- prompt excluye reglas no elegibles.

## Unitarias

- parsing de cada columna prioritaria;
- timezone;
- signos;
- integración de energía;
- residual;
- cada regla;
- severidad y confianza;
- validador IA.

## Integración

- archivo → lote → muestras;
- lote → timeline;
- timeline → reglas → episodio;
- episodio → IA → validación;
- episodio → reporte.

## Golden tests

- dropout FV del 17;
- red inestable del 17;
- descarga profunda del 19;
- tormenta de inicializaciones;
- sobrevoltaje L2;
- carga de batería elevada;
- exportación transitoria;
- hueco del 16;
- salto SOC;
- balance imposible.

## Seguridad

- aislamiento por planta;
- RLS;
- URLs firmadas;
- secreto no aparece en logs;
- serial redaccionado;
- prompt injection en archivos y notas;
- rechazo de archivos maliciosos.

## UX

- importación completa por teclado;
- lectura de episodio sin depender de color;
- huecos visibles;
- estados parciales y errores;
- tabla alternativa para cada gráfica crítica.

## Performance

- 120 columnas × meses de muestras;
- downsampling;
- análisis asíncrono;
- memoria del worker;
- generación de PDF.

## Evidencia

Cada ejecución se documenta en `docs/qa_reports/` con fecha, SHA, comandos y resultados.
