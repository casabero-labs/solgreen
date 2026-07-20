-- Solgreen initial schema
-- Migration 001: core tables

CREATE TABLE IF NOT EXISTS import_batches (
    id UUID PRIMARY KEY,
    plant_id VARCHAR(64) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    original_filename VARCHAR(512) NOT NULL,
    sha256 CHAR(64) NOT NULL,
    byte_size INTEGER NOT NULL,
    parser_id VARCHAR(128) NOT NULL,
    parser_version VARCHAR(64) NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL,
    quality_summary JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_batches_plant_id ON import_batches(plant_id);
CREATE INDEX IF NOT EXISTS idx_import_batches_imported_at ON import_batches(imported_at);


CREATE TABLE IF NOT EXISTS canonical_samples (
    id SERIAL PRIMARY KEY,
    batch_id UUID REFERENCES import_batches(id) ON DELETE CASCADE,
    timestamp_axis TIMESTAMPTZ NOT NULL,
    source VARCHAR(16) NOT NULL,
    time_delta INTERVAL,
    flow_potencia_produccion_w DOUBLE PRECISION,
    flow_potencia_consumo_w DOUBLE PRECISION,
    flow_grid_w DOUBLE PRECISION,
    flow_soc_pct DOUBLE PRECISION,
    flow_battery_w DOUBLE PRECISION,
    telemetry_pv_power_w DOUBLE PRECISION,
    telemetry_grid_power_w DOUBLE PRECISION,
    telemetry_battery_power_w DOUBLE PRECISION,
    telemetry_soc_pct DOUBLE PRECISION,
    telemetry_inverter_state VARCHAR(64),
    quality_level VARCHAR(16) NOT NULL DEFAULT 'measured',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_canonical_samples_batch_id ON canonical_samples(batch_id);
CREATE INDEX IF NOT EXISTS idx_canonical_samples_timestamp ON canonical_samples(timestamp_axis);


CREATE TABLE IF NOT EXISTS canonical_episodes (
    id SERIAL PRIMARY KEY,
    batch_id UUID REFERENCES import_batches(id) ON DELETE CASCADE,
    episode_type VARCHAR(32) NOT NULL,
    start TIMESTAMPTZ NOT NULL,
    "end" TIMESTAMPTZ NOT NULL,
    duration INTERVAL NOT NULL,
    sample_count INTEGER NOT NULL,
    coverage_pct DOUBLE PRECISION NOT NULL,
    source_summary VARCHAR(16) NOT NULL,
    signals JSONB
);

CREATE INDEX IF NOT EXISTS idx_canonical_episodes_batch_id ON canonical_episodes(batch_id);
CREATE INDEX IF NOT EXISTS idx_canonical_episodes_start ON canonical_episodes(start);


CREATE TABLE IF NOT EXISTS rule_executions (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER REFERENCES canonical_episodes(id) ON DELETE CASCADE,
    rule_id VARCHAR(32) NOT NULL,
    rule_version VARCHAR(16) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    parameters_used JSONB NOT NULL,
    fired BOOLEAN NOT NULL,
    evidence JSONB,
    input_checksum VARCHAR(64) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rule_executions_episode_id ON rule_executions(episode_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_rule_id ON rule_executions(rule_id);


CREATE TABLE IF NOT EXISTS llm_interpretations (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER REFERENCES canonical_episodes(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    hypotheses JSONB,
    alternatives JSONB,
    missing_info JSONB,
    suggested_actions JSONB,
    warnings JSONB,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(64) NOT NULL,
    prompt_version VARCHAR(32) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_interpretations_episode_id ON llm_interpretations(episode_id);
