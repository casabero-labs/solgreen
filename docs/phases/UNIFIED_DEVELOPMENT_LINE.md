# Línea única de desarrollo — Solgreen

## 1. Decisión

Solgreen se desarrolla mediante una sola línea canónica:

```text
main
  └── develop/solgreen-unified
        └── un único PR activo contra main
```

`main` contiene únicamente estados verificados. `develop/solgreen-unified` integra de forma ordenada backend, motor científico, economía, frontend, IA, reportes y operación.

No se crean ramas independientes por pista mientras esta integración esté activa. Una excepción requiere un hotfix de producción documentado y reversible.

## 2. Razón

La separación anterior produjo:

- documentación económica divergida;
- fases técnicas cerradas nominalmente antes de validar su comportamiento científico;
- roadmap distinto entre README, Loop Registry y código;
- frontend postergado como una pista aislada;
- múltiples PRs cortos sin una visión de producto compartida.

La línea única no significa mezclar todo en un commit. Significa mantener una sola secuencia de producto con loops pequeños, verificados y dependencias explícitas.

## 3. Regla de integración

Cada loop dentro del PR unificado debe:

1. partir del último SHA verde de la rama;
2. declarar `GOAL`, `CONTEXT`, `ACTION`, `FEEDBACK`, `STOP CONDITION`, `HUMAN GATE` y `ROLLBACK`;
3. cambiar una capacidad coherente;
4. mantener el PR desplegable o explícitamente bloqueado;
5. actualizar código, tests y documentación juntos;
6. no presentar superficies experimentales como terminadas.

## 4. Secuencia U0–U7

| Loop | Resultado | Dependencias | Estado |
|---|---|---|---|---|
| U0 | Fundación unificada y frontend Showcase Ink ejecutable | R0 | TECHNICALLY_VERIFIED_HUMAN_GATE |
| U1 | Calidad, semántica y safety gates | U0, #21 | ENGINEERING_CLOSED |
| U2.0 | Energy semantics discovery | U1 | DISCOVERY_COMPLETE_HUMAN_GATE_PENDING |
| U2.1 | PowerSignProfile + normalización direccional | U2.0 | ENGINEERING_CLOSED |
| U2.2a | Temporal integration core W→Wh | U2.1 | ENGINEERING_CLOSED |
| U2.2b | Solarman energy runtime (persisted → integrate_energy, 5 series) | U2.2a | ENGINEERING_CLOSED |
| U3 | Eventos, reglas y golden cases | U2, #20 | PLANNED |
| U4 | Frontend conectado y flujos human-first | U3 | PLANNED |
| U5 | Inteligencia económica Afinia | U2, U4 | FOUNDATION_ABSORBED |
| U6 | IA validada con evidencias estables | U3, #22 | BLOCKED |
| U7 | PDF, deploy y operación verificable | U4, U5, U6 | PLANNED |

## 5. U0 — Fundación unificada

### Goal

Crear una sola fuente de verdad y una primera vertical frontend real que no prometa funciones inexistentes.

### Entregables

- fundación económica Afinia absorbida desde el PR #8;
- ADR deterministic-first;
- diccionario de facturación;
- test plan económico;
- aplicación React + TypeScript + Vite;
- visualización D3 con tabla alternativa;
- navegación Planta, Datos y Economía;
- modo oscuro global;
- datos demostrativos etiquetados;
- acción de importación bloqueada hasta contar con API y E2E;
- CI Python, frontend, documentación y privacidad;
- arquitectura frontend Showcase Ink;
- un solo PR activo.

Evidencia técnica: [`../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md`](../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md).

### Estado

TECHNICALLY_VERIFIED_HUMAN_GATE. CI completa en verde. Frontend abre y permite navegar. Pendiente revisión humana visual y funcional.

## 6. U1 — Calidad, semántica y safety gates

### Estado: ENGINEERING_CLOSED

