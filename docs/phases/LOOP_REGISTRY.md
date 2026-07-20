# Loop Registry — Solgreen

## Metodología

Solgreen aplica `casabero-labs/estandar-casabero`:

```text
DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT
```

Cada loop debe declarar `GOAL`, `CONTEXT`, `ACTION`, `FEEDBACK`, `STOP CONDITION`, `HUMAN GATE`, `ROLLBACK` y próximo paso exacto.

## Feedback disponible

- schemas de los dos datasets;
- fixtures sintéticos;
- datasets privados iniciales fuera de Git;
- episodios dorados del 17 y 19 de julio;
- pruebas unitarias e integración;
- CI;
- revisión humana del propietario;
- diagnóstico posterior del instalador.

## Comandos de verificación

```bash
uv sync --extra dev --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy solgreen
uv run pytest
```

## Human gates

- perfil real de planta;
- límites de batería y red;
- severidad crítica;
- confirmación de causa;
- aprobación de umbrales;
- merge;
- reportes compartidos;
- deploy automático;
- cualquier capacidad de escritura sobre equipos.

## Límites de iteración

- un solo objetivo verificable por loop;
- máximo tres correcciones automáticas antes de escalar;
- no mezclar feature, refactor y deploy si pueden separarse;
- ningún loop se cierra si docs, tests y código se contradicen.

## Estado oficial

| Track | Objetivo | Feedback | Stop condition | Estado |
|---|---|---|---|---|
| F0 | Fundamentos y contratos | revisión documental | cero contradicciones críticas | NEEDS_RECONCILIATION |
| I1 | Importación reproducible | parser/hash/tests | ambos formatos reproducibles | CLOSED |
| Q2 | Calidad de datos | tests de calidad | plausibilidad y cobertura verificadas | PARTIAL |
| T3 | Timeline canónico | tests de join/lineage | cada valor rastreable a ambas fuentes | PARTIAL |
| M4 | Métricas físicas | fixtures y fórmulas | energía, balance, batería, PV y red validados | NOT_STARTED |
| E5 | Eventos y episodios | golden cases | 17 y 19 reconstruidos | PROTOTYPE_ONLY |
| R6 | Reglas determinísticas | tests por regla | condición real evaluada, no presencia de señal | CATALOG_ONLY |
| A7 | IA validada | schema, refs y adversarial tests | cero respuestas inválidas aceptadas | EXPERIMENTAL_BLOCKED |
| P8 | Persistencia | integración PostgreSQL | lineage, idempotencia y migraciones probadas | PARTIAL |
| U9 | UI y D3 | E2E humano | exploración completa y accesible | NOT_STARTED |
| G10 | Reportes | golden PDF | instalador audita cada hallazgo | NOT_STARTED |
| O11 | Operación | deploy + SHA + health | restore y smoke documentados | PARTIAL_UNVERIFIED |
| ECO | Afinia y gestión de cargas | golden billing | factura y horarios reproducibles | DESIGNED_NOT_MERGED |

## Loop correctivo activo

### R0 — Development reconciliation and safety gate

**GOAL:** alinear estado documental y código, bloquear falsos diagnósticos y restaurar feedback de CI.

**CONTEXT:** auditoría 2026-07-20, PRs #9–#19, PR #8, estándares Casabero.

**ACTION:**

1. reconciliar README, CHANGELOG, NEXT_STEPS y este registro;
2. restaurar validación documental y de privacidad;
3. impedir que una regla se active solo porque una señal existe;
4. conservar cero medido y estados textuales;
5. bloquear IA cuando no exista evidencia evaluada;
6. dejar la pista económica pendiente de rebase.

**FEEDBACK:** ruff, format, mypy, pytest, cobertura, CI documental y revisión del PR.

**STOP CONDITION:** documentación y código describen el mismo estado y ninguna salida experimental puede presentarse como diagnóstico real.

**HUMAN GATE:** merge del PR correctivo y decisión sobre rebase del PR #8.

**ROLLBACK:** cerrar el PR sin merge; `main` permanece intacta.

## Próximo loop después de R0

### Q2.3 — Plausibilidad física y calidad avanzada

- saltos SOC;
- temperaturas imposibles;
- signos contradictorios;
- huecos ponderados por duración;
- lote vacío no perfecto;
- consistencia básica entre fuentes.

No avanzar a UI, facturación o diagnósticos IA hasta cerrar M4, E5 y R6 con golden cases.
