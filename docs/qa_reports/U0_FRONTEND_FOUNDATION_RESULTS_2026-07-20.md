# Resultado QA — U0 Frontend Showcase Ink

## Identificación

- Fecha: 2026-07-20
- Rama: `develop/solgreen-unified`
- SHA verificado: `4565de0a12d5dde9062660220acd63c50bc423c7`
- Pull request: #27
- Workflow: CI run #86
- Resultado: `success`

## Alcance

Validación de la fundación unificada U0:

- documentación y privacidad;
- baseline Python;
- frontend React + TypeScript + D3;
- restricciones Showcase Ink;
- tests de comportamiento;
- build de producción.

## Resultados

### Documentation + Privacy

**PASS**

- documentos canónicos presentes;
- dominio económico y frontend presentes;
- exports CSV/XLSX privados rechazados fuera de fixtures;
- archivos `.env` rechazados fuera de rutas permitidas.

### Python Quality + Tests

**PASS**

- Ruff;
- formato incremental de archivos Python modificados;
- mypy;
- pytest con cobertura mínima configurada.

No se modificó lógica Python en U0, pero se verificó que la integración documental y frontend no rompiera el baseline.

### Frontend Typecheck + Tests + Build

**PASS**

- instalación de dependencias;
- guarda Showcase Ink;
- TypeScript strict;
- Vitest + Testing Library;
- Vite production build.

## Casos frontend cubiertos

- aviso persistente de datos demostrativos;
- cambio de periodo y actualización de métricas;
- bloqueo de resultados COP sin perfil tarifario verificado;
- modo oscuro global;
- navegación Planta, Datos y Economía;
- gráfica D3 acompañada de tabla alternativa.

## Guarda Showcase Ink

La CI rechaza:

- Playfair o serif de la variante Warm;
- tokens `accent`, `danger` o `success`;
- gradientes decorativos;
- `backdrop-filter`;
- colores hexadecimales fuera de la paleta Ink clara y oscura autorizada.

La revisión humana sigue siendo obligatoria para evaluar jerarquía, densidad, comprensión y flujo completo.

## Incidente durante la verificación

El primer typecheck detectó incompatibilidad entre Vite 6 y los tipos incluidos por Vitest 2. No se usaron casts ni silencios.

Corrección:

- Vite alineado a `5.4.11`;
- Vitest conservado en `2.1.8`;
- TypeScript volvió a una única familia compatible de contratos Vite.

Resultado posterior: typecheck, tests y build correctos.

## Limitaciones

- los datos son demostrativos;
- no existe importación web real;
- no hay API de análisis conectada;
- no hay Playwright todavía;
- no se validó una factura vigente;
- no se desplegó la aplicación;
- no se cerró el human gate de U0.

## Stop condition

La condición técnica de U0 está satisfecha. Permanece pendiente únicamente:

1. revisión humana de la interfaz;
2. decisión de cierre U0;
3. mantener el PR como draft hasta esa revisión.

## Estado actual + próximo paso exacto

**Estado actual:** CI U0 completa en verde sobre `4565de0`.

**Próximo paso exacto:** revisar visualmente y funcionalmente el frontend U0; después marcar U0 cerrado e iniciar U1 sin abrir otra línea de desarrollo.
