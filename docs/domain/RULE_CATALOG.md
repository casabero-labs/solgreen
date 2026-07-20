# Catálogo inicial de reglas

Las reglas son determinísticas, versionadas y parametrizadas por perfil de planta, red o tarifa.

## Reglas técnicas y de calidad

| ID | Nombre | Señales principales | Resultado |
|---|---|---|---|
| DATA-001 | Intervalo ausente | timestamps | hueco de telemetría |
| DATA-002 | Timestamp duplicado | timestamp + hash fila | duplicado |
| DATA-003 | Salto SOC físicamente improbable | SOC, potencia, duración, capacidad | recalibración/dato anómalo |
| DATA-004 | Temperatura imposible | temperaturas | sensor/escala inválida |
| DATA-005 | Balance instantáneo incoherente | FV, carga, red, batería | dato desincronizado |
| BAT-001 | SOC bajo | SOC | advertencia/alarma |
| BAT-002 | Descarga profunda | SOC + duración | estrés de batería |
| BAT-003 | Carga elevada | V, A, W, límites BMS | posible exceso |
| BAT-004 | Descarga elevada | V, A, W, límites BMS | posible exceso |
| BAT-005 | Caída de voltaje bajo carga | V, A, SOC | sag/resistencia |
| BAT-006 | SOC estancado o recalibrado | SOC, energía integrada | estimador inconsistente |
| PV-001 | Dropout FV con voltaje presente | PV1/2 V-A-W | interrupción de conversión |
| PV-002 | Caída simultánea MPPT | PV1/2 | evento común del bloque FV |
| PV-003 | Asimetría persistente | PV1 vs PV2 | string/MPPT desigual |
| PV-004 | Recuperación abrupta | potencia y pendiente | retorno tras protección |
| PV-005 | Clipping probable | potencia plana cerca del límite | limitación por potencia |
| GRID-001 | Sobrevoltaje | L1/L2 | red fuera de rango |
| GRID-002 | Bajo voltaje | L1/L2 | red fuera de rango |
| GRID-003 | Pérdida de red | voltajes, estado | outage/aislamiento |
| GRID-004 | Desequilibrio L1/L2 | L1/L2 | fase/neutro sospechoso |
| GRID-005 | Exportación transitoria | flujo de red + balance | posible zero-export lento |
| INV-001 | Tormenta de inicializaciones | estado de máquina | reinicios repetidos |
| INV-002 | Waiting prolongado | estado + carga | indisponibilidad |
| INV-003 | Temperatura alta | temperaturas + carga | estrés/derating |
| INV-004 | Estado interno nuevo | System Status | transición no habitual |
| INV-005 | BUS anómalo | BUS positivo/negativo | electrónica DC interna |
| CORR-001 | Episodio multicapa | reglas cercanas | correlación de eventos |

## Reglas económicas y de consumo planificadas

Estas reglas producen **estado económico u oportunidad**, no severidad eléctrica. No deben elevar o reducir el riesgo técnico de un episodio.

| ID | Nombre | Inputs principales | Resultado |
|---|---|---|---|
| BILL-001 | Perfil tarifario ausente o vencido | ciclo, vigencia, fuente | cálculo monetario bloqueado o histórico |
| BILL-002 | Discrepancia de conciliación | kWh SolarMAN, kWh factura, cobertura | revisión de conciliación |
| BILL-003 | Cruce del bloque subsidiable | consumo acumulado, perfil | cambio de costo marginal esperado |
| BILL-004 | Línea de factura no reconciliada | líneas, fórmula, total | revisión documental |
| BILL-005 | Forecast con incertidumbre alta | cobertura, baseline, días restantes | forecast degradado o bloqueado |
| CONS-001 | Ventana de alta importación | importación horaria, percentiles | franja crítica de compra |
| CONS-002 | Agotamiento temprano de batería | SOC, descarga, importación posterior | cadena causal compatible |
| CONS-003 | Carga desplazable candidata | carga, FV, batería, catálogo | oportunidad a evaluar |
| CONS-004 | Consumo base nocturno elevado | carga nocturna, baseline | oportunidad de auditoría |
| CONS-005 | Cambio de hábito | perfil reciente vs histórico | desviación de consumo |
| LOAD-001 | Ventana solar recomendada | forecast FV, carga, SOC, duración | recomendación candidata |
| LOAD-002 | Reserva de batería comprometida | escenario, reserva, incertidumbre | recomendación bloqueada |
| LOAD-003 | Riesgo de pico coincidente | equipos, arranque, límite | separar o bloquear cargas |
| LOAD-004 | Restricción humana incumplida | horario, supervisión, prioridad | recomendación bloqueada |
| LOAD-005 | Beneficio económico no positivo | baseline, escenario, tarifa | no recomendar por ahorro |
| SIM-001 | Delta de escenario | baseline, escenario, versiones | impacto energético/económico |
| SIM-002 | Escenario incompatible | perfiles, límites, modo operativo | escenario bloqueado |

## Dimensiones separadas

Todo resultado declara dimensiones independientes:

- `electrical_severity`;
- `data_quality`;
- `evidence_confidence`;
- `economic_impact`;
- `recommendation_confidence`.

Ejemplos:

- una factura alta puede tener impacto económico alto y severidad eléctrica nula;
- una caída PV puede tener severidad técnica alta y costo económico pequeño;
- una recomendación atractiva con datos incompletos debe tener confianza baja;
- un perfil vencido bloquea COP vigente aunque los kWh sean confiables.

## Contrato de regla

Cada regla declara:

- ID y versión;
- familia: técnica, calidad, económica, consumo, recomendación o simulación;
- pregunta técnica o económica;
- señales y entidades requeridas y opcionales;
- precondiciones de calidad;
- parámetros y fuente;
- algoritmo;
- evidencias producidas;
- dimensión de salida;
- severidad base o impacto, según familia;
- falsos positivos conocidos;
- casos válidos e inválidos;
- tests de regresión;
- fecha de caducidad cuando dependa de forecast o tarifa.

## Guardrails económicos

- `BILL-*` nunca acusa fraude o error de facturación automáticamente.
- `CONS-*` no identifica electrodomésticos sin evidencia por circuito o dispositivo.
- `LOAD-*` no modifica equipos ni configuración.
- `LOAD-*` debe aplicar reserva, límites, confort y supervisión.
- `SIM-*` conserva baseline inmutable.
- Toda cifra monetaria cita `tariff_profile_id` y vigencia.
- Toda recomendación expresa ahorro como intervalo y supuestos.