442 tests, 90.78% cobertura (pre-U2.1). Cero medido preservado. Estados textuales sobreviven al merge. Plausibilidad física. Consistencia solo pares declarados. Parser ISO corregido (#24). Formato global normalizado (#25). Seed rules not_evaluable. LLM gate sin reglas elegibles.

## 7. U2 — Energía y métricas

### U2.0 — Energy semantics discovery

**Estado:** DISCOVERY_COMPLETE_HUMAN_GATE_PENDING

Inventario completo de 23+ señales. AC/DC documentado. Signos map confirmed/provisional/unknown. Authority hierarchy declarada. ADR-008 y ADR-009 aceptados.

### U2.1 — PowerSignProfile + normalización direccional

**Estado:** ENGINEERING_CLOSED (PR #27, merged)

PowerSignProfile con per-direction evidence status (ADR-009). DirectionalPowerResult con validación de invariantes. normalize_power_value con gate direccional. Seeds de producción y telemetría. D10 proposal disabled hasta operador autorice effective_from.

### U2.2a — Temporal integration core

**Estado:** ENGINEERING_CLOSED (PR #31)

`DirectionalPowerObservation`, `IntegrationProfile`, `EnergyInterval`, `EnergySummary`, `IntegrationResult`. Integración trapezoidal pura para series homogéneas direccionales. Instantaneous-sample semantics exclusivo. Política de gaps explícita. Boundary accounting. Coverage nunca escala energía.

### U2.2b — Source-profile selection y runtime wiring

**Estado:** PLANNED

Seleccionar IntegrationProfile concreto para fuentes SOLARMAN. Conectar integrate_energy al pipeline de sync. Sin billing, tarifas, frontend ni reportes.

### U2.3–U2.7 — Planned implementation

| Sub-phase | Goal | Depends on |
|---|---|---|
| U2.3 | Métricas de red (import/export, horarios) | U2.2 |
| U2.4 | Métricas de batería (charge/discharge) | U2.2 |
| U2.5 | Métricas de producción y consumo | U2.2 |
| U2.6 | Cobertura, agregaciones, perfiles horarios | U2.3–U2.5 |
| U2.7 | Conciliación con contadores acumulados, QA | U2.3–U2.6 |

## 8. U3 — Eventos y reglas

- segmentos operativos separados de eventos;
- ventanas antes, durante y después;
- dropout FV;
- pérdida y retorno de red;
- SOC bajo y descarga profunda;
- reinicios e inicializaciones;
- evaluadores determinísticos, no presencia de señales;
- golden cases privados del 17 y 19;
- evidencia estructurada estable.

## 9. U4 — Frontend conectado

- API contracts;
- carga CSV/XLSX;
- progreso real;
- timeline D3;
- filtros persistentes;
- episodios con evidencia;
- tablas alternativas;
- estados vacío, loading, error y parcial;
- E2E Human-First;
- telemetría de producto sin datos sensibles.

## 10. U5 — Economía Afinia

- `TariffProfile` y vigencia;
- factura normalizada;
- motor tarifario puro;
- subsidio parametrizado;
- conciliación;
- P10/P50/P90;
- perfil horario de compra;
- catálogo de cargas;
- recomendaciones restringidas;
- simulador `what-if`;
- escenarios AGPE separados del modo actual.

## 11. U6 — IA validada

- IDs de evidencia estables;
- exact coverage;
- rechazo de referencias inexistentes o cruzadas;
- rechazo de cifras nuevas;
- proveedor y modelo reales registrados;
- prompt versionado;
- coste y fallback auditables;
- cero persistencia de respuestas inválidas.

## 12. U7 — Reportes y operación

- PDF técnico reproducible;
- privacidad configurable;
- API y frontend desplegados;
- migraciones versionadas;
- Coolify con polling a estado final;
- SHA del contenedor;
- health público;
- smoke tests;
- rollback probado;
- evidencia en `docs/deployments/`.

## 13. Política de PRs

Durante la línea unificada:

- un único PR de producto abierto;
- los issues describen loops, bloqueadores y stop conditions;
- los commits son pequeños y temáticos dentro de la misma rama;
- un commit rojo no se considera checkpoint;
- no se fusiona parcialmente una pista incompleta;
- el PR permanece draft mientras el loop activo no cierre;
- `main` solo recibe squash cuando el conjunto integrado es coherente y verificable.

## 14. Promoted releases

### Unified release (PR #27)

Merged via squash `1f70674..5cfb9fb` into `main`. Unified R0 + U0 + U1 + U2.1
(backed by ADR-008 and ADR-009). D10 remains disabled and requires operator
authorization to activate.

## 15. Estado actual + próximo paso exacto

**Estado actual:** R0 fusionado; economía E0 absorbida; U0 técnicamente verificado (human gate pendiente); U1 ENGINEERING_CLOSED; U2.1 ENGINEERING_CLOSED (PR #27 merged); U2.2a ENGINEERING_CLOSED (PR #31 merged); U2.2b ENGINEERING_CLOSED (PR #33).

**Próximo paso exacto:** U2.3a — Grid import/export energy metrics and persistence contracts.
