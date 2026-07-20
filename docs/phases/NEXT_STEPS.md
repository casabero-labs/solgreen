# Plan ejecutable — Solgreen

## Baseline estable

- Rama: `main`
- SHA de reconciliación R0: `1f70674f0a0d835c8933dc23f38f46f798a6facb`
- Auditoría: [`../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md`](../qa_reports/DEVELOPMENT_AUDIT_2026-07-20.md)

## Línea activa

- Rama: `develop/solgreen-unified`
- Epic: #26
- Pull request único: #27
- Política: un solo PR activo contra `main`
- Roadmap: [`UNIFIED_DEVELOPMENT_LINE.md`](UNIFIED_DEVELOPMENT_LINE.md)

El PR económico #8 fue cerrado como supersedido. Su fundación E0 fue absorbida en esta línea y no continúa como pista separada.

## Estado actual

### Verificado en main

- importación CSV/XLSX de ambos formatos SolarMAN;
- contratos de datos y catálogo de señales;
- calidad básica;
- timeline por tolerancia como prototipo;
- PostgreSQL inicial;
- API health básica;
- CI, privacidad y estado documental reconciliados.

### Verificado en la línea unificada

- dominio de inteligencia económica;
- ADR deterministic-first;
- diccionario de factura Afinia;
- workflows económicos;
- perfil histórico de ejemplo marcado como no vigente;
- test plan económico;
- arquitectura frontend Showcase Ink;
- aplicación React + D3 con datos demo;
- TypeScript strict;
- tests de componentes;
- build Vite;
- guarda automática Showcase Ink;
- CI Python, documentación y privacidad.

Evidencia: [`../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md`](../qa_reports/U0_FRONTEND_FOUNDATION_RESULTS_2026-07-20.md).

### Bloqueado o pendiente

- semántica correcta de cero y status;
- plausibilidad física avanzada;
- integración de energía;
- eventos científicos;
- evaluadores determinísticos;
- golden cases privados;
- endpoints de frontend;
- motor tarifario;
- IA validada;
- PDF y deploy verificable.

## Loop activo U0

### Goal

Entregar la fundación integrada y un frontend ejecutable, accesible y honesto sobre su estado.

### Checklist

- [x] R0 fusionado;
- [x] una rama unificada creada;
- [x] PR #8 cerrado como supersedido;
- [x] economía E0 absorbida;
- [x] epic único creado;
- [x] frontend React + TypeScript + D3 construido;
- [x] tokens Showcase Ink aplicados;
- [x] datos demo etiquetados;
- [x] COP vigente bloqueado;
- [x] importación web falsa evitada;
- [x] tabla alternativa para gráfica;
- [x] CI frontend en verde;
- [x] CI Python y documentación en verde sobre el PR;
- [x] evidencia QA documentada;
- [ ] revisión humana U0;
- [ ] cierre documental U0.

## Correcciones permitidas durante U0

Solo fallos objetivos de:

- TypeScript;
- tests frontend;
- build Vite;
- CI Python;
- enlaces o archivos documentales;
- accesibilidad básica;
- coherencia con Showcase Ink;
- contradicciones entre estado y código.

No iniciar todavía:

- carga web real;
- endpoints nuevos;
- motor de energía;
- reglas nuevas;
- cálculos de factura;
- llamadas LLM desde la UI;
- PDF;
- deploy.

## Siguiente loop U1

### Goal

Limpiar la semántica y calidad de los datos antes de producir métricas o conectar la UI.

### Entregables

- conservar `0.0` como medición válida;
- conservar estado textual en muestras merged;
- distinguir ausencia, cero, no aplicable y suprimido;
- lote vacío no obtiene score perfecto;
- huecos ponderados por duración;
- saltos SOC imposibles;
- temperaturas, frecuencia y voltajes plausibles;
- signos contradictorios;
- consistencia entre fuentes;
- parser ISO de tolerancia correcto (#24);
- formato global normalizado (#25).

### Stop conditions

- #21 resuelto;
- #24 resuelto;
- #25 resuelto;
- fixtures positivos y negativos pasan;
- documentación coincide;
- frontend puede confiar en el contrato de calidad sin excepciones ocultas.

## Después de U1

### U2 — Energía y métricas

- W→Wh/kWh por duración real;
- huecos explícitos;
- importación/exportación;
- batería;
- balance y residual;
- cobertura y confianza;
- perfiles horarios locales.

### U3 — Eventos y reglas

- segmentos separados de eventos;
- ventanas antes/durante/después;
- dropout FV;
- pérdida y retorno de red;
- descarga profunda y reinicios;
- evaluadores determinísticos (#20);
- evidencia estable;
- golden 17 y 19.

### U4 — Frontend conectado

- contratos API;
- importación con progreso real;
- timeline D3;
- filtros persistentes;
- episodios y evidencia;
- Playwright Human-First;
- estados parciales y errores accionables.

### U5 — Economía Afinia

- perfiles tarifarios;
- factura normalizada;
- motor tarifario;
- subsidio parametrizado;
- conciliación;
- P10/P50/P90;
- perfiles horarios;
- recomendaciones y escenarios.

### U6 — IA validada

- resolver #22;
- IDs de evidencia;
- exact coverage;
- rechazo de cifras y referencias nuevas;
- registro de proveedor, modelo y fallback;
- cero persistencia de respuestas inválidas.

### U7 — Reportes y operación

- PDF técnico;
- privacidad;
- deploy Coolify;
- polling;
- SHA del contenedor;
- health y smoke;
- rollback;
- evidencia operativa.

## Próximo paso exacto

Revisar visual y funcionalmente el frontend del PR #27. Con aprobación humana, cerrar U0 y continuar U1 dentro de la misma rama y el mismo PR, sin abrir otra línea de desarrollo.
