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
|---|---|---|---|
| U0 | Fundación unificada y frontend Showcase Ink ejecutable | R0 | TECHNICALLY_VERIFIED_HUMAN_GATE |
| U1 | Calidad avanzada y semántica correcta | U0, #21 | PLANNED |
| U2 | Energía y métricas físicas | U1 | PLANNED |
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

### Feedback

```text
Python: Ruff + mypy + pytest
Frontend: TypeScript + Vitest + Vite build
Docs: archivos canónicos y privacidad
Humano: revisión del flujo, alcance y jerarquía
```

Evidencia técnica: [`../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md`](../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md).

### Stop condition

- CI completa en verde;
- frontend abre y permite navegar/cambiar periodo;
- no presenta datos demo como reales;
- no presenta COP vigente sin perfil;
- D3 tiene tabla alternativa;
- README, arquitectura, Loop Registry y Next Steps coinciden;
- PR #8 cerrado como supersedido;
- un solo PR de producto abierto.

La condición técnica está cumplida. El cierre definitivo espera revisión humana.

### Human gate

Revisión visual y funcional antes de marcar U0 cerrado. El frontend aún no constituye validación de una planta real.

### Rollback

Cerrar el PR unificado. `main` conserva R0 sin el frontend ni la integración económica.

## 6. U1 — Calidad y semántica

Resuelve primero los errores que contaminan todo lo posterior:

- conservar cero medido;
- conservar estados textuales;
- score no perfecto para lote vacío;
- huecos ponderados por duración;
- plausibilidad de SOC, voltaje, frecuencia y temperatura;
- consistencia entre fuentes;
- parser ISO de tolerancia #24;
- formato global #25.

## 7. U2 — Energía y métricas

- integración temporal W→Wh/kWh;
- tratamiento de huecos;
- importación y exportación canónicas;
- carga y descarga de batería;
- balance y residual;
- cobertura y confianza;
- perfiles horarios locales;
- no mezclar potencia con energía.

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

La factura oficial y el medidor fiscal conservan autoridad. El LLM no calcula dinero ni energía.

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

## 14. Estado actual + próximo paso exacto

**Estado actual:** R0 fusionado; economía E0 absorbida; U0 técnicamente verificado y pendiente de revisión humana sobre el PR #27.

**Próximo paso exacto:** revisar visual y funcionalmente el frontend U0; después cerrar U0 e iniciar U1 dentro de la misma rama y el mismo PR, sin abrir otra línea de desarrollo.
