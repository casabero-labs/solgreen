-- Solarman API snapshots: idempotent raw data + normalized signals
-- Migration 002: add live API ingestion support

CREATE TABLE IF NOT EXISTS solarman_snapshots (
    id BIGSERIAL PRIMARY KEY,
    device_sn TEXT NOT NULL,
    device_type TEXT,
    device_state INTEGER,
    collection_time TIMESTAMPTZ NOT NULL,
    station_id TEXT NOT NULL,
    plant_id TEXT NOT NULL,
    raw_signals JSONB NOT NULL,
    signal_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(device_sn, collection_time)
);

CREATE TABLE IF NOT EXISTS solarman_normalized_signals (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES solarman_snapshots(id) ON DELETE CASCADE,
    signal_key TEXT NOT NULL,
    canonical_field TEXT NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'inverter_telemetry',
    raw_power_w DOUBLE PRECISION,
    normalized_status TEXT NOT NULL,
    grid_import_w DOUBLE PRECISION,
    grid_export_w DOUBLE PRECISION,
    battery_charge_w DOUBLE PRECISION,
    battery_discharge_w DOUBLE PRECISION,
    pv_generation_w DOUBLE PRECISION,
    load_consumption_w DOUBLE PRECISION,
    warnings JSONB,
    within_zero_deadband BOOLEAN DEFAULT FALSE,
    UNIQUE(snapshot_id, signal_key)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_device_sn
    ON solarman_snapshots(device_sn);
CREATE INDEX IF NOT EXISTS idx_snapshots_collection_time
    ON solarman_snapshots(collection_time);
CREATE INDEX IF NOT EXISTS idx_snapshots_plant_id
    ON solarman_snapshots(plant_id);
CREATE INDEX IF NOT EXISTS idx_norm_signals_snapshot_id
    ON solarman_normalized_signals(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_norm_signals_canonical_field
    ON solarman_normalized_signals(canonical_field);
