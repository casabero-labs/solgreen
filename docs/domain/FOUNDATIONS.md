# Fundamentos del dominio

## 1. Jerarquía epistemológica

Solgreen diferencia cinco niveles:

1. **Medido:** valor presente en la fuente.
2. **Normalizado:** valor convertido sin alterar significado.
3. **Calculado:** derivado mediante fórmula explícita.
4. **Inferido:** conclusión compatible con varios hechos.
5. **Confirmado:** diagnóstico aceptado por humano autorizado con evidencia adicional.

La interfaz y los reportes deben mostrar el nivel.

## 2. Tiempo

- Se conserva el timestamp original y la zona horaria original.
- Se normaliza internamente a UTC.
- Las visualizaciones pueden mostrar `America/Bogota`.
- La tolerancia de unión entre datasets es configurable.
- Un muestreo de cinco minutos representa un punto observado, no un promedio garantizado.

## 3. Potencia y energía

- Potencia se expresa en W o kW.
- Energía se expresa en Wh o kWh.
- No se estima energía mediante suma simple; se integra usando duración entre muestras y reglas para huecos.
- El balance instantáneo puede no cerrar por desincronización.
- El balance por ventana es más confiable cuando la cobertura es suficiente.

## 4. Convenciones de signos

Cada parser declara su convención. El modelo canónico usa:

- `grid_import_w ≥ 0`;
- `grid_export_w ≥ 0`;
- `battery_charge_w ≥ 0`;
- `battery_discharge_w ≥ 0`.

No se conserva ambigüedad de signo en las métricas canónicas.

## 5. Ausencia frente a cero

- `null`: no medido, ausente o inválido.
- `0`: medición válida de cero.
- `not_applicable`: señal no soportada.
- `suppressed`: dato oculto por política.

## 6. Calidad de datos

La confianza de cualquier episodio está limitada por:

- cobertura temporal;
- consistencia entre fuentes;
- plausibilidad física;
- precisión del timestamp;
- estabilidad del parser;
- disponibilidad de señales críticas.

## 7. Episodios

Un episodio agrupa uno o más eventos cercanos que comparten señales, causalidad plausible o transición operativa. Debe incluir ventana previa y posterior.

## 8. Severidad

La severidad expresa impacto potencial, no certeza de causa. Se calcula mediante reglas y perfil de planta.

## 9. IA

El LLM recibe hechos seleccionados y referencias. No recibe autoridad para crear mediciones, reglas o códigos de alarma.

## 10. Seguridad operativa

Solgreen informa y documenta. No sustituye protección eléctrica, manual del fabricante ni técnico certificado.
