# Loop Registry — Solgreen

## Feedback disponible

- schemas de los dos datasets;
- datasets privados iniciales;
- episodios dorados del 17 y 19 de julio;
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
- cualquier futura capacidad de escritura.

## Loops

### L0 — Foundation freeze

**GOAL:** cerrar fundamentos, contratos y alcance.  
**FEEDBACK:** revisión documental.  
**STOP:** cero contradicciones abiertas críticas.

### L1 — Importación reproducible

**GOAL:** reconocer y parsear ambos formatos.  
**FEEDBACK:** filas, columnas, hash, timestamps y tests.  
**STOP:** imports idempotentes y sin pérdida.

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
