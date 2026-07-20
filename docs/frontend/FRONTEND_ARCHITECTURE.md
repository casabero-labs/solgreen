# Arquitectura de frontend — Solgreen

## 1. Decisión visual

Solgreen es una herramienta técnica y analítica. Su interfaz adopta **Casabero Ink** como única variante visual.

Fuentes normativas:

1. `casabero-labs/estandar-casabero/SKILL.md`;
2. `standards/frontend/DESIGN_SYSTEM_INK.md`;
3. `examples/frontend/showcase-ink.html`;
4. `standards/frontend/UX_UI_MANIFESTO.md`;
5. `standards/frontend/HUMAN_FIRST_UX.md`.

No se crea un estilo Solgreen independiente. La identidad se construye mediante composición, densidad y contenido del dominio dentro de los catálogos Ink existentes.

## 2. Catálogos usados

| Superficie | Catálogo | Razón |
|---|---|---|
| Dashboard, timeline, calidad y episodios | Ink Console | Alta densidad, datos técnicos y navegación profesional |
| Importación, filtros, factura y simulador | Ink Form | Labels visibles, prevención de errores y feedback cercano |
| Reportes y explicación técnica | Ink Editorial | Lectura prolongada y jerarquía documental |

Los catálogos comparten tokens. No se mezclan con Warm y no constituyen temas separados.

## 3. Stack

```text
React + TypeScript + Vite
        ↓
componentes y flujos de producto
        ↓
D3 modular para escalas, geometría y cálculos visuales
        ↓
REST/SSE FastAPI
        ↓
servicios determinísticos de Solgreen
```

React gobierna estado, accesibilidad y composición. D3 no controla el DOM completo: calcula escalas y paths que React renderiza. Esto evita una segunda arquitectura de estado dentro de la gráfica.

## 4. Estructura inicial

```text
apps/web/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── components/
    │   └── EnergyChart.tsx
    ├── data/
    │   └── demo.ts
    ├── styles/
    │   ├── tokens.css
    │   └── app.css
    └── test/
        └── setup.ts
```

La estructura crecerá por capacidades y flujos, no por una biblioteca indiscriminada de componentes:

```text
features/
├── imports/
├── plant-overview/
├── data-quality/
├── timeline/
├── episodes/
├── economics/
├── scenarios/
└── reports/
```

## 5. Tokens y prohibiciones

La paleta se limita a:

- `ink-800`;
- `ink-500`;
- `ink-200`;
- `paper-100`;
- `paper-000`.

Reglas:

- Inter para toda la UI;
- JetBrains Mono para cifras, timestamps, IDs y hashes;
- sin serif;
- sin acentos cromáticos;
- sin gradientes decorativos;
- sin glass o blur decorativo;
- máximo dos radios predominantes por vista;
- botones sólidos en `ink-800`;
- estados comunicados con icono, forma, peso y texto;
- soporte de modo oscuro global;
- `prefers-reduced-motion` obligatorio.

## 6. Visualización científica

Toda gráfica debe declarar:

- pregunta que responde;
- unidad y tipo de medida;
- periodo y zona horaria;
- cobertura;
- procedencia;
- huecos o incertidumbre;
- tabla alternativa accesible.

Potencia y energía no comparten eje sin separación explícita. Datos medidos, normalizados, calculados, proyectados e inferidos deben distinguirse mediante texto y estructura, no únicamente mediante color.

## 7. Estado de datos

La UI reconoce cinco niveles epistemológicos:

```text
original → medido → normalizado → calculado → inferido
```

Una cifra monetaria vigente se bloquea si no existe perfil tarifario verificado y aplicable. Un resultado de demo siempre lleva una señal visible persistente.

## 8. Arquitectura de estado

U0 mantiene estado local de demostración. Antes de conectar la API se introducirán contratos explícitos para:

- estado de consulta;
- progreso de importación;
- errores accionables;
- filtros persistentes;
- paginación o ventanas temporales;
- selección de episodio;
- versión de análisis;
- procedencia y confianza.

No se añadirá una librería global de estado hasta demostrar una necesidad transversal real.

## 9. Accesibilidad

Mínimos:

- navegación completa por teclado;
- foco visible Ink;
- landmarks y encabezados semánticos;
- texto alternativo o tabla para gráficas;
- tamaño táctil mínimo de 44 px en acciones móviles críticas;
- estados con al menos dos señales no cromáticas;
- contraste AA;
- reducción de movimiento;
- mensajes humanos para carga, error, bloqueo y éxito.

## 10. Human-first gate

Los flujos críticos requieren Playwright o evidencia equivalente:

```text
abrir → entender → completar → ejecutar → ver feedback → terminar
```

U0 no simula una carga de archivos falsa. La acción aparece bloqueada y explica la dependencia pendiente. La importación web se habilitará en U4 cuando exista contrato API, progreso real, persistencia y E2E.

## 11. Telemetría de producto

Se diseñarán eventos sin información sensible para conocer:

- flujo iniciado y completado;
- filtro aplicado;
- episodio abierto;
- gráfica o tabla consultada;
- recomendación aceptada o descartada;
- escenario comparado;
- error recuperable;
- abandono de un flujo.

No se enviarán montos, dirección, NIC, serial, factura ni valores técnicos privados a analítica de terceros.

## 12. Criterio de cierre U0

- frontend ejecutable;
- navegación y periodo funcionales;
- modo oscuro funcional;
- D3 con tabla alternativa;
- economía integrada documentalmente;
- datos demo claramente marcados;
- pruebas de comportamiento básicas;
- build y tests frontend en CI;
- roadmap unificado y un solo PR activo.
