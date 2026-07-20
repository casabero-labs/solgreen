# Idea Brief — Solgreen

## Intención

Construir una aplicación científica que permita comprender, vigilar y proteger una planta solar híbrida doméstica a partir de exportaciones SolarMAN, telemetría técnica del inversor, recibos de energía y perfiles tarifarios versionados.

Además de prevenir daños, Solgreen debe ayudar a comprender el costo real de la energía, detectar cuándo y por qué se compra a la red, proyectar facturas y proponer cambios de horario sin sacrificar seguridad, reserva de batería ni confort.

## Problema

SolarMAN expone grandes volúmenes de variables, pero presenta varias limitaciones:

- gráficos de inspección superficial;
- datos repartidos en formatos diferentes;
- intervalos de muestreo que ocultan transitorios;
- nombres ambiguos y convenciones de signos inconsistentes;
- ausencia de correlación automática entre paneles, batería, red e inversor;
- escasa explicación técnica de eventos;
- dificultad para producir evidencia útil para el instalador;
- ausencia de conciliación entre energía importada y factura oficial;
- poca visibilidad sobre las horas que agotan la batería;
- falta de recomendaciones trazables para desplazar cargas;
- imposibilidad de comparar escenarios domésticos de forma reproducible.

El propietario necesita pasar de mirar curvas a responder preguntas técnicas y económicas: qué ocurrió, cuándo empezó, cuánto duró, qué variables cambiaron, cuál es el riesgo, cuánto se compró, cuánto podría facturarse, qué hipótesis son compatibles y qué acción conviene probar.

## Usuarios

### Propietario / operador

- carga datos y facturas;
- revisa salud, eventos, consumo y costo;
- recibe explicaciones sencillas y técnicas;
- analiza horas críticas;
- prueba escenarios;
- recibe recomendaciones conservadoras;
- genera informes;
- valida observaciones del instalador.

### Instalador / técnico

- consulta episodios y evidencia;
- revisa parámetros antes, durante y después;
- registra diagnóstico, mediciones y acciones;
- confirma o descarta hipótesis;
- verifica que recomendaciones respeten límites reales.

### Administrador

- gestiona perfiles de planta, red y tarifa;
- administra reglas, proveedores IA, permisos, retención y auditoría;
- mantiene fuentes y vigencias.

### Investigador / analista futuro

- compara periodos e instalaciones anonimizadas;
- evalúa reglas y modelos estadísticos;
- analiza eficiencia, economía y comportamiento;
- exporta datos derivados.

## Resultado esperado

La app debe producir una línea de tiempo verificable y una lista priorizada de episodios con:

- hechos medidos;
- calidad de datos;
- reglas activadas;
- severidad determinística;
- confianza de evidencia;
- hipótesis diferenciadas de hechos;
- acciones técnicas sugeridas;
- trazabilidad hasta archivo, fila, señal y versión del motor.

También debe producir resultados económicos separados del riesgo eléctrico:

- energía importada integrada;
- factura estimada y conciliada;
- forecast P10/P50/P90;
- desglose de tarifa, subsidio y cargos;
- perfiles de consumo, FV, red, batería y SOC por hora;
- ventanas críticas y su cadena causal;
- recomendaciones con restricciones y caducidad;
- escenarios comparables con supuestos visibles.

## Bases fundamentales

1. La física y los datos tienen prioridad sobre la narrativa del LLM.
2. Causa raíz y correlación no son sinónimos.
3. El muestreo aproximado de cinco minutos no permite observar todos los transitorios.
4. Los umbrales y tarifas deben ser perfiles versionados, no números mágicos.
5. La calidad del dato limita la confianza del diagnóstico y la proyección.
6. Los originales son inmutables.
7. Toda inferencia debe citar evidencia estructurada.
8. Ninguna acción peligrosa se ejecuta automáticamente.
9. La factura oficial y el medidor fiscal prevalecen en conciliación económica.
10. Un ahorro se expresa como intervalo, no como garantía.
11. Riesgo eléctrico, calidad del dato y oportunidad económica son dimensiones distintas.
12. La app debe funcionar sin IA; el LLM mejora interpretación, no autoridad.

