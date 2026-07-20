# Arquitectura de visualización

## Principios

- D3.js para escalas, ejes, interacción y geometrías;
- cálculo analítico fuera del componente visual;
- Web Workers para downsampling y transformaciones pesadas;
- datos medidos, calculados, interpolados e inferidos con lenguajes visuales distintos;
- zoom, brush, crosshair y selección sincronizada.

## Visualizaciones MVP

1. Timeline multicapa.
2. Visor antes/durante/después.
3. Mapa de calor día × hora.
4. Comparador PV1/PV2.
5. SOC-potencia-voltaje de batería.
6. Calidad de red L1/L2.
7. Residual de balance.
8. Matriz de episodios.

## Contrato de gráfica

Cada gráfica documenta:

- pregunta;
- señales;
- transformación;
- agregación;
- unidades;
- dominio temporal;
- manejo de huecos;
- limitaciones;
- test visual.
