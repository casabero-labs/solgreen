# Auditoría de desarrollo — Solgreen

Fecha: 2026-07-20  
Baseline: `main@94a66407e258990bbf9d7ed347a86d9cf529caf5`

## Objetivo

Contrastar el estado declarado con el código presente y restablecer un roadmap verificable según `casabero-labs/estandar-casabero`.

No fue posible ejecutar el repositorio desde esta auditoría remota. Los conteos de tests consignados en PRs son declaraciones del autor y deben confirmarse por CI antes del merge.

## Estado real

| Capacidad | Estado |
|---|---|
| Fundamentos | Requieren reconciliación |
| Importación SolarMAN | Implementada |
| Calidad de datos | Parcial: orden, duplicados, huecos y score básico |
| Timeline canónico | Parcial |
| Métricas físicas | No implementadas |
| Episodios | Prototipo por separación temporal, no diagnóstico causal |
| Reglas | Catálogo sin evaluadores determinísticos reales |
| IA | Experimental y bloqueada por evidencia insuficiente |
| PostgreSQL | Primera versión implementada |
| API | Health mínimo |
| UI y D3 | No implementados |
| PDF técnico | No implementado |
| Economía Afinia | Diseñada en PR #8, no fusionada |
| Operación | Parcial, sin evidencia visible de deploy validado |

## Hallazgos críticos

### 1. Reglas activadas por presencia de señales

`_evaluate_rules` marca una regla como activada cuando encuentra las señales requeridas. No comprueba el umbral de SOC, la duración de waiting, la caída FV ni la pérdida de red.

Consecuencia: puede producir falsos positivos y alimentar al LLM con hechos inexistentes.

### 2. Episodios no diagnósticos

`build_episodes` divide el timeline únicamente cuando existe un hueco superior a diez minutos. Los eventos breves pueden diluirse dentro de promedios largos.

### 3. Guardrails LLM incompletos

El parser fuerza `prohibited_claims=()` y el validador solo verifica rangos numéricos y campos vacíos. No demuestra cobertura exacta ni referencias estables.

### 4. Cero FV tratado potencialmente como ausencia

`_pv_power` usa lógica booleana al seleccionar un canal. Un `0.0` válido puede convertirse en `None`.

### 5. Estado textual del inversor perdido

En muestras fusionadas, `current_state_of_machine` se consulta como número aunque es una señal de estado textual.

### 6. Documentación obsoleta

README, CHANGELOG, NEXT_STEPS y LOOP_REGISTRY todavía indican que L2 está pendiente, aunque main contiene piezas posteriores.

### 7. CI documental eliminado

El workflow actual omite PRs solo documentales y ya no contiene el job que verificaba documentos requeridos y exports privados.

### 8. PR económico divergido

El PR #8 parte de un main antiguo y está 19 commits detrás. No debe fusionarse sin reconciliación.

## Reclasificación oficial propuesta

| Track | Estado |
|---|---|
| I1 Importación | CLOSED |
| Q2 Calidad | PARTIAL |
| T3 Timeline | PARTIAL |
| M4 Métricas físicas | NOT_STARTED |
| E5 Eventos y episodios | PROTOTYPE_ONLY |
| R6 Reglas | CATALOG_ONLY |
| A7 IA | EXPERIMENTAL_BLOCKED |
| P8 Persistencia | PARTIAL |
| U9 UI/D3 | NOT_STARTED |
| G10 Reportes | NOT_STARTED |
| O11 Operación | PARTIAL_UNVERIFIED |
| ECO Economía | DESIGNED_NOT_MERGED |

## Loop correctivo R0

**GOAL:** restablecer verdad documental, bloquear falsos diagnósticos y recuperar feedback de CI.

**ACTION:**

1. actualizar estado y roadmap;
2. restaurar validación documental;
3. impedir `señal presente = regla activada`;
4. conservar cero FV y estado textual;
5. no ejecutar IA sin evidencia evaluada;
6. dejar PR #8 en draft hasta su rebase deliberado.

**FEEDBACK:** ruff, format, mypy, pytest, cobertura, job documental y revisión del diff.

**STOP CONDITION:** documentación y código describen el mismo estado y ninguna regla seed produce hallazgos sin evaluador real.

## Próximo paso después de R0

Implementar plausibilidad física y métricas de energía antes de continuar episodios, IA, UI o facturación.
