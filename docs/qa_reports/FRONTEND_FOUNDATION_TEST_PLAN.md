# Test Plan — Frontend unificado Showcase Ink

## 1. Objetivo

Verificar que el frontend de Solgreen sea funcional, accesible, científicamente honesto y coherente con Casabero Ink.

U0 valida la fundación. Los flujos críticos se amplían progresivamente y no se consideran cerrados hasta superar Human-First UX Gate.

## 2. Fuentes normativas

- `casabero-labs/estandar-casabero/SKILL.md`;
- `standards/frontend/DESIGN_SYSTEM_INK.md`;
- `examples/frontend/showcase-ink.html`;
- `standards/frontend/UX_UI_MANIFESTO.md`;
- `standards/frontend/HUMAN_FIRST_UX.md`.

## 3. Unitarias y componentes

### UI-001 — Etiqueta de demostración

La vista inicial debe informar de manera persistente que los datos son demostrativos y no corresponden a una planta ni factura real.

### UI-002 — Cambio de periodo

Al seleccionar 24h, 7d o 30d:

- cambia la serie;
- cambian los indicadores;
- se conserva la vista activa;
- el control comunica `aria-pressed`.

### UI-003 — Bloqueo monetario

Al abrir Economía sin perfil vigente:

- no aparece un total COP actual;
- aparece texto específico del bloqueo;
- la causa y el próximo requisito son comprensibles.

### UI-004 — Modo oscuro

El toggle modifica el tema global, conserva accesibilidad y actualiza su nombre accesible.

### UI-005 — Gráfica y tabla

La serie D3 debe tener:

- título y descripción;
- leyenda textual;
- líneas distinguibles por trazo y grosor;
- tabla alternativa con los mismos datos;
- unidades y periodo visibles.

### UI-006 — Acción no disponible

La importación web no debe fingir funcionalidad. El botón deshabilitado explica el bloqueo y la fase que la habilitará.

## 4. Validación visual Ink

Checklist:

- solo cinco tokens cromáticos Ink;
- Inter y JetBrains Mono, sin tercera familia;
- sin Playfair o serif;
- sin gradientes decorativos;
- sin accent, danger o success;
- sin estados dependientes solo de color;
- botones sólidos `ink-800`;
- ring shadows coherentes;
- dos radios predominantes por vista;
- modo oscuro global;
- `prefers-reduced-motion`.

## 5. Accesibilidad

- skip link funcional;
- navegación por teclado;
- foco visible;
- estructura de headings sin saltos arbitrarios;
- landmarks `header`, `nav`, `main`, `footer`;
- tabla con caption y headers;
- iconos decorativos ocultos al lector cuando corresponda;
- botones con nombre accesible;
- estado no comunicado solo por color;
- responsive a 320 px sin pérdida del flujo.

## 6. Integración futura

### U4 — Importación web

E2E obligatorio:

```text
abrir → seleccionar archivo fixture → ver validación → iniciar → ver progreso
→ recibir resultado o error accionable → conservar el estado → terminar
```

### U4 — Timeline

- filtrar periodo;
- alternar señales;
- abrir tabla alternativa;
- seleccionar un evento;
- conservar filtros;
- ver procedencia y cobertura.

### U5 — Factura

- cargar recibo fixture;
- revisar campos extraídos;
- corregir valores;
- seleccionar perfil;
- conciliar;
- bloquear perfil vencido;
- no mostrar total vigente sin autoridad.

### U5 — Escenario

- seleccionar baseline;
- modificar horario o carga;
- validar restricciones;
- comparar delta;
- conservar supuestos y versión;
- no modificar datos originales.

### U7 — Informe

- seleccionar alcance;
- revisar redacción;
- aplicar política de privacidad;
- generar PDF;
- verificar descarga y metadata.

## 7. Performance

Objetivos iniciales:

- interacción de filtros sin bloqueo perceptible;
- carga inicial razonable en red doméstica;
- D3 no controla el DOM completo;
- downsampling para series grandes;
- tablas virtualizadas solo cuando la evidencia de volumen lo requiera;
- operaciones superiores a 800 ms con progreso visible.

## 8. Seguridad y privacidad

- no incrustar secretos en el bundle;
- no registrar datasets privados en consola;
- no enviar archivos o montos a analítica de terceros;
- sanitizar contenido textual proveniente de archivos;
- CSP y headers antes del deploy público;
- errores no revelan DSN, rutas privadas o claves.

## 9. Evidencia U0

Comandos esperados:

```bash
cd apps/web
npm install --no-audit --no-fund
npm run typecheck
npm run test
npm run build
```

Resultados deben quedar en CI. U0 permanece abierto si falla cualquiera de los tres.

## 10. Stop condition U0

- tests de comportamiento pasan;
- TypeScript strict pasa;
- Vite build pasa;
- documentación y frontend describen el mismo alcance;
- datos demo no pueden confundirse con producción;
- economía no muestra cifra vigente sin perfil;
- una sola rama y PR activos para desarrollo de producto.
