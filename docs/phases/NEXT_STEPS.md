# Plan ejecutable

## Fase 0 — Freeze documental

- revisar Idea Brief;
- confirmar perfil real de planta;
- confirmar límites de batería y red;
- cerrar schemas;
- registrar ADRs.

## Fase 1 — Importer core

Entregables:

- detector de formato;
- parser XLSX flujo de planta;
- parser CSV telemetría;
- hash y metadata;
- pruebas con fixtures sintéticos;
- reporte de importación.

## Fase 2 — Data quality

- huecos;
- duplicados;
- saltos SOC;
- temperaturas inválidas;
- signos contradictorios;
- score y UI.

## Fase 3 — Timeline

- modelo canónico;
- join por tolerancia;
- lineage;
- API temporal;
- downsampling.

## Fase 4 — Análisis determinístico

- balance;
- batería;
- PV/MPPT;
- red;
- estados;
- reglas v0.1.

## Fase 5 — Episodios y D3

- agrupador;
- timeline;
- visor contextual;
- heatmaps;
- comparadores.

## Fase 6 — IA

- adapters;
- prompts versionados;
- schemas;
- validadores;
- consenso para severidad alta.

## Fase 7 — Reportes

- plantillas;
- generación PDF;
- redacción de secretos;
- anexos.

## Fase 8 — Producción

- Butterbase/PostgreSQL;
- Coolify;
- Infisical;
- observabilidad;
- backup/restore;
- hardening.

## Próximo prompt ejecutable

Implementar únicamente L1: importación reproducible, sin UI avanzada, reglas ni IA.
