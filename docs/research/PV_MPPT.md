# Análisis PV y MPPT

## Señales

PV1/PV2 voltaje, corriente y potencia; potencia total; estado del inversor; batería; carga; temperatura y red.

## Patrones

- nube: caída no necesariamente simultánea a cero y con continuidad de extracción;
- dropout: potencia a cero con voltaje DC presente;
- desconexión física: posible caída también de voltaje;
- asimetría: diferencia persistente entre MPPT comparables;
- clipping: meseta cerca del límite;
- curtailment: potencia limitada por SOC, exportación o configuración;
- recuperación de protección: retorno abrupto tras intervalo anómalo.

La clasificación final siempre muestra hipótesis alternativas.
