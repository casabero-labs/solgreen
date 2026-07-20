# Inteligencia económica y gestión de cargas

## 1. Propósito

Este subsistema convierte telemetría SolarMAN, recibos de energía y perfiles tarifarios versionados en resultados económicos y operativos reproducibles:

- estimación y conciliación de facturas;
- proyección del ciclo vigente con intervalo de incertidumbre;
- perfiles de consumo, producción, batería y compra por hora;
- identificación de ventanas críticas de importación;
- recomendaciones de desplazamiento de cargas;
- simulaciones `what-if`;
- explicaciones asistidas por IA sobre resultados ya calculados.

No sustituye el medidor fiscal, la factura emitida por el comercializador ni la decisión humana sobre confort o seguridad.

## 2. Principio rector

```text
Datos SolarMAN + factura + perfil tarifario
  → validación de calidad y vigencia
  → integración de potencia a energía
  → cálculo tarifario determinístico
  → perfiles horarios y escenarios
  → recomendaciones con restricciones
  → interpretación IA validada
  → decisión humana
```

La IA no calcula dinero, energía, horarios óptimos ni restricciones. Recibe resultados estructurados y los explica.

## 3. Fuentes de autoridad

En orden descendente:

1. factura oficial del periodo y sus líneas;
2. perfil tarifario oficial vigente y documentado;
3. medición del contador fiscal, cuando esté disponible;
4. exportación SolarMAN validada e integrada;
5. configuración confirmada de planta y batería;
6. catálogo de electrodomésticos declarado por el usuario;
7. inferencias estadísticas;
8. interpretación del LLM.

Una factura histórica puede ser fixture de regresión, pero no autoriza usar sus tarifas para meses futuros.

## 4. Alcance funcional

### 4.1 Motor de factura

Calcula por periodo:

```text
energia_bruta = consumo_facturable_kwh × cu_cop_kwh
energia_subsidiable = min(consumo_facturable_kwh, limite_subsidiable_kwh)
subsidio = energia_subsidiable × descuento_efectivo_cop_kwh
subtotal_energia = energia_bruta - subsidio
factura_estimada = subtotal_energia + cargos_no_energia + ajustes - creditos
```

La fórmula exacta debe ser configurable por `TariffProfile`. No se permiten números mágicos en código.

El motor debe conservar:

- valores sin redondear;
- regla de redondeo por línea y total;
- moneda;
- versión del perfil;
- periodo de vigencia;
- fuente documental;
- explicación de cada componente.

### 4.2 Conciliación

Compara:

- energía importada estimada desde SolarMAN;
- energía registrada en la factura;
- subtotal de energía calculado;
- subsidio calculado;
- cargos observados;
- total estimado frente al total facturado.

La diferencia se reporta en kWh, COP y porcentaje, con causas candidatas:

- cobertura incompleta;
- desfase del ciclo;
- signo de red incorrecto;
- pérdidas y consumos fuera del punto medido;
- redondeo;
- lectura fiscal distinta a SolarMAN;
- cambio tarifario;
- ajuste o saldo anterior.

Nunca se acusa error de facturación automáticamente.

### 4.3 Proyección del ciclo

Produce un intervalo, no una falsa cifra exacta:

- compra acumulada;
- compra proyectada al corte;
- costo de energía proyectado;
- cargos fijos o estimados;
- factura total probable;
- percentiles P10, P50 y P90;
- días restantes;
- cobertura y confianza.

La proyección combina, según disponibilidad:

- importación integrada observada;
- perfil por hora y día de semana;
- días faltantes;
- estacionalidad reciente;
- producción solar y SOC;
- clima futuro en una fase posterior;
- baseline anterior al sistema solar.

### 4.4 Perfil horario

Para cada hora local calcula:

- consumo kWh y potencia media;
- producción FV;
- importación y exportación;
- carga y descarga de batería;
- SOC inicial, final y pendiente;
- P50, P90, P95 y máximo;
- cobertura;
- días observados;
- diferencia laboral/festivo;
- diferencia soleado/nublado cuando exista clasificación confiable.

Las visualizaciones deben distinguir potencia instantánea de energía integrada.

### 4.5 Recomendaciones de cargas

Una recomendación es una propuesta, no una orden. Optimiza múltiples objetivos:

1. reducir compra a red;
2. aprovechar excedente FV;
3. mantener reserva de batería;
4. evitar picos simultáneos;
5. respetar confort, horarios y supervisión;
6. no superar límites confirmados de batería e inversor.

Cada recomendación incluye:

- equipo o clase de carga;
- ventana recomendada;
- ventana evitada;
- ahorro esperado en kWh y COP como intervalo;
- impacto estimado en SOC;
- restricciones aplicadas;
- evidencia;
- confianza;
- fecha de caducidad.

Sin medición por circuito, Solgreen no puede afirmar qué electrodoméstico produjo un pico. Solo puede recomendar sobre equipos declarados y patrones agregados.

### 4.6 Simulador `what-if`

Escenarios iniciales:

- mover una carga de una hora a otra;
- variar duración y potencia;
- encender dos aires simultáneamente;
- modificar una reserva de SOC dentro de límites permitidos;
- reducir una carga base nocturna;
- simular menor producción solar;
- comparar autoconsumo frente a futura operación AGPE.

El simulador debe mostrar baseline, escenario, delta, supuestos y límites. No modifica el inversor.

## 5. Modelos de dominio

- `TariffProfile`
- `InvoiceDocument`
- `BillingCycle`
- `InvoiceLine`
- `BillingEstimate`
- `BillingReconciliation`
- `HourlyEnergyProfile`
- `ApplianceProfile`
- `LoadRecommendation`
- `ScenarioDefinition`
- `ScenarioRun`
- `EconomicAIInterpretation`

Los contratos detallados están en `DATA_CONTRACTS.md` y `data-dictionary/afinia-billing.md`.

## 6. Calidad y confianza

La confianza económica depende de:

- coincidencia exacta del ciclo;
- cobertura temporal;
- resolución y regularidad de muestras;
- convención de signo confirmada;
- vigencia del perfil tarifario;
- factura oficial disponible;
- tratamiento de huecos;
- reconciliación con acumulados del inversor;
- estabilidad del baseline.

Si falta el perfil tarifario vigente, Solgreen puede proyectar kWh, pero no debe presentar COP como resultado vigente.

## 7. Papel de la IA

El LLM puede:

- explicar por qué aumentó o bajó una factura;
- resumir las horas críticas;
- comparar escenarios;
- convertir restricciones en un plan doméstico legible;
- señalar hipótesis de discrepancia;
- redactar recomendaciones en versión técnica y sencilla.

No puede:

- crear tarifas;
- asumir que un límite histórico sigue vigente;
- alterar resultados calculados;
- identificar un electrodoméstico sin evidencia;
- recomendar descargar por debajo de un límite confirmado;
- presentar ahorro como garantía;
- omitir incertidumbre.

Toda interpretación debe referenciar entidades y evidencias existentes.

## 8. Golden cases privados

Los recibos y cálculos reales permanecen fuera de Git. Se documentan resultados históricos sin identificadores personales para pruebas privadas:

- periodo 2026-04-15 a 2026-05-15: 645 kWh, CU 960,12 COP/kWh, subsidio de energía 58.470,54 COP y total 625.720 COP;
- periodo 2026-05-15 a 2026-06-16: 694 kWh, CU 934,36 COP/kWh, subsidio de energía 53.171,55 COP y total 662.010 COP;
- baseline anterior al solar: aproximadamente 21,6 kWh/día;
- análisis histórico SolarMAN: compra media aproximada 7,22 kWh/día y concentración nocturna dominante;
- proyección histórica de un ciclo parcial: 315–322 kWh y 285.000–292.000 COP.

Estos valores prueban regresión. No son tarifas ni promesas actuales.

## 9. Privacidad

Las facturas pueden contener nombre, dirección, cuenta, NIC, medidor y hábitos horarios. Reglas:

- archivo original privado e inmutable;
- hash SHA-256;
- identificadores redactados en reportes compartidos;
- no enviar la factura completa a proveedores IA;
- enviar solo hechos mínimos estructurados;
- retención y sharing explícitos;
- exportaciones privadas fuera de Git.

## 10. Dependencias de implementación

La pista económica no desplaza el roadmap técnico:

- cálculo horario depende de L2, L3 y L4;
- recomendaciones dependen de perfiles horarios confiables;
- explicación IA depende de L8;
- factura puede modelarse antes, pero la reconciliación necesita energía integrada;
- cualquier automatización física queda fuera del MVP.
