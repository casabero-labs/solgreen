# Workflows — Inteligencia económica y gestión de cargas

## 1. Objetivo UX

Permitir que el propietario pase de una curva eléctrica a decisiones verificables:

- cuánto ha comprado a la red;
- cuánto podría facturarse al cierre;
- por qué cambió el costo;
- en qué horas se concentra la compra;
- qué cargas conviene desplazar;
- qué cambia bajo un escenario alternativo.

La interfaz separa siempre `medido`, `calculado`, `proyectado`, `inferido` y `confirmado`.

## 2. Flujo A — Asociar una factura a un ciclo

### Camino feliz

1. El usuario carga un recibo PDF o registra manualmente sus líneas.
2. Solgreen calcula SHA-256 y conserva el original privado.
3. El parser propone proveedor, periodo, energía, CU, subsidio, cargos y total.
4. La interfaz muestra cada valor junto a su ubicación documental y confianza.
5. El usuario corrige o confirma los campos.
6. Solgreen asocia la factura a un `BillingCycle`.
7. El sistema selecciona un `TariffProfile` cuya vigencia y segmento coincidan.
8. Se genera una conciliación reproducible.

### Estados visibles

- `archivo_recibido`;
- `extraccion_pendiente`;
- `requiere_revision`;
- `perfil_tarifario_faltante`;
- `listo_para_conciliar`;
- `conciliado`;
- `diferencia_requiere_revision`.

### Errores esperables

- periodo ilegible;
- factura duplicada;
- recibo de otro servicio;
- perfil tarifario vencido o inexistente;
- línea no reconocida;
- total que no coincide con suma de líneas;
- ciclo solapado.

### Human gates

- confirmar datos extraídos;
- seleccionar o aprobar perfil tarifario;
- aceptar una explicación de discrepancia;
- autorizar compartir el recibo o informe.

## 3. Flujo B — Proyección del ciclo vigente

1. El usuario selecciona un ciclo abierto o Solgreen lo propone.
2. El sistema verifica cobertura SolarMAN y convención de signo.
3. Integra importación observada con reglas de huecos.
4. Construye un baseline por hora y día de semana.
5. Proyecta días faltantes.
6. Aplica el perfil tarifario vigente.
7. Presenta P10, P50 y P90, no una cifra única teatral.
8. Explica qué factores dominan la incertidumbre.

### Resultado mínimo

- kWh acumulados;
- kWh proyectados al corte;
- costo de energía;
- subsidio o crédito estimado;
- cargos no energéticos observados o supuestos;
- total probable;
- días restantes;
- cobertura;
- confianza;
- supuestos.

### Bloqueos

No se muestra una proyección monetaria como vigente cuando:

- no hay perfil tarifario aplicable;
- el ciclo no está definido;
- la convención de importación no está confirmada;
- la cobertura es insuficiente y no existe baseline aceptable.

En esos casos sí puede mostrarse energía observada con advertencia.

## 4. Flujo C — Analizar consumo por hora

1. El usuario elige periodo y clasificación de días.
2. Solgreen calcula perfiles de energía por hora local.
3. La UI muestra heatmap día × hora y curva típica.
4. El usuario alterna consumo, FV, red, batería y SOC.
5. Las horas críticas se explican mediante una cadena causal.

Ejemplo de lectura:

```text
Carga alta 19:00–22:00
  → caída acelerada del SOC
  → batería alcanza reserva
  → importación elevada 22:00–06:00
```

### Visualizaciones

- heatmap de kWh por hora;
- bandas P50/P90/P95;
- curva de SOC inicial y final;
- importación acumulada por franja;
- comparación laboral/festivo;
- comparación entre periodos;
- cobertura y huecos superpuestos.

Una gráfica nunca mezcla W y kWh en el mismo eje sin separación explícita.

## 5. Flujo D — Crear catálogo doméstico

