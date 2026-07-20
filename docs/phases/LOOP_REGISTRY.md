# Loop Registry — Solgreen

## Feedback disponible

- schemas de los dos datasets;
- datasets privados iniciales;
- episodios dorados del 17 y 19 de julio;
- recibos históricos privados redactados;
- cálculos históricos revisados de energía y factura;
- pruebas unitarias y de integración;
- validación visual;
- revisión humana del propietario;
- diagnóstico posterior del instalador.

## Human gates

- perfil de planta;
- umbrales de fabricante;
- clasificación de severidad crítica;
- confirmación de causa;
- sharing de reportes;
- cualquier futura capacidad de escritura;
- perfil tarifario vigente;
- revisión de extracción de factura;
- periodo de facturación;
- restricciones de confort y horarios;
- aceptación de recomendaciones;
- habilitación futura de AGPE como perfil separado.

## Regla de orden

La pista técnica L0-L10 mantiene su orden y autoridad. La pista económica E0-E5 es paralela, pero declara dependencias explícitas. Ningún loop económico puede saltarse calidad, timeline o métricas necesarias.

## Loops técnicos

### L0 — Foundation freeze

**GOAL:** cerrar fundamentos, contratos y alcance.  
**FEEDBACK:** revisión documental.  
**STOP:** cero contradicciones abiertas críticas.

### L1 — Importación reproducible

**GOAL:** reconocer y parsear ambos formatos.  
**FEEDBACK:** filas, columnas, hash, timestamps y tests.  
**STOP:** imports idempotentes y sin pérdida.

**STATUS:** cerrado el 2026-07-20.

### L2 — Calidad de datos

**GOAL:** huecos, duplicados, invalidez y score.  
**STOP:** golden cases detectados.

### L3 — Timeline canónico

**GOAL:** sincronizar datasets con lineage.  
**STOP:** cada valor rastreable.

### L4 — Métricas físicas

**GOAL:** balances, energía y métricas base.  
**STOP:** fórmulas verificadas con fixtures.

### L5 — Catálogo de reglas v0.1

**GOAL:** implementar reglas críticas.  
**STOP:** golden events reproducibles.

### L6 — Episodios

**GOAL:** agrupar eventos y ventanas contextuales.  
**STOP:** 17 y 19 de julio correctamente reconstruidos.

### L7 — Visualización D3

**GOAL:** explorador científico.  
**STOP:** flujos UX y accesibilidad aprobados.

### L8 — IA validada

**GOAL:** MiniMax/DeepSeek con schema y evidence refs.  
**STOP:** cero respuestas inválidas aceptadas.

### L9 — Reportes

**GOAL:** PDF técnico reproducible.  
**STOP:** instalador puede auditar todo hallazgo.

### L10 — Operación

**GOAL:** deploy, observabilidad, backups y seguridad.  
**STOP:** health 200, restore probado y runbooks listos.

## Loops económicos paralelos

### E0 — Fundación económica

**GOAL:** cerrar alcance, autoridad, contratos, privacidad, workflows, ADR y test plan.  
**DEPENDENCIES:** L0 y resultados históricos privados revisados.  
**FEEDBACK:** revisión documental y ausencia de contradicciones con L1-L10.  
**STOP:** la pista económica está definida sin cambiar código productivo ni alterar el próximo loop L2.

Entregables:

- `docs/domain/ECONOMIC_INTELLIGENCE.md`;
- diccionario de facturación;
- workflows;
- ADR deterministic-first;
- golden test plan;
- perfil histórico de ejemplo no vigente.

### E1 — Contratos tarifarios y facturas

**GOAL:** implementar `TariffProfile`, `BillingCycle`, `InvoiceDocument`, `InvoiceLine` y validadores.  
**DEPENDENCIES:** E0.  
**FEEDBACK:** fixtures sintéticos y perfiles válidos/inválidos.  
**STOP:** perfiles sin fuente o vencidos son rechazados como vigentes; montos usan centavos enteros; parser manual/API no expone PII.

No requiere modificar parsers SolarMAN.

### E2 — Motor de factura, conciliación y forecast

**GOAL:** reproducir facturas históricas y proyectar ciclos con incertidumbre.  
**DEPENDENCIES:** E1 + L2 + L3 + integración de energía de L4.  
**FEEDBACK:** golden cases privados, traza de cálculo y cobertura.  
**STOP:** dos recibos históricos se reproducen dentro de tolerancia; forecast reporta P10/P50/P90; perfil vencido no se usa como vigente.

### E3 — Perfiles horarios y ventanas críticas

**GOAL:** calcular consumo, FV, red, batería y SOC por hora local.  
**DEPENDENCIES:** L2 + L3 + L4.  
**FEEDBACK:** dataset privado histórico y fixtures sintéticos.  
**STOP:** integración por hora es reproducible, cobertura visible y ventana nocturna golden correctamente caracterizada.

Puede avanzar en paralelo con E2 una vez cerradas sus dependencias.

### E4 — Recomendaciones de cargas

**GOAL:** generar ventanas conservadoras con restricciones y deltas.  
**DEPENDENCIES:** E3 + perfil de planta confirmado + catálogo de cargas.  
**FEEDBACK:** escenarios sintéticos y revisión humana.  
**STOP:** ninguna recomendación viola reserva, potencia, supervisión o confort; todo ahorro aparece como intervalo; no se afirma identidad sin evidencia.

### E5 — Simulador e interpretación económica IA

**GOAL:** comparar escenarios inmutables y explicar resultados con IA validada.  
**DEPENDENCIES:** E2 + E3 + E4 + L8.  
**FEEDBACK:** golden scenarios, validadores de cifras y evidence refs.  
**STOP:** baseline inmutable; delta reproducible; cero cifras o referencias inventadas; funciona sin proveedor IA.

## Dependencias resumidas

```text
L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8 → L9 → L10
       │         │     │                   │
       │         │     ├────────────┐      │
       │         │                  │      │
       └→ E0 → E1 → E2 ←────────────┘      │
                  └→ E3 ← L3/L4            │
                       └→ E4                │
                            └→ E5 ←─────────┘
```

## Límite de iteraciones

- máximo tres iteraciones automáticas por loop ante el mismo fallo;
- una contradicción de dominio o tarifa bloquea el loop;
- falta de datos privados produce fixture sintético y bloqueo documentado, no una suposición;
- cualquier propuesta de control automático abre un proyecto y ADR separados.
