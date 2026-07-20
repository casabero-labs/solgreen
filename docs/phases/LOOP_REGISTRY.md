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
uv run mypy solgreen
uv run pytest
```

### Frontend

```bash
cd apps/web
npm install --no-audit --no-fund
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
|---|---|---|---|---|
| R0 | Reconciliar baseline y safety gates | CI y auditoría | estado documental coincide con código | CLOSED |
| U0 | Integrar economía y frontend Showcase Ink | TS, Vitest, build, docs | primera vertical ejecutable y honesta | ACTIVE |
| U1 | Calidad avanzada y semántica | fixtures y tests | cero, status, plausibilidad y cobertura correctos | PLANNED |
| U2 | Energía y métricas físicas | fórmulas y golden manuales | W→kWh y balance reproducibles | PLANNED |
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

## Loop activo

# U0 — Fundación unificada + Showcase Ink

## Goal

Unificar el producto y entregar una primera vertical frontend ejecutable sin fingir conexión con capacidades aún no disponibles.

## Context

- R0 fusionado en `main`;
- antiguo PR #8 cerrado como supersedido;
- economía E0 absorbida;
- frontend inexistente en el baseline;
- Showcase Ink como estándar visual obligatorio.

## Action

1. mantener una sola rama y PR activos;
2. absorber dominio, ADR, workflows y test plan económico;
3. crear `apps/web` con React, TypeScript, Vite y D3;
4. implementar navegación Planta, Datos y Economía;
5. mostrar datos demo con advertencia persistente;
6. añadir gráfica y tabla alternativa;
7. bloquear COP sin perfil vigente;
8. bloquear importación web hasta U4 con razón legible;
9. añadir arquitectura y QA frontend;
10. ejecutar CI backend, frontend, documentación y privacidad.

## Feedback

- TypeScript strict;
- Vitest;
- Vite build;
- Ruff;
- mypy;
- pytest;
- validación documental;
- revisión visual y human-first del alcance.

## Stop condition

- un solo PR de producto abierto;
- CI verde;
- frontend navega y cambia periodo;
- modo oscuro funciona;
- datos demo no parecen reales;
- no aparece COP vigente;
- D3 tiene tabla alternativa;
- documentación coincide con la implementación;
- economía E0 existe en la rama unificada.

## Human gate

El propietario revisa jerarquía, navegación y honestidad del alcance. U0 no valida todavía una planta real.

## Rollback

Cerrar el PR unificado. `main` conserva R0.

## Próximo loop exacto

U1: resolver semántica de cero y estados, plausibilidad avanzada, parser ISO y baseline de formato antes de calcular energía o conectar el frontend.
