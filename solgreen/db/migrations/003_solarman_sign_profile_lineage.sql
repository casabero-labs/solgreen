-- Migration 003: add sign_profile_version column to solarman_normalized_signals
-- Supports energy integration by tracking which sign profile version normalized each row.

ALTER TABLE solarman_normalized_signals
    ADD COLUMN IF NOT EXISTS sign_profile_version TEXT;

CREATE INDEX IF NOT EXISTS idx_norm_signals_sign_profile_version
    ON solarman_normalized_signals(sign_profile_version);