1. El usuario registra un equipo o grupo de cargas.
2. Declara potencia, duración, flexibilidad, prioridad y horarios.
3. Solgreen marca la fuente como `user_declared`.
4. Datos de enchufe o circuito pueden reemplazar estimaciones en el futuro.
5. El usuario puede desactivar recomendaciones por equipo.

La app no identifica automáticamente equipos desde la señal agregada como hecho.

## 6. Flujo E — Recibir una recomendación

1. El motor detecta una oportunidad de desplazamiento.
2. Verifica reserva de batería, ventana solar, potencia coincidente y restricciones.
3. Calcula escenario baseline y escenario sugerido.
4. Produce un intervalo de ahorro e impacto en SOC.
5. El LLM redacta una explicación usando exclusivamente esos resultados.
6. El usuario acepta, descarta o modifica la recomendación.
7. La decisión queda auditada para evaluar utilidad futura.

### Tarjeta de recomendación

Debe mostrar:

- acción concreta;
- mejor ventana;
- ventana que conviene evitar;
- ahorro P10/P50/P90;
- impacto en batería;
- restricciones;
- confianza;
- por qué se recomienda;
- evidencia;
- caducidad.

### Ejemplo de forma, no de resultado garantizado

> Mover la lavadora de 20:00 a 11:00 podría reducir la compra estimada entre 0,4 y 0,8 kWh, manteniendo la reserva nocturna. Cálculo válido para el perfil observado y la fecha indicada.

## 7. Flujo F — Simulador `what-if`

1. El usuario parte de un día real, perfil típico o forecast.
2. Añade una modificación: carga, duración, hora, SOC o producción.
3. Solgreen valida límites y coherencia.
4. Ejecuta baseline y escenario bajo la misma versión del motor.
5. Compara energía, costo, SOC, picos y restricciones.
6. Presenta delta e incertidumbre.

### Casos iniciales

- lavadora a mediodía frente a noche;
- preenfriamiento de habitaciones;
- dos aires simultáneos;
- reducción de 500 W en una franja;
- producción solar 30% menor;
- reserva de batería alternativa permitida;
- escenario futuro AGPE, separado del modo actual.

### Prohibiciones

- no enviar configuraciones al inversor;
- no simular una reserva fuera del rango permitido sin bloquearla;
- no ocultar supuestos;
- no comparar escenarios con versiones o perfiles diferentes sin advertencia.

## 8. Flujo G — Explicación IA

El usuario puede solicitar:

- explicación sencilla;
- explicación técnica;
- comparación de periodos;
- plan diario;
- causas candidatas de una diferencia;
- resumen para instalador o familia.

El payload contiene identificadores, métricas y evidencias mínimas. No incluye el PDF completo, cuenta, dirección ni seriales.

La respuesta debe pasar por:

1. schema JSON;
2. validación de referencias;
3. cobertura exacta de hallazgos;
4. verificación de cifras contra resultados determinísticos;
5. guardrails de incertidumbre;
6. revisión humana cuando el impacto sea alto.

## 9. Telemetría de producto

Eventos mínimos:

- `invoice_uploaded`;
- `invoice_fields_reviewed`;
- `billing_cycle_reconciled`;
- `billing_forecast_viewed`;
- `hourly_profile_filtered`;
- `recommendation_viewed`;
- `recommendation_accepted`;
- `recommendation_dismissed`;
- `scenario_created`;
- `scenario_compared`;
- `economic_ai_interpretation_requested`;
- `economic_ai_interpretation_rejected`.

No se envían montos, direcciones ni identificadores sensibles a analítica de terceros.

## 10. Criterios de éxito

- el usuario puede explicar qué componente movió la factura;
- el total histórico se reproduce dentro de la tolerancia definida;
- cada kWh proviene de una integración trazable;
- las horas críticas tienen cobertura suficiente;
- una recomendación nunca viola reserva o límites confirmados;
- todo ahorro aparece como intervalo;
- la IA no cambia ninguna cifra calculada;
- el flujo funciona sin IA, aunque con menos explicación narrativa.
