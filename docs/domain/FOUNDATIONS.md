# Fundamentos del dominio

## 1. Jerarquía epistemológica

Solgreen diferencia cinco niveles:

1. **Medido:** valor presente en la fuente.
2. **Normalizado:** valor convertido sin alterar significado.
3. **Calculado:** derivado mediante fórmula explícita.
4. **Inferido:** conclusión compatible con varios hechos.
5. **Confirmado:** diagnóstico aceptado por humano autorizado con evidencia adicional.

La interfaz y los reportes deben mostrar el nivel.

En economía se añade una distinción ortogonal:

- **oficial:** presente en factura o medidor fiscal;
- **estimado:** calculado por Solgreen;
- **proyectado:** estimado para un periodo todavía abierto;
- **conciliado:** comparado contra una fuente oficial.

`Oficial` no significa que una interpretación causal esté confirmada; solo identifica la autoridad documental del valor.

## 2. Tiempo

- Se conserva el timestamp original y la zona horaria original.
- Se normaliza internamente a UTC.
- Las visualizaciones pueden mostrar `America/Bogota`.
- La tolerancia de unión entre datasets es configurable.
- Un muestreo de cinco minutos representa un punto observado, no un promedio garantizado.
- Los ciclos de facturación usan inicio inclusivo y fin exclusivo.
- Los perfiles horarios se agregan por hora local, no por UTC.

## 3. Potencia y energía

- Potencia se expresa en W o kW.
- Energía se expresa en Wh o kWh.
- No se estima energía mediante suma simple; se integra usando duración entre muestras y reglas para huecos.
- El balance instantáneo puede no cerrar por desincronización.
- El balance por ventana es más confiable cuando la cobertura es suficiente.
- Una factura consume energía integrada o energía oficial en kWh, nunca una suma de W.
- La integración declara método, cobertura, tolerancia de huecos y versión.

## 4. Convenciones de signos

Cada parser declara su convención. El modelo canónico usa:

- `grid_import_w ≥ 0`;
- `grid_export_w ≥ 0`;
- `battery_charge_w ≥ 0`;
- `battery_discharge_w ≥ 0`.

No se conserva ambigüedad de signo en las métricas canónicas.

Una convención de signo no confirmada bloquea la conciliación económica como resultado confiable.

## 5. Ausencia frente a cero

- `null`: no medido, ausente o inválido.
- `0`: medición válida de cero.
- `not_applicable`: señal no soportada.
- `suppressed`: dato oculto por política.

En facturación:

- monto ausente no equivale a cero;
- cargo no aplicable no equivale a cargo de cero;
- una línea no reconocida se conserva y requiere revisión.

## 6. Calidad de datos

La confianza de cualquier episodio, métrica o proyección está limitada por:

- cobertura temporal;
- consistencia entre fuentes;
- plausibilidad física;
- precisión del timestamp;
- estabilidad del parser;
- disponibilidad de señales críticas;
- coincidencia del ciclo;
- vigencia de perfiles;
- diferencia entre SolarMAN y medidor fiscal;
- estabilidad del baseline.

La app puede producir kWh con advertencia y bloquear COP si falta autoridad tarifaria vigente.

## 7. Episodios

Un episodio agrupa uno o más eventos cercanos que comparten señales, causalidad plausible o transición operativa. Debe incluir ventana previa y posterior.

Las oportunidades económicas no se mezclan dentro de la severidad del episodio. Pueden enlazarse como impacto secundario.

## 8. Severidad y otras dimensiones

La severidad expresa impacto eléctrico potencial, no certeza de causa. Se calcula mediante reglas y perfil de planta.

Solgreen mantiene separadas:

- severidad eléctrica;
- calidad de datos;
- confianza de evidencia;
- impacto económico;
- confianza de recomendación.

No existe un score universal que mezcle estas dimensiones.

## 9. Facturación

- La factura oficial prevalece para el total facturado.
- El medidor fiscal prevalece para energía facturable cuando está disponible.
- SolarMAN sirve para estimación y explicación, no reemplaza el contador fiscal.
- CU, subsidio, límites y cargos pertenecen a perfiles versionados con fuente y vigencia.
- Valores históricos son fixtures, no autoridad vigente.
- COP se persiste como centavos enteros.
- Redondeos se aplican según política explícita.
- Una discrepancia genera conciliación y revisión, no acusación automática.

## 10. Perfiles horarios

- Se prioriza energía por ventana sobre fotografías instantáneas.
- Cada agregado declara cobertura y número de días.
- Potencia y energía se visualizan separadamente.
- La hora donde se compra energía puede ser consecuencia de cargas ocurridas antes.
- Una cadena causal temporal se presenta como compatible, no confirmada, salvo evidencia adicional.

## 11. Recomendaciones y escenarios

- Una recomendación es una propuesta con vigencia, no una instrucción automática.
- Toda recomendación compara baseline y escenario.
- Debe respetar reserva, potencia, duración, supervisión, confort y prioridad.
- Ahorro y SOC se expresan como intervalos cuando hay incertidumbre.
- La curva agregada no identifica un electrodoméstico con certeza.
- Un escenario no modifica muestras, baseline ni configuración.
- Escenarios futuros AGPE usan perfiles separados.

## 12. IA

El LLM recibe hechos seleccionados y referencias. No recibe autoridad para crear mediciones, reglas, códigos de alarma, tarifas, facturas, ahorros ni horarios óptimos.

Puede explicar y comparar resultados determinísticos. Toda cifra debe existir en el envelope y toda referencia debe resolver a evidencia real.

## 13. Seguridad operativa

Solgreen informa y documenta. No sustituye protección eléctrica, manual del fabricante, técnico certificado, factura oficial ni asesoría regulatoria.

No controla el inversor ni electrodomésticos en el MVP. Facturas y hábitos horarios son datos privados y se redactan antes de compartir o enviar a proveedores IA.
