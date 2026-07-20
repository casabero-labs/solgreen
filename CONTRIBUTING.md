# Contribuir a Solgreen

## Antes de abrir cambios

1. Identificar el loop activo en `docs/phases/LOOP_REGISTRY.md`.
2. Leer los fundamentos del dominio relacionados.
3. Declarar datos de prueba y evidencia esperada.
4. Diseñar tests antes de modificar una regla crítica.

## Reglas

- Commits pequeños y semánticos.
- Una regla nueva exige: definición, fuente, fixture válido, fixture inválido y test de regresión.
- Una visualización nueva debe declarar: pregunta analítica, datos, transformación, codificación visual y limitaciones.
- Una integración LLM nueva debe pasar el mismo schema y validador que los demás proveedores.
- No versionar datos reales de la vivienda.

## Pull requests

Toda PR debe incluir:

- problema y alcance;
- fundamento del dominio;
- archivos modificados;
- evidencia y comandos;
- capturas cuando toque UX;
- riesgos y rollback;
- siguiente paso.
