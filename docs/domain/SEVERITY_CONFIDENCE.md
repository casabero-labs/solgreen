# Severidad y confianza

## Severidad

La severidad mide impacto potencial:

- `info`: observación sin riesgo inmediato.
- `low`: desviación menor o aislada.
- `medium`: condición que requiere seguimiento.
- `high`: riesgo técnico o repetición relevante.
- `critical`: riesgo inmediato de seguridad, daño o indisponibilidad severa.

Factores:

- magnitud;
- duración;
- recurrencia;
- número de subsistemas;
- proximidad a límites;
- respuesta de protecciones;
- impacto en continuidad.

## Confianza

La confianza mide calidad de la conclusión:

- cobertura de señales;
- consistencia entre datasets;
- precisión temporal;
- calidad del parser;
- plausibilidad física;
- disponibilidad de log nativo;
- confirmación humana.

Un episodio puede ser `high severity` con `low confidence`.

## Regla de presentación

Nunca mezclar ambos conceptos en un único porcentaje opaco.
