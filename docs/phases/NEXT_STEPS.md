# Plan ejecutable

## Baseline auditado

- Rama: `main`
- SHA: `94a66407e258990bbf9d7ed347a86d9cf529caf5`
- Fecha: 2026-07-20
- Auditoría: [`../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md)

## Resumen del avance real

### Cerrado

- I1 — importación reproducible de ambos formatos SolarMAN;
- hashing, normalización temporal, fixtures y CLI básica.

### Parcial

- Q2 — orden, duplicados, huecos y score básico;
- T3 — muestra canónica y join por tolerancia;
- P8 — persistencia PostgreSQL inicial;
- O11 — Docker, health y workflow de deploy.

### Prototipo o catálogo

- agrupador temporal denominado episodio;
- catálogo seed de reglas;
- proveedores MiniMax/DeepSeek;
- prompt y validador LLM.

### No iniciado

- métricas físicas;
- detectores científicos de eventos;
- evaluadores reales de reglas;
- golden cases del 17 y 19;
- UI D3;
- PDF técnico;
- motor de factura Afinia.

## Próximo loop obligatorio

# R0 — Development reconciliation and safety gate

## Goal

Restablecer coherencia entre documentación y código, evitar falsos diagnósticos y recuperar validación continua.

## Scope

- estado documental;
- CI documental y privacidad;
- seguridad de reglas seed;
- semántica de cero FV;
- estado textual del inversor;
- bloqueo de IA sin evidencia evaluada;
- tratamiento del PR #8 divergido.

## Out of scope

- nuevas reglas científicas;
- métricas de energía;
- UI;
- D3;
- facturación;
- PDF;
- cambios de esquema grandes;
- control del inversor.

## Stop conditions

| Condición | Estado inicial |
|---|---|
| README, CHANGELOG, NEXT_STEPS y LOOP_REGISTRY coinciden | FAIL |
| CI corre también en cambios documentales | FAIL |
| reglas no se activan por mera presencia | FAIL |
| cero FV permanece cero | FAIL |
| estado textual permanece en muestras merged | FAIL |
| IA no recibe reglas no evaluadas | FAIL |
| PR económico no puede fusionarse accidentalmente | FAIL |
| ruff, format, mypy y pytest pasan | PENDING |

## Human gate

No hacer merge automático. El propietario revisa el PR correctivo y autoriza el cierre de R0.

## Después de R0

### Q2.3 — Plausibilidad física y calidad avanzada

Entregables:

- salto SOC físicamente improbable;
- temperatura imposible;
- frecuencia y voltaje plausibles;
- signo contradictorio;
- huecos ponderados por duración;
- cobertura temporal;
- score que no considere perfecto un lote vacío;
- tests sintéticos de regresión.

### M4.1 — Energía y balance

Depende de Q2.3 y T3:

- integración temporal de W a Wh/kWh;
- tratamiento explícito de huecos;
- balance por ventana;
- residual y confianza;
- fixtures con resultados manuales conocidos.

### E5.1 — Eventos científicos

Depende de M4:

- detector de dropout FV;
- pérdida y retorno de red;
- SOC bajo;
- inicializaciones repetidas;
- ventanas antes/durante/después;
- golden cases del 17 y 19.

### R6.1 — Evaluadores determinísticos

Cada regla debe tener algoritmo, parámetros, evidencia, falsos positivos y tests. La presencia de una señal nunca equivale a activación.

### A7.1 — IA validada

Solo después de R6.1:

- evidence IDs estables;
- exact coverage;
- rechazo de referencias inexistentes;
- rechazo de causas confirmadas;
- prompts versionados;
- consenso opcional;
- tests adversariales.

### ECO — Rebase de inteligencia económica

El PR #8 no debe fusionarse tal como está. Después de R0 debe recrearse desde main y conservar únicamente la fundación económica compatible.

## Próximo prompt ejecutable

Implementar únicamente R0. No iniciar Q2.3, métricas físicas, facturación, UI ni nuevas integraciones hasta que el PR correctivo pase todos los checks y sea revisado por un humano.
