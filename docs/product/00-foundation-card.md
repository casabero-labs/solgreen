# Foundation Card — Solgreen

## Bases no negociables

- Deterministic-first, AI-assisted.
- Originales inmutables y hasheados.
- Unidades, signos y timezone explícitos.
- Hechos, inferencias e hipótesis son tipos diferentes.
- La severidad se calcula fuera del LLM.
- La factura, energía y ahorro se calculan fuera del LLM.
- La confianza depende de evidencia y calidad de datos.
- Cada hallazgo es reproducible por versión del parser, regla y configuración.
- Cada cálculo económico es reproducible por perfil tarifario, fórmula y redondeo.
- Riesgo eléctrico, calidad de datos y oportunidad económica no comparten un score único.
- No hay control automático del inversor ni de electrodomésticos en el MVP.
- Una recomendación nunca puede violar límites confirmados, reserva o restricciones humanas.

## Fuentes de autoridad

1. Mediciones del dispositivo y archivos originales.
2. Manual oficial del modelo y firmware.
3. Configuración real confirmada de la planta.
4. Normativa y perfil de red aplicable.
5. Factura oficial y sus líneas para el periodo facturado.
6. Perfil tarifario oficial vigente y documentado.
7. Medidor fiscal, cuando esté disponible.
8. Principios físicos, económicos y estadísticos documentados.
9. Diagnóstico humano del instalador o revisión humana de factura.
10. Interpretación de IA, siempre subordinada.

La prioridad depende del tipo de afirmación. La factura oficial prevalece para el total facturado; la telemetría prevalece para describir lo observado por el sistema; ninguna de las dos convierte automáticamente una hipótesis técnica en causa confirmada.

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
- causa confirmada;
- potencia;
- energía integrada;
- ciclo de facturación;
- perfil tarifario;
- vigencia;
- medidor fiscal;
- factura oficial;
- estimación;
- forecast;
- conciliación;
- baseline;
- escenario;
- recomendación;
- restricción;
- ahorro estimado.

## Identificadores oficiales

- `plant_id` interno;
- hash SHA-256 del archivo;
- serial cifrado o redaccionado;
- `rule_id` estable y versionado;
- `episode_id` UUID;
- `evidence_id` estable dentro del episodio;
- `analysis_run_id` UUID;
- versión de parser y catálogo;
- `billing_cycle_id` UUID;
- `invoice_id` UUID;
- `tariff_profile_id` UUID y versión;
- `recommendation_id` UUID;
- `scenario_run_id` UUID.

## Datos sensibles

- seriales;
- registradores;
- consumo y horarios;
- ubicación;
- configuraciones;
- credenciales;
- archivos e informes;
- nombre y dirección del titular;
- cuenta, NIC o referencia de contrato;
- número de medidor;
- códigos de pago;
- recibos completos;
- catálogo de hábitos domésticos.

## Estados regulados

Los hallazgos técnicos pueden pasar por:

`detected → interpreted → needs_review → confirmed | dismissed → resolved`

Solo un humano autorizado puede marcar una causa como confirmada.

Las facturas y conciliaciones pueden pasar por:

`uploaded → extracted → needs_review → verified → reconciled | disputed`

Una discrepancia no se clasifica como error del comercializador sin revisión humana y evidencia suficiente.

Las recomendaciones pueden pasar por:

`generated → active → accepted | dismissed | expired`

Aceptar una recomendación no implica ejecución automática.

## Decisiones humanas explícitas

- perfil eléctrico aplicable;
- modelo y límites de batería;
- límites recomendados por fabricante;
- si un evento requiere visita técnica;
- aceptación de una hipótesis;
- autorización para compartir un informe;
- periodo exacto de facturación;
- perfil tarifario aplicable y su vigencia;
- corrección de campos extraídos de una factura;
- restricciones de confort, supervisión y horarios;
- aceptación o descarte de una recomendación;
- autorización de cualquier futura automatización.

## Qué NO puede asumir el agente

- que 0 W significa equipo apagado;
- que una caída PV es una nube;
- que una alarma observada en pantalla aparece en el archivo;
- que un código implica daño;
- que dos señales con timestamps similares fueron capturadas simultáneamente;
- que el SOC es exacto;
- que la red positiva siempre significa exportación;
- que el perfil de red por defecto corresponde a la instalación;
- que una tarifa histórica sigue vigente;
- que 173 kWh es un límite universal o permanente;
- que un porcentaje máximo de subsidio es el descuento efectivo del recibo;
- que SolarMAN y el medidor fiscal registran exactamente la misma energía;
- que todos los cargos pertenecen al componente de energía;
- que una cifra proyectada es una factura garantizada;
- que un pico agregado identifica un electrodoméstico;
- que mover una carga siempre reduce costo o desgaste;
- que bajar la reserva de batería es aceptable;
- que una recomendación puede ignorar confort o supervisión.

## Tests de contrato requeridos

- conservación exacta del hash del original;
- parser idempotente;
- timestamps normalizados sin perder el original;
- reglas determinísticas reproducibles;
- cada afirmación IA referencia evidencias existentes;
- cobertura exacta de issues;
- rechazo de referencias inexistentes o duplicadas;
- separación visual entre medido, calculado e inferido;
- integración de W a kWh usando duración real;
- montos persistidos en centavos enteros;
- perfiles tarifarios con fuente y vigencia;
- bloqueo de perfiles vencidos como vigentes;
- reproducción de golden cases históricos privados;
- separación entre factura estimada y oficial;
- recomendaciones que respetan todas las restricciones;
- ahorros expresados como intervalos y supuestos;
- rechazo de identificación de equipos sin evidencia;
- inmutabilidad del baseline en escenarios.
