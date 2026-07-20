# Foundation Card — Solgreen

## Bases no negociables

- Deterministic-first, AI-assisted.
- Originales inmutables y hasheados.
- Unidades, signos y timezone explícitos.
- Hechos, inferencias e hipótesis son tipos diferentes.
- La severidad se calcula fuera del LLM.
- La confianza depende de evidencia y calidad de datos.
- Cada hallazgo es reproducible por versión del parser, regla y configuración.
- No hay control automático del inversor en el MVP.

## Fuentes de autoridad

1. Mediciones del dispositivo y archivos originales.
2. Manual oficial del modelo y firmware.
3. Configuración real confirmada de la planta.
4. Normativa y perfil de red aplicable.
5. Principios físicos y estadísticos documentados.
6. Diagnóstico humano del instalador.
7. Interpretación de IA, siempre subordinada.

## Conceptos críticos

- muestra;
- señal;
- lote;
- dato ausente;
- cero medido;
- dato interpolado;
- residual de balance;
- evento;
- episodio;
- evidencia;
- regla;
- severidad;
- confianza;
- hipótesis;
- causa confirmada.

## Identificadores oficiales

- `plant_id` interno;
- hash SHA-256 del archivo;
- serial cifrado o redaccionado;
- `rule_id` estable y versionado;
- `episode_id` UUID;
- `evidence_id` estable dentro del episodio;
- `analysis_run_id` UUID;
- versión de parser y catálogo.

## Datos sensibles

- seriales;
- registradores;
- consumo y horarios;
- ubicación;
- configuraciones;
- credenciales;
- archivos e informes.

## Estados regulados

Los hallazgos pueden pasar por:

`detected → interpreted → needs_review → confirmed | dismissed → resolved`

Solo un humano autorizado puede marcar una causa como confirmada.

## Decisiones humanas explícitas

- perfil eléctrico aplicable;
- modelo y límites de batería;
- límites recomendados por fabricante;
- si un evento requiere visita técnica;
- aceptación de una hipótesis;
- autorización para compartir un informe.

## Qué NO puede asumir el agente

- que 0 W significa equipo apagado;
- que una caída PV es una nube;
- que una alarma observada en pantalla aparece en el archivo;
- que un código implica daño;
- que dos señales con timestamps similares fueron capturadas simultáneamente;
- que el SOC es exacto;
- que la red positiva siempre significa exportación;
- que el perfil de red por defecto corresponde a la instalación.

## Tests de contrato requeridos

- conservación exacta del hash del original;
- parser idempotente;
- timestamps normalizados sin perder el original;
- reglas determinísticas reproducibles;
- cada afirmación IA referencia evidencias existentes;
- cobertura exacta de issues;
- rechazo de referencias inexistentes o duplicadas;
- separación visual entre medido, calculado e inferido.
