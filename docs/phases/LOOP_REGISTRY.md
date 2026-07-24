# Loop Registry — Solgreen

## Metodología

Solgreen aplica `casabero-labs/estandar-casabero`:

```text
DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT
```

Cada loop declara `GOAL`, `CONTEXT`, `ACTION`, `FEEDBACK`, `STOP CONDITION`, `HUMAN GATE`, `ROLLBACK` y próximo paso exacto.

## Gobernanza de desarrollo

```text
main → develop/solgreen-unified → un único PR activo
```

- `main` es la fuente estable.
- La rama unificada integra todas las capacidades.
- Los issues son loops o bloqueadores, no ramas alternativas.
- No abrir pistas paralelas de frontend, economía, diagnóstico o IA.
- Documento canónico: [`UNIFIED_DEVELOPMENT_LINE.md`](UNIFIED_DEVELOPMENT_LINE.md).

## Feedback disponible

- schemas SolarMAN;
- fixtures sintéticos;
- datasets y facturas privadas fuera de Git;
- golden cases del 17 y 19 de julio;
- tests Python y frontend;
- CI;
- revisión Human-First;
- revisión del propietario;
- diagnóstico del instalador;
- perfiles oficiales cuando estén disponibles.

## Comandos de verificación

### Backend

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest --cov=solgreen --cov-fail-under=80
```

### Frontend

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run typecheck
npm run test
npm run build
```

## Human gates

- perfil real de planta;
- signos de red y batería;
- límites de batería, inversor y red;
- severidad crítica;
- confirmación de causa;
- perfil tarifario vigente;
- corrección de factura extraída;
- merge;
- reportes compartidos;
- deploy;
- cualquier escritura sobre equipos;
- cierre de flujos críticos de UI.

## Estado oficial unificado

| Loop | Objetivo | Feedback principal | Stop condition | Estado |
|---|---|---|---|---|---|
| R0 | Reconciliar baseline y safety gates | CI y auditoría | estado documental coincide con código | CLOSED |
| U0 | Integrar economía y frontend Showcase Ink | TS, Vitest, build, docs | primera vertical ejecutable y honesta | TECHNICALLY_VERIFIED_HUMAN_GATE |
| U1 | Calidad avanzada y semántica | fixtures y tests | cero, status, plausibilidad, consistencia y safety gates | ENGINEERING_CLOSED |
| U2.0 | Energy semantics discovery | inventario y docs | semántica energética documentada | DISCOVERY_COMPLETE_HUMAN_GATE_PENDING |
| U2.1 | PowerSignProfile + normalización direccional | seeds y tests | contratos direccionales implementados | ENGINEERING_CLOSED |
| U2.2a | Temporal integration core | integración trapezoidal y tests | W→Wh con sample semantics explícito | ENGINEERING_CLOSED |
| U2.2b | Solarman energy runtime (persisted rows → integrate_energy) | 5 series, trapezoidal, explicit lookback | ENGINEERING_CLOSED |
| U3 | Eventos, reglas y evidencia | golden 17/19 | eventos científicos y reglas reales | PLANNED |
| U4 | Frontend conectado | Playwright Human-First | carga, timeline y episodios utilizables | PLANNED |
| U5 | Afinia, cargas y escenarios | golden billing | factura y horarios reproducibles | FOUNDATION_ABSORBED |
| U6 | IA validada | adversarial tests | cero respuesta inválida aceptada | BLOCKED_BY_U3 |
| U7 | PDF y operación | deploy, SHA, health | flujo desplegado y reversible | PLANNED |

## Bloqueadores vinculados

- #20: evaluadores determinísticos;
- #21: semántica del timeline y eventos;
- #22: evidencias y validador IA;
- #24: parser ISO de duración;
- #25: baseline global de formato;
- #26: epic de línea unificada.

## U2.0 — Energy semantics, sign profiles and integration contract discovery

### Goal

Determinar y documentar la semántica energética completa antes de implementar
cualquier cálculo W→Wh.

### Actions ejecutadas

1. Inventario completo de señales energéticas (potencia, energía) con 23+ señales.
2. Matriz AC/DC por señal.
3. Matriz de convención de signos con estados confirmed/provisional/unknown.
4. Jerarquía de autoridad: fiscal (medidor Afinia) vs operacional (SolarMAN/inversor).
5. Diseño conceptual de PowerSignProfile (perfil de signos versionado).
6. Diseño conceptual de normalización direccional.
7. Diseño conceptual de integración temporal W→Wh.
8. Política de gaps: no interpolar, estados explícitos, cobertura como fracción.
9. Contratos conceptuales: EnergyInterval, EnergySummary.
10. ADR-008 y ADR-009 aceptados.

### Human gates pendientes

- Signo de red: ventana nocturna con consumo conocido y PV cero.
- Signo de batería: ventana de carga solar y descarga nocturna.
- Semántica temporal de las muestras.
- Puntos físicos de medición (CT, BMS, cableado).

## U2.1 — PowerSignProfile and directional normalization

### Goal

Implementar contratos versionados de signos y normalización direccional.

### Entregables

- PowerSignProfile con per-direction evidence status (ADR-009).
- PowerSignProfileRegistry con seeds de producción y telemetría.
- DirectionalPowerResult con validación de invariantes.
- normalize_power_value con gate direccional.
- D1.0 proposal registry.

### Estado: ENGINEERING_CLOSED

PR #27 merged. 1260 tests. CI verde. D10 proposal permanece disabled hasta
que el operador autorice el effective_from.

## U2.2a — Temporal integration core

### Goal

Convertir observaciones direccionales normalizadas non-negativas en energía
integrada (Wh) usando contrato instantaneous-sample explícito e integración
trapezoidal.

### Entregables

- `DirectionalPowerObservation`: modelo frozen con timestamp tz-aware,
  canonical source, source system, direction, power_w ≥ 0 o None,
  profile_version para observaciones NORMALIZED.
- `IntegrationProfile`: semantics=instantaneous, method=trapezoidal,
  expected_interval, maximum_authorized_interval.
- `EnergyInterval`: intervalo con status (observed/missing/excluded_*),
  energy_wh nullable, invariantes de consistency.
- `EnergySummary`: observed_energy_wh/kWh, cobertura, contadores.
- `IntegrationResult`: (intervals, summary) immutable.
- `integrate_energy()`: función pura sin I/O, sin side effects.
- Política de gaps: missing, excluded_nonfinite, excluded_zero_duration,
  excluded_unconfirmed_sign.
- Boundary accounting: leading/trailing gaps cuentan como missing.
- Homogeneous-series invariant: rechaza campos, fuentes, direcciones
  o profile versions mixtos.
- Profile-transition policy: no integrar a través de transiciones de
  versión de signo.
- Coverage nunca escala energía. Missing energy es unknown, no zero.

### Estado: ENGINEERING_CLOSED

61 tests unitarios. Ruff, mypy, frontend gates limpios. PR #31.

## U2.2b — Solarman energy runtime

### Implemented (ENGINEERING_CLOSED)

Wires persisted SOLARMAN normalized power rows to `integrate_energy()` via
`SolarmanPersistedSignalRow` adapter and `SolarmanEnergyRuntimeResult`.
Default mode is OFF; instantaneous mode requires explicit profile_version,
expected_interval, maximum_interval, and lookback. Five directional series:
GRID_IMPORT, GRID_EXPORT, BATTERY_CHARGE, BATTERY_DISCHARGE, PV_GENERATION.
No billing, tariffs, frontend, or persistence of energy results.

### Dependencies

U2.2a complete.

