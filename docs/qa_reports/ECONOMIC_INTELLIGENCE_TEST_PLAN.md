# Test Plan — Inteligencia económica y gestión de cargas

## 1. Objetivo

Demostrar que Solgreen calcula energía, factura, perfiles horarios, escenarios y recomendaciones de forma reproducible, sin delegar aritmética crítica al LLM.

Esta fase documental no implementa el motor. Define los contratos de cierre para E1-E5.

## 2. Pirámide de pruebas

### Unitarias

- integración temporal;
- cálculo tarifario;
- subsidios parametrizados;
- redondeo monetario;
- perfiles horarios;
- restricciones de recomendaciones;
- simulación de escenarios;
- validadores de respuestas IA.

### Integración

- flujo SolarMAN → timeline → energía → factura;
- factura parseada → perfil tarifario → conciliación;
- perfil horario → recomendación → explicación IA;
- escenario → comparación → reporte.

### Golden privadas

- recibos reales redactados;
- exportaciones SolarMAN privadas;
- resultados históricos ya revisados;
- nunca se versionan en Git.

### E2E futuras

- cargar factura;
- revisar extracción;
- abrir proyección;
- explorar hora crítica;
- crear equipo;
- aceptar o descartar recomendación;
- comparar escenario;
- exportar informe.

## 3. Tolerancias generales

- Potencia a energía sobre intervalos regulares: error absoluto ≤ 0,001 kWh en fixtures pequeños.
- Integración sobre datos reales: tolerancia declarada según huecos y método.
- Dinero por línea: exactitud al centavo después de aplicar la política de redondeo.
- Total histórico: diferencia máxima de 1 COP cuando todos los componentes y reglas están presentes.
- Proyección: se evalúa calibración de intervalos, no coincidencia exacta de P50.
- Referencias IA: tolerancia cero a identificadores inexistentes.

## 4. Tests del motor de energía

### ENG-001 — No sumar vatios directamente

Input: 12 muestras constantes de 1.000 W separadas cinco minutos.

Expected: 1,0 kWh durante una hora, no 12.000 Wh por suma ciega.

### ENG-002 — Intervalos irregulares

Input: potencias con deltas de 5, 10 y 3 minutos.

Expected: integración usa duración real y registra método.

### ENG-003 — Hueco superior a tolerancia

Input: ausencia de 60 minutos.

Expected: no interpolar silenciosamente; producir rango o energía incompleta con flag.

### ENG-004 — Signo canónico

Input: red SolarMAN negativa bajo perfil confirmado como importación.

Expected: `grid_import_w ≥ 0`, `grid_export_w = 0`.

### ENG-005 — Cobertura insuficiente

Expected: bloquear monto vigente o degradar confianza según contrato.

## 5. Tests tarifarios

### BILL-001 — Perfil fuera de vigencia

Expected: ejecución bloqueada como vigente. Puede usarse solo con `historical_reference` visible.

### BILL-002 — Bloque subsidiable parametrizado

Input: consumo inferior, igual y superior al límite del perfil.

Expected: el motor aplica `min(consumo, limite)` sin asumir un límite universal.

### BILL-003 — Tarifa protegida

Input: método `protected_rate`.

Expected: subsidio = bloque elegible × (CU - tarifa protegida), sin valor negativo.

### BILL-004 — Descuento por kWh

Input: método `discount_per_kwh`.

Expected: subsidio exacto y trazable.

### BILL-005 — Cargos no energéticos

Expected: aseo, alumbrado y ajustes permanecen separados del subtotal de energía.

### BILL-006 — Redondeo

Expected: reproducibilidad al centavo bajo políticas por línea y al total.

### BILL-007 — Perfil sin fuente

Expected: validación rechaza el perfil.

## 6. Golden cases históricos privados

Estos casos se ejecutan fuera del repositorio con recibos redactados y perfiles históricos explícitos.

### GOLD-BILL-2026-04

Periodo: 2026-04-15 a 2026-05-15.

Valores esperados observados:

- energía: 645 kWh;
- CU: 960,12 COP/kWh;
- subsidio de energía: 58.470,54 COP;
- total: 625.720 COP.

Criterio: el parser extrae líneas y el motor reproduce el resultado bajo el perfil histórico correspondiente.

### GOLD-BILL-2026-05

Periodo: 2026-05-15 a 2026-06-16.

Valores esperados observados:

- energía: 694 kWh;
- CU: 934,36 COP/kWh;
- subsidio de energía: 53.171,55 COP;
- total: 662.010 COP.

### GOLD-BASELINE-PRE-SOLAR

Expected: baseline aproximado 21,6 kWh/día sobre los dos ciclos, con duración real del periodo.

### GOLD-SOLARMAN-IMPORT

Expected sobre el dataset privado histórico:

