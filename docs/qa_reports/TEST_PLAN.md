# Plan de pruebas

## Unitarias

- parsing de cada columna prioritaria;
- timezone;
- signos;
- integración de energía;
- residual;
- cada regla;
- severidad y confianza;
- validador IA.

## Integración

- archivo → lote → muestras;
- lote → timeline;
- timeline → reglas → episodio;
- episodio → IA → validación;
- episodio → reporte.

## Golden tests

- dropout FV del 17;
- red inestable del 17;
- descarga profunda del 19;
- tormenta de inicializaciones;
- sobrevoltaje L2;
- carga de batería elevada;
- exportación transitoria;
- hueco del 16;
- salto SOC;
- balance imposible.

## Seguridad

- aislamiento por planta;
- RLS;
- URLs firmadas;
- secreto no aparece en logs;
- serial redaccionado;
- prompt injection en archivos y notas;
- rechazo de archivos maliciosos.

## UX

- importación completa por teclado;
- lectura de episodio sin depender de color;
- huecos visibles;
- estados parciales y errores;
- tabla alternativa para cada gráfica crítica.

## Performance

- 120 columnas × meses de muestras;
- downsampling;
- análisis asíncrono;
- memoria del worker;
- generación de PDF.

## Evidencia

Cada ejecución se documenta en `docs/qa_reports/` con fecha, SHA, comandos y resultados.
