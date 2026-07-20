# Despliegue

## Objetivo

Self-hosted en Coolify con PostgreSQL/Butterbase, almacenamiento privado, API, worker y web.

## Servicios

- `solgreen-web`
- `solgreen-api`
- `solgreen-worker`
- `postgres`
- `redis`
- `object-storage` o proveedor compatible
- OpenTelemetry collector

## Secrets

Cargados desde Infisical. Nunca en Compose, repositorio ni logs.

## Flujo

1. CI: lint, typecheck, tests, build.
2. Crear backup previo si hay migración.
3. Deploy válido en Coolify.
4. Polling hasta estado final.
5. Verificar SHA del contenedor.
6. `/health` y smoke tests.
7. Validar importación sintética.
8. Registrar evidencia en `docs/deployments/`.

## Rollback

- imagen anterior;
- migración reversible o restore;
- originales permanecen inmutables;
- análisis regenerables.
