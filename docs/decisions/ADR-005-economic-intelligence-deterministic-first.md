# ADR-005 — Inteligencia económica deterministic-first

## Estado

Propuesto para aceptación mediante el PR de fundación económica.

## Contexto

Solgreen incorporará cálculo de factura, proyección de consumo, análisis horario, recomendaciones de cargas y simulaciones. Estas funciones pueden afectar decisiones de gasto, operación doméstica y reserva de batería.

Un LLM puede explicar patrones y relacionar evidencia, pero no ofrece reproducibilidad numérica, estabilidad de redondeo ni garantía de respetar tarifas, vigencias y restricciones físicas.

Además:

- la tarifa cambia por periodo y segmento;
- SolarMAN no es el medidor fiscal;
- los datos de cinco minutos pueden contener huecos y desincronización;
- una recomendación de horario depende de restricciones humanas y técnicas;
- los cálculos históricos deben poder repetirse con la misma versión.

## Decisión

La inteligencia económica seguirá esta separación:

```text
Motores determinísticos
  ├── integración de potencia a energía
  ├── motor tarifario
  ├── conciliación
  ├── perfiles horarios
  ├── optimización restringida
  └── simulador
          ↓ resultados estructurados
LLM intercambiable
  ├── explicación
  ├── priorización narrativa
  ├── comparación de hipótesis
  └── redacción de recomendaciones
          ↓ schema + validadores
Decisión humana
```

El LLM no ejecuta fórmulas económicas ni modifica sus resultados.

## Contratos obligatorios

Todo resultado monetario debe incluir:

- `analysis_run_id`;
- `tariff_profile_id` y versión;
- inputs con checksum;
- periodo;
- energía utilizada;
- fórmula y redondeos;
- cobertura;
- supuestos;
- intervalo de incertidumbre cuando sea proyección.

Toda recomendación debe incluir:

- baseline;
- escenario sugerido;
- delta calculado;
- restricciones aplicadas;
- evidencia;
- confianza;
- caducidad.

Toda interpretación IA debe incluir referencias a resultados existentes y ser rechazada si cambia cifras o inventa identificadores.

## Límites de responsabilidad

- La factura oficial prevalece sobre la estimación.
- El medidor fiscal prevalece sobre SolarMAN para energía facturable.
- Un perfil vencido no se presenta como vigente.
- Un ahorro es estimado, nunca garantizado.
- Una curva agregada no identifica un electrodoméstico con certeza.
- El sistema no controla el inversor ni electrodomésticos en el MVP.

## Alternativas rechazadas

### LLM calcula directamente la factura

Rechazada por falta de reproducibilidad, riesgo de alucinación y redondeo inconsistente.

### Reglas tarifarias hardcodeadas

Rechazada porque CU, subsidios, cargos, territorio y vigencia cambian.

### Un único score que mezcle riesgo eléctrico y ahorro

Rechazada porque severidad técnica, calidad del dato y oportunidad económica son dimensiones distintas.

### Recomendaciones basadas solo en excedente solar instantáneo

Rechazada porque ignora reserva nocturna, potencia de arranque, duración, confort y variabilidad.

## Consecuencias positivas

- resultados auditables;
- pruebas golden estables;
- proveedor IA reemplazable;
- funcionamiento sin IA;
- separación entre riesgo técnico y economía;
- evolución incremental sin tocar el importador L1.

## Consecuencias negativas

- más contratos y versionado;
- requiere perfiles tarifarios mantenidos;
- necesita L2-L4 antes de recomendaciones confiables;
- las recomendaciones iniciales serán conservadoras;
- reconciliación perfecta no siempre será posible.

## Revalidación

Revisar este ADR cuando:

- se incorpore lectura automática del medidor fiscal;
- se habilite AGPE;
- existan medidores por circuito;
- se plantee control automático;
- cambie la estructura tarifaria;
- se añada optimización probabilística avanzada.
