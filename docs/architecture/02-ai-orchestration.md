# Orquestación de IA

## Pipeline

```text
Episode envelope
 → redaction
 → provider adapter
 → JSON response
 → schema validation
 → evidence validation
 → semantic consistency checks
 → optional second opinion
 → consolidated interpretation
```

## Adaptadores

Todos implementan:

- `analyze_episode()`;
- `explain_for_owner()`;
- `draft_installer_report()`;
- `healthcheck()`;
- costes y latencia normalizados.

## Resiliencia

- timeout;
- retry limitado;
- circuit breaker;
- fallback;
- cache por input hash;
- presupuesto por análisis;
- no bloquear análisis determinístico si IA falla.
