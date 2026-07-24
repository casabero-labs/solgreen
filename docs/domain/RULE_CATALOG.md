# Catálogo inicial de reglas

Las reglas son determinísticas, versionadas y parametrizadas por perfil de planta.

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

## Estado de implementación

- Las cinco seed rules del catálogo (DATA-001, BAT-001, PV-001, GRID-003,
  INV-002) están explícitamente marcadas como `implementation_status=planned`.
- Ninguna tiene evaluador determinístico de producción.
- Su presencia en el código no implica ejecución: `evaluate_rule_catalog`
  produce 5 outcomes `not_evaluable` y 0 `RuleExecution` persistidos.
- Outcomes `not_evaluable` no se persisten como ejecuciones falsas ni se
  envían al LLM.
- Las reglas DATA-002 a DATA-005, BAT-002 a BAT-006, PV-002 a PV-005,
  GRID-001, GRID-002, GRID-004, GRID-005, INV-001, INV-003 a INV-005 y
  CORR-001 son definiciones de catálogo sin código activo.
- Evaluadores científicos reales, parámetros y evidencia estructurada
  pertenecen a U3 (#20).
- Los parámetros seed (umbrales, falsos positivos) son provisionales.
  Requieren perfil de planta confirmado y fuente técnica antes de activarse.
- #20 continúa abierto como epic de evaluadores U3.
