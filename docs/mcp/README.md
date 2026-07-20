# MCP de Solgreen

## Fase inicial

Diseño read-only. No se implementa hasta estabilizar API y contratos.

## Capabilities previstas

- `list_plants`
- `get_plant_health`
- `list_import_batches`
- `list_episodes`
- `get_episode`
- `get_episode_evidence`
- `compare_periods`
- `get_report_metadata`

## Restricciones

- scopes por planta;
- no secretos;
- no SQL libre;
- no archivos crudos por defecto;
- auditoría;
- respuestas paginadas;
- límites de volumen.
