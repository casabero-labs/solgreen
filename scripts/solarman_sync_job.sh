#!/usr/bin/env bash
#
# solarman_sync_job.sh — scheduler-ready SOLARMAN sync entrypoint
#
# Usage:
#   SOLGREEN_DATABASE_URL="..." SOLGREEN_SOLARMAN_STATION_ID="..." ./scripts/solarman_sync_job.sh
#
# Environment variables:
#   SOLGREEN_DATABASE_URL                PostgreSQL connection URL (optional)
#   SOLGREEN_SOLARMAN_STATION_ID        Station ID to sync (optional, auto-detected if only one)
#   SOLGREEN_PLANT_ID                    Plant identifier (default: casabero)
#   SOLGREEN_SIGN_NORMALIZATION_MODE    off|legacy|d10 (default: off)
#   SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM  ISO 8601 timestamp for d10 mode
#   SOLARMAN_BASE_URL                   SOLARMAN API base URL
#   SOLARMAN_APP_ID                     SOLARMAN application ID
#   SOLARMAN_APP_SECRET                 SOLARMAN application secret
#   SOLARMAN_EMAIL                      SOLARMAN account email
#   SOLARMAN_PASSWORD_SHA256            SHA-256 of SOLARMAN account password
#   SOLARMAN_TIMEOUT_SECONDS            HTTP timeout (default: 30)
#   SOLARMAN_MAX_RETRIES                Max retries (default: 3)
#   SOLGREEN_SYNC_RUN_MIGRATIONS         Set to "1" to run migrations before sync (default: no)
#   SOLGREEN_SYNC_MIGRATIONS_DIR         Path to migrations directory (optional)
#   SOLGREEN_SYNC_DRY_RUN                Set to "1" for dry-run mode (default: no)
#   SOLGREEN_SYNC_NO_DB                 Set to "1" to skip database persistence (default: no)
#   SOLGREEN_SYNC_TIMEOUT_SECONDS        Lock timeout (default: 300)
#   SOLGREEN_SYNC_SKIP_DOCTOR           Set to "1" to skip pre-sync doctor check (default: no)
#
set -euo pipefail

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
export SOLGREEN_PLANT_ID="${SOLGREEN_PLANT_ID:-casabero}"
export SOLGREEN_SIGN_NORMALIZATION_MODE="${SOLGREEN_SIGN_NORMALIZATION_MODE:-off}"

# Logging helper (no secrets)
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

# Exit codes:
#   0  — success
#   1  — failure (API error, etc.)
#   2  — skipped (lock busy)
#   3  — configuration error
#   4  — doctor check failed / not ready

# Check configuration
if [[ -z "${SOLARMAN_BASE_URL:-}" ]] || [[ -z "${SOLARMAN_APP_ID:-}" ]] || \
   [[ -z "${SOLARMAN_APP_SECRET:-}" ]] || [[ -z "${SOLARMAN_EMAIL:-}" ]] || \
   [[ -z "${SOLARMAN_PASSWORD_SHA256:-}" ]]; then
    log "FATAL: Missing required SOLARMAN_* environment variables"
    exit 3
fi

# Run migrations if requested
if [[ "${SOLGREEN_SYNC_RUN_MIGRATIONS:-}" == "1" ]]; then
    if [[ -z "${SOLGREEN_DATABASE_URL:-}" ]]; then
        log "WARN: SOLGREEN_SYNC_RUN_MIGRATIONS=1 but no SOLGREEN_DATABASE_URL — skipping migrations"
    else
        log "Running migrations..."
        MIGRATIONS_DIR="${SOLGREEN_SYNC_MIGRATIONS_DIR:-$PROJECT_ROOT/solgreen/db/migrations}"
        uv run solgreen db migrate \
            --db-url "${SOLGREEN_DATABASE_URL}" \
            --migrations-dir "${MIGRATIONS_DIR}" \
            --dry-run
        uv run solgreen db migrate \
            --db-url "${SOLGREEN_DATABASE_URL}" \
            --migrations-dir "${MIGRATIONS_DIR}"
        log "Migrations complete"
    fi