## Datos principales

- archivo y lote de importación;
- muestras de flujo de planta;
- muestras técnicas del inversor;
- timeline canónico sincronizado;
- métricas derivadas;
- regla y ejecución de regla;
- evidencia;
- episodio;
- interpretación IA;
- revisión humana;
- informe técnico;
- factura y líneas normalizadas;
- ciclo de facturación;
- perfil tarifario;
- estimación y conciliación;
- perfil energético horario;
- catálogo de cargas;
- recomendación;
- definición y ejecución de escenario.

## Flujos MVP técnicos

1. Cargar uno o dos archivos.
2. Reconocer formato y validar estructura.
3. Crear lote inmutable y calcular hash.
4. Normalizar timestamps, unidades y signos.
5. Mostrar informe de calidad.
6. Ejecutar reglas determinísticas.
7. Agrupar señales en episodios.
8. Explorar el episodio con D3.js.
9. Solicitar interpretación IA validada.
10. Generar informe técnico.

## Flujos económicos incrementales

1. Cargar o registrar una factura.
2. Revisar campos y asociar ciclo.
3. Seleccionar perfil tarifario vigente o histórico.
4. Reproducir y conciliar el cálculo.
5. Proyectar ciclo abierto con intervalo.
6. Explorar consumo y compra por hora.
7. Declarar electrodomésticos y restricciones.
8. Recibir recomendaciones trazables.
9. Comparar escenarios `what-if`.
10. Solicitar explicación IA sin delegar cálculos.

La pista económica no bloquea L2 y no adelanta recomendaciones antes de contar con calidad, timeline y métricas físicas confiables.

## Riesgos

- falsos positivos por datos desincronizados;
- inferencias excesivas del LLM;
- umbrales incorrectos para una instalación concreta;
- exposición de datos privados;
- dependencia de nombres de columnas SolarMAN;
- cambios de firmware o formatos;
- interpretación errónea de importación/exportación;
- confundir ausencia de telemetría con ausencia de energía;
- utilizar una tarifa histórica como vigente;
- asumir que SolarMAN coincide con el medidor fiscal;
- identificar electrodomésticos sin medición por circuito;
- recomendaciones que erosionen reserva o confort;
- proyecciones con falsa precisión.

## Pantallas iniciales

- Importaciones.
- Resumen de salud.
- Explorador temporal.
- Episodios.
- Paneles y MPPT.
- Batería.
- Red.
- Inversor y temperaturas.
- Calidad de datos.
- Laboratorio IA.
- Reportes.
- Configuración.

## Pantallas económicas

- Factura y ahorro.
- Ciclo vigente y forecast.
- Consumo por hora.
- Ventanas críticas.
- Catálogo de cargas.
- Recomendaciones.
- Simulador de escenarios.
- Conciliación y fuentes tarifarias.

## Arquitectura sugerida

- React + TypeScript + D3.js;
- FastAPI + Python para análisis;
- PostgreSQL/Butterbase;
- workers asíncronos;
- almacenamiento de objetos;
- MiniMax y DeepSeek detrás de un gateway;
- Coolify + Infisical;
- motores económicos como servicios separados del diagnóstico eléctrico.

## MCP / agentes

MCP read-only en una fase posterior para consultar plantas, episodios, evidencia, ciclos, perfiles horarios, estimaciones y reportes. Escrituras quedan fuera del MVP.

## Tests mínimos

El sistema debe detectar y representar correctamente los episodios dorados del 17 y 19 de julio, además de huecos, saltos de SOC, sobrevoltaje L2, reinicios y caída PV con voltaje presente.

La pista económica debe reproducir recibos históricos privados, integrar correctamente potencia a energía, detectar ventanas nocturnas, bloquear perfiles vencidos y rechazar cualquier respuesta IA que cambie cifras o invente referencias.

## Fases

Documentación → importación → calidad → timeline → métricas → reglas → episodios → visualizaciones → IA → reportes → operación.

Pista económica paralela: fundamentos → contratos tarifarios → conciliación y forecast → perfiles horarios → recomendaciones → escenarios e interpretación IA.
