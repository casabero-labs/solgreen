# U2.2A — Temporal Integration Results

**Date:** 2026-07-24
**Loop:** U2.2a — Temporal integration core for normalized directional power
**Branch:** `feat/u2-2-temporal-integration`
**PR:** #31

## Goal

Implement the pure temporal integration core that converts validated,
non-negative directional power observations (W) into observed energy (Wh)
using an explicit instantaneous-sample contract and trapezoidal integration.

## Implemented Contracts

### `solgreen/energy/integration.py`

| Contract | Type | Description |
|---|---|---|
| `SampleSemantics` | StrEnum | `instantaneous`, `interval_average`, `unknown` |
| `IntegrationMethod` | StrEnum | `trapezoidal` |
| `IntegrationProfile` | BaseModel (frozen) | Profile version, semantics, method, intervals |
| `IntervalStatus` | StrEnum | `observed`, `missing`, `excluded_nonfinite`, `excluded_zero_duration`, `excluded_unconfirmed_sign`, `not_applicable` |
| `DirectionalPowerObservation` | BaseModel (frozen) | Timestamped directional power observation |
| `EnergyInterval` | BaseModel (frozen) | Interval between two consecutive observations |
| `EnergySummary` | BaseModel (frozen) | Aggregated period summary |
| `IntegrationResult` | BaseModel (frozen) | Immutable (intervals, summary) container |
| `integrate_energy()` | Pure function | Main integration entry point |

## Formulas

### Trapezoidal Integration

```
duration_hours = duration.total_seconds() / 3600.0
energy_wh = ((start_power_w + end_power_w) / 2.0) * duration_hours
```

### Coverage

```
coverage_fraction = observed_duration / expected_duration
0 <= coverage_fraction <= 1
```

### kWh Conversion

```
observed_energy_kwh = observed_energy_wh / 1000.0
```

## Supported Sample Semantics

- `instantaneous` — samples represent instantaneous readings at the timestamp.

## Unsupported Semantics

- `interval_average` — rejected at profile validation.
- `unknown` — rejected at profile validation.

Semantics are never inferred from source names in the pure domain layer.

## Edge-Case Policy

| Case | Handling |
|---|---|
| Empty series | Zero energy, zero coverage, full period missing |
| Single observation | Zero energy, zero coverage (no valid pair) |
| Duplicate timestamps | `excluded_zero_duration`, energy_wh=None |
| Out-of-order timestamps | Batch-level rejection |
| Gap > max_authorized | `missing`, energy_wh=None, no interpolation |
| Non-finite endpoint | `excluded_nonfinite`, energy_wh=None |
| Unconfirmed sign | `excluded_unconfirmed_sign`, energy_wh=None |
| Zero measured power | `observed` with energy_wh=0.0 |
| Leading boundary | `missing` duration |
| Trailing boundary | `missing` duration |
| Missing energy | Unknown, not zero; never scale to fill coverage |

## Test Evidence

61 focused unit tests in `tests/unit/test_energy/test_integration.py`:

- Model validation: naive timestamp, non-finite/negative power, missing profile version, invalid direction, frozen immutability.
- Integration behavior: constant 1000W/1h = 1000Wh, linear ramp 0→1000W/1h = 500Wh, zero power = 0Wh observed, irregular authorized interval, multiple interval accumulation, Wh/kWh conversion.
- Gap policy: exceeded max_authorized → missing, leading/trailing boundaries → missing, observations outside period filtered.
- Edge cases: empty series, single observation, duplicate timestamps, out-of-order rejection, coverage never scales energy.
- Excluded intervals: missing endpoint → excluded_nonfinite, unconfirmed sign → excluded_unconfirmed_sign, both non-finite → excluded.
- Homogeneous-series: mixed source field, source system, direction, and profile version all rejected.
- Immutability: input order preserved, returned models frozen, lineage stable, warnings deterministic.
- Six valid directions all integrate correctly.
- Floating-point precision preserved.

## Pre-existing Test Failure

One test in `test_migrations.py` (`test_default_migrations_path_does_not_crash`)
fails due to a pre-existing duplicate migration file (`002_solarman_snapshots` copy).
This is not caused by U2.2a changes.

## Coverage

Integration module: 87% (45 misses in uncovered branches including error paths and `from_normalized` factory method).

Overall project: 73% (depressed by `* 2.py` backup files at 0% coverage and `db/*` omitted from coverage configuration).

## Exclusions

- No SOLARMAN API, auth, endpoints, sync, or persistence changes.
- No scheduler changes.
- No PostgreSQL migrations.
- No CLI commands.
- No frontend changes.
- No tariff, subsidy, or billing logic.
- No PDF generation.
- No Coolify or deployment changes.
- D10 remains disabled.
- No `effective_from` set.
- No private datasets or evidence.

## Rollback

Revert commits on `feat/u2-2-temporal-integration`. No production files
modified. No existing contracts broken. Pure addition.

## Next Exact Step

**U2.2b** — Source-profile selection and runtime wiring.
Select the `IntegrationProfile` for each SOLARMAN source, connect
`integrate_energy` to the sync pipeline. No billing, tariffs, frontend,
or reports.
