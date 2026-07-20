# Diccionario SolarMAN — Flujo de planta

Formato inicial observado: 12 columnas, muestreo nominal de cinco minutos.

| # | Columna original | Nombre canónico propuesto | Unidad | Observación |
|---:|---|---|---|---|
| 1 | `Nombre de planta` | `nombre_de_planta` | texto/fecha | Fuente SolarMAN; semántica final definida por parser. |
| 2 | `Hora actualizada` | `hora_actualizada` | texto/fecha | Fuente SolarMAN; semántica final definida por parser. |
| 3 | `Zona horaria` | `zona_horaria` | texto/fecha | Fuente SolarMAN; semántica final definida por parser. |
| 4 | `Potencia de producción(W)` | `potencia_de_produccion` | W | Fuente SolarMAN; semántica final definida por parser. |
| 5 | `Potencia de consumo(W)` | `potencia_de_consumo` | W | Fuente SolarMAN; semántica final definida por parser. |
| 6 | `Energía de la red(W)` | `energia_de_la_red` | W | Fuente SolarMAN; semántica final definida por parser. |
| 7 | `Poder adquisitivo(W)` | `poder_adquisitivo` | W | Fuente SolarMAN; semántica final definida por parser. |
| 8 | `Potencia de alimentación(W)` | `potencia_de_alimentacion` | W | Fuente SolarMAN; semántica final definida por parser. |
| 9 | `Potencia de la batería(W)` | `potencia_de_la_bateria` | W | Fuente SolarMAN; semántica final definida por parser. |
| 10 | `Potencia de carga(W)` | `potencia_de_carga` | W | Fuente SolarMAN; semántica final definida por parser. |
| 11 | `Poder de descarga(W)` | `poder_de_descarga` | W | Fuente SolarMAN; semántica final definida por parser. |
| 12 | `SoC(%)` | `soc` | % | Fuente SolarMAN; semántica final definida por parser. |

## Regla de signos inicial observada

La columna `Energía de la red(W)` puede usar signo negativo para compra y positivo para posible entrega, pero esta semántica debe confirmarse por balance y perfil del importador. Las columnas `Poder adquisitivo` y `Potencia de alimentación` no se consideran autoridad automática porque se observaron inconsistencias.
