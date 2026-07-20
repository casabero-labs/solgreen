# Idea Brief — Solgreen

## Intención

Construir una aplicación científica que permita comprender, vigilar y proteger una planta solar híbrida doméstica a partir de exportaciones SolarMAN y telemetría técnica del inversor.

## Problema

SolarMAN expone grandes volúmenes de variables, pero presenta varias limitaciones:

- gráficos de inspección superficial;
- datos repartidos en formatos diferentes;
- intervalos de muestreo que ocultan transitorios;
- nombres ambiguos y convenciones de signos inconsistentes;
- ausencia de correlación automática entre paneles, batería, red e inversor;
- escasa explicación técnica de eventos;
- dificultad para producir evidencia útil para el instalador.

El propietario necesita pasar de mirar curvas a responder preguntas técnicas: qué ocurrió, cuándo empezó, cuánto duró, qué variables cambiaron, cuál es el riesgo, qué hipótesis son compatibles y qué debe medirse físicamente.

## Usuarios

### Propietario / operador

- carga datos;
- revisa salud y eventos;
- recibe explicaciones sencillas y técnicas;
- genera informes;
- valida observaciones del instalador.

### Instalador / técnico

- consulta episodios y evidencia;
- revisa parámetros antes, durante y después;
- registra diagnóstico, mediciones y acciones;
- confirma o descarta hipótesis.

### Administrador

- gestiona perfiles, reglas, proveedores IA, permisos, retención y auditoría.

### Investigador / analista futuro

- compara periodos e instalaciones anonimizadas;
- evalúa reglas y modelos estadísticos;
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

## Bases fundamentales

1. La física y los datos tienen prioridad sobre la narrativa del LLM.
2. Causa raíz y correlación no son sinónimos.
3. El muestreo aproximado de cinco minutos no permite observar todos los transitorios.
4. Los umbrales deben ser perfiles versionados, no números mágicos.
5. La calidad del dato limita la confianza del diagnóstico.
6. Los originales son inmutables.
7. Toda inferencia debe citar evidencia estructurada.
8. Ninguna acción peligrosa se ejecuta automáticamente.

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
- informe técnico.

## Flujos MVP

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

## Riesgos

- falsos positivos por datos desincronizados;
- inferencias excesivas del LLM;
- umbrales incorrectos para una instalación concreta;
- exposición de datos privados;
- dependencia de nombres de columnas SolarMAN;
- cambios de firmware o formatos;
- interpretación errónea de importación/exportación;
- confundir ausencia de telemetría con ausencia de energía.

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

## Arquitectura sugerida

- React + TypeScript + D3.js;
- FastAPI + Python para análisis;
- PostgreSQL/Butterbase;
- workers asíncronos;
- almacenamiento de objetos;
- MiniMax y DeepSeek detrás de un gateway;
- Coolify + Infisical.

## MCP / agentes

MCP read-only en una fase posterior para consultar plantas, episodios, evidencia y reportes. Escrituras quedan fuera del MVP.

## Tests mínimos

El sistema debe detectar y representar correctamente los episodios dorados del 17 y 19 de julio, además de huecos, saltos de SOC, sobrevoltaje L2, reinicios y caída PV con voltaje presente.

## Fases

Documentación → importación → calidad → timeline → reglas → episodios → visualizaciones → IA → reportes → operación.
