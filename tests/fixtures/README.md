# Fixtures sintéticas

Este directorio contiene fixtures sintéticos reproducibles para tests y desarrollo.

**Ningún archivo aquí contiene datos reales.** Todos son generados por `_generate.py` con semilla RNG fija. Se permiten en el repositorio porque son sintéticos y pequeños.

Los archivos reales SolarMAN **nunca** deben commitearse aquí ni en cualquier otra ruta; `.gitignore` excluye los patrones `*Datos detallados*.csv` y `*Datos detallados*.xlsx`.

## Regenerar

```bash
uv run python tests/fixtures/_generate.py
```

## Contenido

- `flow_small.csv` — 5 filas × 12 columnas (formato flujo de planta).
- `telemetry_small.csv` — 3 filas × 120 columnas (formato telemetría técnica).
- `garbage.csv` — 10 filas × 5 columnas random (para tests negativos del detector).