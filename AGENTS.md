# AGENTS.md — Solgreen

## Fuente normativa

Antes de actuar, leer el núcleo obligatorio de `casabero-labs/estandar-casabero`:

1. `standards/ai/AI_RULES.md`
2. `standards/ai/AGENT_APPLICATION_FLOW.md`
3. `standards/ai/MCP_STANDARD.md`
4. `standards/ai/LOOP_ENGINEERING.md`

Después cargar solo los estándares pertinentes mediante `casabero-standards-mcp`.

## Línea única de desarrollo

Solgreen mantiene una sola línea activa de producto:

```text
main → develop/solgreen-unified → un único PR activo
```

- `main` es la fuente estable.
- `develop/solgreen-unified` integra backend, motor científico, economía, frontend, IA y operación.
- No abrir ramas paralelas de feature mientras la integración unificada esté activa.
- Los issues representan loops o bloqueadores, no líneas alternativas.
- Hotfixes de producción son la única excepción y requieren rollback documentado.
- Leer `docs/phases/UNIFIED_DEVELOPMENT_LINE.md` antes de planear nuevas capacidades.

## Fundamentos de Solgreen

Lectura obligatoria antes de modificar lógica de dominio:

- `docs/product/00-foundation-card.md`
- `docs/domain/FOUNDATIONS.md`
- `docs/domain/DATA_CONTRACTS.md`
- `docs/domain/RULE_CATALOG.md`
- `docs/domain/SEVERITY_CONFIDENCE.md`
- `docs/domain/LLM_GUARDRAILS.md`
- `docs/domain/ECONOMIC_INTELLIGENCE.md`
- `docs/domain/data-dictionary/afinia-billing.md`

## Diseño UI/UX

Solgreen usa exclusivamente **Casabero Ink**. Antes de escribir o revisar UI, consultar:

1. `casabero-labs/estandar-casabero/SKILL.md`;
2. `standards/frontend/DESIGN_SYSTEM_INK.md`;
3. `examples/frontend/showcase-ink.html`;
4. `standards/frontend/UX_UI_MANIFESTO.md`;
5. `standards/frontend/HUMAN_FIRST_UX.md`.

Aplicación por superficie:

- Ink Console: dashboard, timeline, calidad y episodios;
- Ink Form: importación, filtros, factura y escenarios;
- Ink Editorial: reportes técnicos dentro de la app.

Prohibiciones:

- no mezclar tokens Warm;
- no crear una cuarta variante visual;
- no usar serif, gradientes decorativos, glass o colores de acento;
- no comunicar estado solo con color;
- no cerrar un flujo crítico con screenshots o unit tests aislados;
- toda gráfica crítica debe tener tabla alternativa accesible;
- datos demo, calculados, proyectados e inferidos deben identificarse explícitamente.

Arquitectura frontend: `docs/frontend/FRONTEND_ARCHITECTURE.md`.

## Prohibiciones de dominio

- No interpretar un cero como ausencia, apagado o falla sin revisar calidad de datos y señales correlacionadas.
- No asumir convención de signos de la red o batería sin perfil de importación versionado.
- No afirmar causa raíz desde un muestreo de cinco minutos.
- No permitir SQL libre, shell libre ni acceso LLM directo a secretos.
- No enviar datasets completos a proveedores de IA cuando basten episodios resumidos.
- No desactivar protecciones como AFCI desde la app.
- No automatizar cambios del inversor durante el MVP.
- No presentar COP vigente sin perfil tarifario verificado y aplicable.
- No delegar cálculos de energía, factura, subsidio o ahorro al LLM.

## Flujo de trabajo

`DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE → CLOSEOUT`

Cada loop debe declarar objetivo, contexto, acciones, feedback objetivo, stop condition, human gate, rollback, evidencia y próximo paso exacto.

## Arquitectura

Dependencias unidireccionales:

```text
controllers → services → repositories → models
```

El motor científico y económico se implementa mediante funciones puras, reglas versionadas y contratos explícitos. React gobierna el estado de interfaz; D3 calcula escalas y geometría, pero no crea una segunda arquitectura de estado.

## Cierre obligatorio

Todo cierre debe incluir:

- comandos ejecutados;
- resultados de tests;
- archivos cambiados;
- limitaciones conocidas;
- evidencia Human-First cuando aplique;
- estado actual + próximo paso exacto.