fi

# Build sync command
SYNC_CMD=(uv run solgreen solarman sync)

# Add plant-id
SYNC_CMD+=(--plant-id "${SOLGREEN_PLANT_ID}")

# Add station-id if set
if [[ -n "${SOLGREEN_SOLARMAN_STATION_ID:-}" ]]; then
    SYNC_CMD+=(--station-id "${SOLGREEN_SOLARMAN_STATION_ID}")
fi

# Add database URL if set
if [[ -n "${SOLGREEN_DATABASE_URL:-}" ]] && [[ "${SOLGREEN_SYNC_NO_DB:-}" != "1" ]]; then
    SYNC_CMD+=(--db-url "${SOLGREEN_DATABASE_URL}")
fi

# Add no-db flag if set
if [[ "${SOLGREEN_SYNC_NO_DB:-}" == "1" ]]; then
    SYNC_CMD+=(--no-db)
fi

# Add dry-run flag if set
if [[ "${SOLGREEN_SYNC_DRY_RUN:-}" == "1" ]]; then
    SYNC_CMD+=(--dry-run)
fi

# Add normalization mode
SYNC_CMD+=(--sign-normalization-mode "${SOLGREEN_SIGN_NORMALIZATION_MODE}")

# Add effective-from if set
if [[ -n "${SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM:-}" ]]; then
    SYNC_CMD+=(--sign-registry-effective-from "${SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM}")
fi

# Add JSON output
SYNC_CMD+=(--json)

# Optionally run doctor first
if [[ "${SOLGREEN_SYNC_SKIP_DOCTOR:-}" != "1" ]]; then
    log "Running pre-sync doctor check..."
    DOCTOR_OUTPUT=$(uv run solgreen solarman doctor --json 2>&1)
    DOCTOR_EXIT=$?

    if [[ $DOCTOR_EXIT -ne 0 ]]; then
        log "Doctor check exited with code $DOCTOR_EXIT — halting pipeline"
        if echo "$DOCTOR_OUTPUT" | python3 -c "import sys,json; json.load(sys.stdin); print('valid')" 2>/dev/null; then
            echo "$DOCTOR_OUTPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null
        else
            log "ERROR: Doctor output could not be parsed — possible configuration or network issue"
        fi
        exit 4
    fi

    DOCTOR_READY=$(echo "$DOCTOR_OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('READY' if d.get('ready', False) else 'NOT_READY')" 2>/dev/null || echo "PARSE_ERROR")

    if [[ "$DOCTOR_READY" != "READY" ]]; then
        log "Doctor check: NOT READY — halting pipeline"
        if [[ "$DOCTOR_READY" != "PARSE_ERROR" ]]; then
            echo "$DOCTOR_OUTPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null
        else
            log "ERROR: Doctor output could not be parsed — possible configuration or network issue"
        fi
        exit 4
    fi

    log "Doctor check passed"
fi

log "Starting SOLARMAN sync..."
log "Command: solgreen solarman sync --plant-id ${SOLGREEN_PLANT_ID} --sign-normalization-mode ${SOLGREEN_SIGN_NORMALIZATION_MODE}"

# Execute sync
set +e
OUTPUT=$("${SYNC_CMD[@]}" 2>&1)
EXIT_CODE=$?
set -e

# Parse exit code and output
if [[ $EXIT_CODE -eq 0 ]]; then
    STATUS=$(echo "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status', d.get('ok', 'UNKNOWN')))" 2>/dev/null || echo "SUCCESS")
    if [[ "$STATUS" == "SKIPPED_LOCKED" ]]; then
        log "Sync skipped: lock busy (another sync running); no API call made"
        echo "$OUTPUT"
        exit 0
    fi
    log "Sync complete: $STATUS"
    echo "$OUTPUT"
    exit 0
elif [[ $EXIT_CODE -eq 1 ]]; then
    log "Sync failed or partial success"
    echo "$OUTPUT"
    exit 1
else
    log "Sync error (exit $EXIT_CODE)"
    echo "$OUTPUT"
    exit $EXIT_CODE
fi
