# Solgreen Web

Frontend técnico de Solgreen construido con React, TypeScript, Vite y módulos D3.

## Sistema visual

La interfaz aplica exclusivamente Casabero Ink:

- `casabero-labs/estandar-casabero/SKILL.md`;
- `standards/frontend/DESIGN_SYSTEM_INK.md`;
- `examples/frontend/showcase-ink.html`;
- `standards/frontend/UX_UI_MANIFESTO.md`;
- `standards/frontend/HUMAN_FIRST_UX.md`.

Catálogos elegidos:

- **Ink Console** para dashboard, timeline y análisis;
- **Ink Form** para filtros, importación y escenarios;
- **Ink Editorial** para reportes técnicos dentro de la aplicación.

No se mezclan tokens Warm, no hay colores de acento y los estados no dependen únicamente del color.

## Estado U0

Esta primera vertical es ejecutable, pero utiliza datos demostrativos claramente señalados. Valida:

- navegación Planta, Datos y Economía;
- selección de periodo;
- métricas energéticas;
- gráfica D3 con tabla alternativa;
- modo oscuro global;
- estados y bloqueos expresados en lenguaje humano;
- fundación económica Afinia sin presentar COP vigente;
- diseño responsive y `prefers-reduced-motion`.

No incluye todavía:

- autenticación;
- carga web real de CSV/XLSX;
- conexión a endpoints de análisis;
- datos de una planta real;
- factura vigente;
- edición de configuraciones del inversor.

## Desarrollo

```bash
cd apps/web
npm install --no-audit --no-fund
npm run dev
```

## Verificación

```bash
npm run typecheck
npm run test
npm run build
```

`npm run check` ejecuta la cadena completa.

## Human-first gate

Los flujos críticos futuros se cierran únicamente con E2E que pruebe:

```text
abrir → entender → completar → ejecutar → ver feedback → terminar
```

Una captura visual o un test unitario aislado no bastan para cerrar carga de archivos, conciliación, escenarios o generación de informes.
