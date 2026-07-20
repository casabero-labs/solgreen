# Guardrails de IA

## Entrada permitida

- metadatos mínimos de planta;
- episodio estructurado;
- evidencias numeradas;
- reglas activadas;
- calidad de datos;
- extractos autorizados de manuales;
- límites explícitos.

## Salida obligatoria

- resumen;
- hechos citados por `evidenceRefs`;
- hipótesis con nivel de soporte;
- alternativas;
- información faltante;
- acciones sugeridas;
- advertencias;
- afirmaciones prohibidas evitadas.

## Validaciones

- schema JSON estricto;
- referencias existentes;
- cero referencias cruzadas entre issues;
- cobertura exacta, sin duplicados;
- columnas y señales coherentes con el issue;
- unidades compatibles;
- ninguna causa “confirmada” sin flag humano;
- ninguna severidad inventada;
- límites de longitud y coste.

## Estrategia multiproveedor

- proveedor primario para interpretación;
- segundo proveedor para eventos de alta severidad;
- comparador determinístico de coincidencias y discrepancias;
- no se promedia “confianza” textual del modelo.
