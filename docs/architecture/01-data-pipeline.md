# Pipeline de datos

```text
Upload
 → hash + metadata
 → storage privado
 → detección de formato
 → parser versionado
 → staging
 → validación
 → tablas canónicas
 → métricas
 → reglas
 → episodios
 → interpretaciones
 → reportes
```

## Idempotencia

El mismo archivo, parser y configuración producen el mismo lote lógico. Se detectan duplicados por hash.

## Lineage

Cada valor derivado conserva referencias a:

- archivo;
- fila;
- columna;
- timestamp;
- transformación;
- versión.

## Rendimiento

- Polars/PyArrow para lectura y transformación;
- Parquet privado para caches analíticos;
- PostgreSQL para entidades y consultas operativas;
- workers para análisis y reportes.
