# AGENTS.md — Solgreen

## Fuente normativa

Antes de actuar, leer el núcleo obligatorio de `casabero-labs/estandar-casabero`:

1. `standards/ai/AI_RULES.md`
2. `standards/ai/AGENT_APPLICATION_FLOW.md`
3. `standards/ai/MCP_STANDARD.md`
4. `standards/ai/LOOP_ENGINEERING.md`

Después cargar solo los estándares pertinentes mediante `casabero-standards-mcp`.

## Fundamentos de Solgreen

Lectura obligatoria antes de modificar lógica de dominio:

- `docs/product/00-foundation-card.md`
- `docs/domain/FOUNDATIONS.md`
- `docs/domain/DATA_CONTRACTS.md`
- `docs/domain/RULE_CATALOG.md`
- `docs/domain/SEVERITY_CONFIDENCE.md`
- `docs/domain/LLM_GUARDRAILS.md`

## Prohibiciones

- No interpretar un cero como ausencia, apagado o falla sin revisar calidad de datos y señales correlacionadas.
- No asumir convención de signos de la red o batería sin perfil de importación versionado.
- No afirmar causa raíz desde un muestreo de cinco minutos.
- No permitir SQL libre, shell libre ni acceso LLM directo a secretos.
- No enviar datasets completos a proveedores de IA cuando basten episodios resumidos.
- No desactivar protecciones como AFCI desde la app.
- No automatizar cambios del inversor durante el MVP.

## Flujo de trabajo

`DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT`

Cada loop debe declarar objetivo, contexto, acciones, feedback objetivo, stop condition, evidencia y próximo paso exacto.

## Arquitectura

Dependencias unidireccionales:

```text
controllers → services → repositories → models
```

El motor científico se implementa mediante funciones puras, reglas versionadas y contratos explícitos.

## Cierre obligatorio

Todo cierre debe incluir:

- comandos ejecutados;
- resultados de tests;
- archivos cambiados;
- limitaciones conocidas;
- estado actual + próximo paso exacto.
