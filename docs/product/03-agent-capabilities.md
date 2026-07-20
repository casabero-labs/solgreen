# Capacidades de agentes

## Permitidas en modo read-only

- listar plantas accesibles;
- consultar cobertura y calidad de datos;
- listar episodios;
- obtener evidencias y métricas;
- comparar periodos;
- generar borradores de explicación;
- generar borradores de reporte.

## Prohibidas en el MVP

- cambiar SOC mínimo o máximo;
- modificar Grid Code;
- desactivar AFCI;
- accionar contactores o transferencia;
- eliminar archivos;
- enviar reportes fuera de la organización;
- ejecutar SQL o shell libre.

## Contrato

Toda capability devuelve datos estructurados, scopes explícitos, `request_id` y registro de auditoría.
