# Plan de pruebas

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