- compra media diaria aproximada: 7,22 kWh/día;
- compra acumulada del tramo analizado: aproximadamente 127,9 kWh;
- el método integra por tiempo y registra cobertura.

### GOLD-HOURLY-NIGHT

Expected:

- la ventana nocturna 21:00–06:00 concentra la mayoría de la importación observada;
- la franja crítica incluye 22:30–01:30;
- la explicación causal distingue carga previa, caída de SOC y posterior importación.

### GOLD-PROJECTION-PARTIAL-CYCLE

Expected histórico:

- energía proyectada: 315–322 kWh;
- total estimado: 285.000–292.000 COP;
- el resultado se etiqueta histórico, no forecast vigente.

## 7. Tests de perfiles horarios

### CONS-001 — Día incompleto

Expected: no tratarlo como día completo; cobertura visible.

### CONS-002 — Percentiles

Expected: P50 ≤ P90 ≤ P95 ≤ máximo para fixtures válidos.

### CONS-003 — Zona horaria

Expected: agrupación por hora `America/Bogota`, no por UTC.

### CONS-004 — Energía frente a potencia

Expected: curva de potencia y barras de kWh usan contratos diferentes.

### CONS-005 — Clasificación de días

Expected: laboral y fin de semana se calculan sobre subconjuntos declarados.

### CONS-006 — Causa temporal

Expected: la explicación no confunde la hora de importación con la hora que agotó la batería.

## 8. Tests de recomendaciones

### LOAD-001 — Ventana solar disponible

Expected: sugiere una ventana con excedente previsto y cobertura suficiente.

### LOAD-002 — Reserva nocturna

Input: escenario que reduce SOC por debajo de reserva confirmada.

Expected: bloquear recomendación.

### LOAD-003 — Potencia coincidente

Input: dos equipos superan límite configurado al coincidir.

Expected: separar horarios o rechazar.

### LOAD-004 — Supervisión

Input: equipo supervisado y ventana fuera del horario permitido.

Expected: no recomendar.

### LOAD-005 — Incertidumbre alta

Expected: intervalo amplio, confianza baja o ausencia de recomendación.

### LOAD-006 — Sin identificación de equipo

Input: pico agregado sin catálogo ni medición por circuito.

Expected: hablar de `carga candidata`, nunca afirmar electrodoméstico.

### LOAD-007 — Ahorro negativo

Expected: no presentar el cambio como recomendación de ahorro.

## 9. Tests del simulador

### SIM-001 — Baseline inmutable

Expected: escenario no modifica muestras ni análisis originales.

### SIM-002 — Delta conservativo

Expected: delta = escenario - baseline bajo misma versión y perfil.

### SIM-003 — Producción 30% menor

Expected: recalcular importación, SOC y costo con supuestos visibles.

### SIM-004 — Cambio de reserva inválido

Expected: bloquear valor fuera del perfil confirmado.

### SIM-005 — Futuro AGPE

Expected: escenario separado, con perfil de compensación explícito; no contaminar modo actual.

## 10. Tests de IA

### AI-ECO-001 — Cifras exactas

Expected: todas las cifras de la respuesta existen en el envelope o son rechazadas.

### AI-ECO-002 — Evidence refs

Expected: cero referencias inexistentes, cruzadas o duplicadas.

### AI-ECO-003 — Cobertura exacta

Expected: un bloque narrativo por hallazgo solicitado, sin duplicaciones.

### AI-ECO-004 — Tarifa inventada

Input: perfil faltante.

Expected: el LLM no propone CU ni total vigente.

### AI-ECO-005 — Garantía de ahorro

Expected: rechazar lenguaje de garantía; exigir intervalo y supuestos.

### AI-ECO-006 — Identificación de equipo

Expected: rechazar afirmación de electrodoméstico sin evidencia.

### AI-ECO-007 — Cambio de configuración

Expected: no recomendar umbrales fuera de límites confirmados ni instruir control automático.

## 11. Tests de privacidad

- recibos reales bloqueados por CI fuera del mecanismo privado;
- cuenta, NIC, dirección y medidor redactados;
- payload LLM no contiene PDF ni identificadores;
- logs no imprimen OCR completo;
- informes compartidos usan política de redacción;
- hashes permiten trazabilidad sin publicar originales.

## 12. Stop conditions por loop

### E1

Contratos y perfiles pasan validación; golden fixtures sintéticos cubren métodos tarifarios.

### E2

Dos recibos históricos se reproducen y la conciliación explica diferencias sin acusaciones automáticas.

### E3

Perfil horario histórico reproduce ventanas críticas con cobertura y energía correctas.

### E4

Recomendaciones respetan todas las restricciones y muestran intervalos.

### E5

Simulador es inmutable y la IA supera validadores con cero referencias inválidas.
