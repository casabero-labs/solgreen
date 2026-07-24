# U2.2b — Solarman Energy Runtime: QA Report

**Date:** 2026-07-24
**Status:** ENGINEERING_CLOSED (pending orchestrator review)
**Baseline:** `7c0f52a48803d35e43107bcab2608268fdd1dd9d`
**Branch:** `feat/u2-2b-solarman-energy-runtime`
**PR:** #33

---

## Goal

Connect persisted SOLARMAN normalized power rows to the pure U2.2a temporal integration core (`integrate_energy()`) at sync runtime, with per-device isolation, explicit profile-version and lookback configuration, fail-closed enum parsing, and immutable in-memory results.

---

## Architecture — Per-Device Isolation

Each device operates independently:

```
SOLARMAN device snapshot (via API)
  -> sign normalization (with sign_profile_version)
  -> snapshot and directional values persisted
  -> for each device whose persistence succeeded (inserted or skipped):
       period_end = snapshot.collection_time (device-specific)
       period_start = period_end - lookback (device-specific window)
       persisted historical rows loaded (JOIN filtered by plant_id, station_id,
         device_sn, canonical_field, source_system, period)
       DirectionalPowerObservation adaptation per row
         (DIRECTIONAL_POWER_FIELD_MAP selects correct column by series_direction)
       integrate_energy() per series (5 series, trapezoidal)
       device-level SolarmanEnergyRuntimeResult stored in DeviceSyncResult
  -> SyncResult aggregates energy_series_attempted/succeeded/failed across devices
  -> PARTIAL_SUCCESS when energy_series_failed > 0
  -> snapshot not rolled back by energy failure
```

No cross-device observation combination. No station-wide latest timestamp.

---

## Exact Query Filters

```sql
WHERE ss.plant_id = %s
  AND ss.station_id = %s
  AND ss.device_sn = %s
  AND ns.canonical_field = %s
  AND ns.source_system = %s
  AND ss.collection_time >= %s
  AND ss.collection_time <= %s
ORDER BY ss.collection_time ASC, ss.id ASC, ns.id ASC
```

---

## Runtime Configuration

| Parameter | Default | Notes |
|---|---|---|
| `mode` | `off` | OFF or `instantaneous` |
| `profile_version` | None | Required for instantaneous |
| `expected_interval` | None | Strictly positive, ISO duration |
| `maximum_authorized_interval` | None | >= expected, strictly positive |
| `lookback` | None | >= max, strictly positive |

- All 5 CLI flags with `SOLGREEN_ENERGY_*` env vars
- No hardcoded 1-hour window
- No defaults for durations

---

## Sign-Profile Lineage

- Migration `003_solarman_sign_profile_lineage.sql` adds nullable `sign_profile_version TEXT` column
- No backfill — legacy rows have `null` lineage
- **Null-lineage fail-closed:** `adapt_persisted_row_to_observation` produces `PROFILE_NOT_FOUND` observations with `power_w=None`
- Rows with null lineage contribute no energy

---

## Directional Zero-Materialization

Complementary zeros are persisted **only** for `NormalizationStatus.NORMALIZED`:

| Active direction | Persisted fields |
|---|---|
| GRID_IMPORT (`grid_import_w=magnitude`) | `grid_export_w=0.0` |
| GRID_EXPORT (`grid_export_w=magnitude`) | `grid_import_w=0.0` |
| BATTERY_CHARGE (`battery_charge_w=magnitude`) | `battery_discharge_w=0.0` |
| BATTERY_DISCHARGE (`battery_discharge_w=magnitude`) | `battery_charge_w=0.0` |
| PV_GENERATION | One column only |

All non-normalized statuses (including `PROFILE_NOT_CONFIRMED`) leave all directional columns as `None`.

---

## Fail-Closed Enum Rejection

Unknown persisted normalization status, canonical field, or source system raises `ValueError`. No silent fallback to `NORMALIZED`. No silent repair of malformed rows.

---

## Idempotent Recomputation

Energy integration runs whether the snapshot was **newly inserted** or **already present** (idempotent skip). A repeated sync may recompute the same in-memory energy results. No energy rows persisted — idempotent by design.

---

## Retained Immutable Results

- `DeviceSyncResult.energy_result: SolarmanEnergyRuntimeResult | None` stores the full immutable result
- Per-series `IntegrationResult` values available internally
- `SolarmanEnergyRuntimeResult` is frozen (Pydantic `ConfigDict(frozen=True)`)
- `SyncResult.energy_profile_version` carries the explicit context profile version
- CLI aggregate includes `profile_version` and `results_persisted=false`

---

## Partial-Success Policy

- Per-device isolation: each device's integration independent
- Per-series isolation: one series failure does not block others
- `PARTIAL_SUCCESS` when `energy_series_failed > 0`
- Energy failure does not roll back snapshot persistence
- Failed series appear in `per_series_errors`

---

## OFF-Output Compatibility

When energy integration is OFF:
- No `energy_integrated` key
- No `energy_series_count` key
- No `energy_integration` key
- No "Energy integration: disabled" line
- Complete output matches pre-U2.2b contract

When enabled, the aggregate contains:
```json
{
  "energy_integration": {
    "enabled": true,
    "profile_version": "explicit-profile-version",
    "series_attempted": 5,
    "series_succeeded": 5,
    "series_failed": 0,
    "results_persisted": false
  }
}
```

---

## Test Evidence

### Focused Tests
- `test_energy_runtime.py`: **51 tests** (97% coverage on `energy_runtime.py`)
- `test_sync.py`: **55 tests** (updated for device isolation, idempotent recomputation, complementary zero semantics)

### Full Suite
- **1100 unit tests pass**, 8 integration skipped, 0 deselected
- Total coverage: **84.42%**
- `energy_runtime.py` coverage: **97%**

### Quality
- Ruff: PASS (0 errors)
- Ruff format: PASS
- mypy: PASS (0 errors in 83 source files)
- Frontend: typecheck + tests (4) + build pass

---

## Exclusions

No energy-result persistence, no metric persistence, no physical balance, no billing, no tariff, no subsidy, no savings, no frontend, no Coolify, no deployment, no D10 activation (remains opt-in), no production `effective_from`.

---

## Rollback

Revert commits from `f5a99a5` through the latest HEAD and run:

```sql
DROP INDEX IF EXISTS idx_norm_signals_sign_profile_version;
ALTER TABLE solarman_normalized_signals DROP COLUMN IF EXISTS sign_profile_version;
```

---

## Next Exact Step

**U2.3a:** Grid import/export energy metrics and persistence contracts
