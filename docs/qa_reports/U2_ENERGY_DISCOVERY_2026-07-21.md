# U2.0 — Energy Semantics Discovery

## Identification

- Date: 2026-07-21
- Line: `develop/solgreen-unified`
- PR: #27
- SHA: `a13b4a1af4d240cd758a28a7fe69297bad1a8d4e` (baseline)
- Phase: U2.0 — DISCOVERY

## Objective

Establish the scientific and contractual foundation for U2 energy
calculations before implementing any W→Wh integration or sign
normalization.

## Scope

- Inventory all power and energy signals in the system.
- Document measurement points (AC/DC, physical location).
- Document sign conventions per source (confirmed/provisional/unknown).
- Define authority hierarchy (fiscal vs. operational).
- Design conceptual contracts for sign profiles, directional
  normalization, and temporal integration.
- Define gap, coverage, and exclusion policies.
- Identify human gates and evidence requirements.
- Plan U2.1–U2.7 implementation sequence.

Out of scope:
- Any Wh/kWh calculation.
- Any sign normalization in code.
- Changes to CanonicalSample, parsers, or contracts.
- Tariffs, billing, or economic models.
- Frontend or API changes.

## Discovered Signal Inventory

### Signals in CanonicalSample (7 power/energy fields)

| Field | Source | Unit | AC/DC | Physical point | Sign convention | Status |
|---|---|---|---|---|---|---|
| `flow_potencia_produccion_w` | SolarMAN flow | W | AC | Inverter output | Unsigned (≥0) | provisional |
| `flow_potencia_consumo_w` | SolarMAN flow | W | AC | Load side | Unsigned (≥0) | provisional |
| `flow_grid_w` | SolarMAN flow | W | AC | Grid point (aggregator) | Original, negative=import? | provisional |
| `flow_battery_w` | SolarMAN flow | W | DC | Battery (aggregator) | Negative=charge? positive=discharge? | provisional |
| `telemetry_pv_power_w` | Inverter telemetry | W | **DC** | MPPT inputs | Unsigned (≥0), summed PV1+PV2 | provisional |
| `telemetry_grid_power_w` | Inverter telemetry | W | AC | Grid point (inverter) | Original, unknown direction | provisional |
| `telemetry_battery_power_w` | Inverter telemetry | W | DC | Battery (inverter) | Unknown | **unknown** |

### Non-power signals in CanonicalSample

| Field | Type | Status |
|---|---|---|
| `flow_soc_pct` | State (%) | provisional |
| `telemetry_soc_pct` | State (%) | provisional |
| `telemetry_inverter_state` | Text | provisional |

### Energy accumulator signals (not yet in CanonicalSample)

| Signal | Source | Unit | Direction | Status |
|---|---|---|---|---|
| `alimentacion_acumulada_de_red_kwh` | Inverter telemetry | kWh | Cumulative export | provisional |
| `energia_adquirida_acumulada_kwh` | Inverter telemetry | kWh | Cumulative import | provisional |
| `energia_de_carga_total_kwh` | Inverter telemetry | kWh | Cumulative charge | provisional |
| `energia_de_descarga_total_kwh` | Inverter telemetry | kWh | Cumulative discharge | provisional |
| `produccion_acumulada_kwh` | Inverter telemetry | kWh | Cumulative production | provisional |
| `consumo_total_kwh` | Inverter telemetry | kWh | Cumulative consumption | provisional |

### Directional power signals (not yet in CanonicalSample)

| Signal | Source | Unit | Direction | Status |
|---|---|---|---|---|
| `potencia_de_carga_w` | SolarMAN flow | W | Battery charge | provisional |
| `poder_de_descarga_w` | SolarMAN flow | W | Battery discharge | provisional |
| `poder_adquisitivo_w` | SolarMAN flow | W | Grid purchase | provisional (non-authority) |
| `potencia_de_alimentacion_w` | SolarMAN flow | W | Grid feed-in | provisional (non-authority) |
| `mains_charging_power_w` | Inverter telemetry | W | Grid→Battery charge | provisional |
| `pv_total_charging_power_w` | Inverter telemetry | W | PV→Battery charge | provisional |
| `potencia_de_carga_l1_w` | Inverter telemetry | W | Load L1 | provisional |
| `potencia_de_carga_l2_w` | Inverter telemetry | W | Load L2 | provisional |

## Authority Matrix

| Use case | Primary (fiscal) | Operational |
|---|---|---|
| Grid import/export | Fiscal meter + Afinia invoice | SolarMAN, inverter |
| Battery state/flow | BMS (to be confirmed) | Inverter, SolarMAN |
| PV production | MPPT (DC), inverter output (AC) | SolarMAN plant flow |
| Load consumption | Load CT clamps (to be confirmed) | Inverter telemetry |

## AC/DC Matrix

| Signal | AC | DC | Notes |
|---|---|---|---|
| `flow_potencia_produccion_w` | X | | Post-inversion AC output |
| `flow_potencia_consumo_w` | X | | Load side AC |
| `flow_grid_w` | X | | Grid AC |
| `flow_battery_w` | | X | Battery DC terminals |
| `telemetry_pv_power_w` | | X | MPPT inputs, before inverter |
| `telemetry_grid_power_w` | X | | Inverter grid port AC |

**Critical observation:** PV power in CanonicalSample is **DC** while
production and consumption in flow are **AC**. These cannot be directly
compared without accounting for inverter conversion efficiency.

## Sign Matrix

| Signal | Positive means | Negative means | Status | Evidence |
|---|---|---|---|---|
| `flow_potencia_produccion_w` | Generation | Not applicable (unsigned) | provisional | SolarMAN docs |
| `flow_potencia_consumo_w` | Consumption | Not applicable (unsigned) | provisional | SolarMAN docs |
| `flow_grid_w` | Export (delivery)? | Import (purchase)? | provisional | solarman-plant-flow.md |
| `flow_battery_w` | Discharge? | Charge? | provisional | CanonicalSample description |
| `telemetry_pv_power_w` | Generation | Not applicable (unsigned) | provisional | SIGNAL_SPECS |
| `telemetry_grid_power_w` | Unknown | Unknown | unknown | No evidence |
| `telemetry_battery_power_w` | Unknown | Unknown | unknown | No evidence |

**Note:** The `flow_battery_w` description in CanonicalSample states
"carga negativa, descarga positiva" but no source evidence confirms
this convention, and the parser performs no sign normalization.

## Key Uncertainties

1. **Grid sign convention** — `flow_grid_w` documentation says "puede
   usar signo negativo para compra" but this is not confirmed with
   physical observation.

2. **Battery sign convention** — `flow_battery_w` is documented as
   negative=charge, positive=discharge, but:
   - PlantFlowSample description says "signo canónico se calcula en parser"
     yet the parser does no normalization.
   - `telemetry_battery_power_w` sign is completely unknown.

3. **Temporal semantics** — unknown whether samples are instantaneous
   readings, interval averages, or held values. This affects integration
   method selection.

4. **Measurement point differences** — `flow_grid_w` (SolarMAN aggregator)
   and `telemetry_grid_power_w` (inverter) may not measure the same
   physical point.

5. **DC vs AC mixing** — `telemetry_pv_power_w` is DC while all flow
   signals are AC. Cannot be directly balanced.

6. **BMS authority** — BMS model and accuracy not confirmed. SOC from
   flow vs. telemetry may disagree (U1.4 only tested SOC consistency).

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Sign normalization without evidence | High | Blocked by human gates |
| W treated as Wh | High | Explicit contract, no sum without integration |
| DC vs AC mixing in balance | High | Documented prohibition until U2.5 |
| Cumulative counter validation deferred | Medium | Flagged as U2.7 activity |
| Flow/telemetry grid disagreement undetected | Medium | Human gate comparison windows |
| Battery sign differs between sources | Medium | Separate profiles per source |

## Proposed Contracts (Conceptual)

### PowerSignProfile (U2.1)

Versioned sign convention profile per canonical field, with
direction declaration, evidence source, and validity period.

### Directional Normalization (U2.1)

Pure function: `normalize_sign(sample, profile) → directional_fields`.
Preserves raw values; produces `grid_import_w ≥ 0`,
`grid_export_w ≥ 0`, `battery_charge_w ≥ 0`, `battery_discharge_w ≥ 0`.

### Temporal Integration (U2.2)

Pure function: `integrate_power(timeline, method, profiles) → EnergyInterval[]`.
Produces `energy_wh` from power intervals using selected method.

### EnergyInterval and EnergySummary (U2.2)

Per-interval energy breakdown and per-window aggregation with
coverage, duration, and quality metadata.

## Gap Policy

- No interpolation or assumption of constant power across gaps.
- Explicit states: `observed`, `missing`, `excluded_nonfinite`,
  `excluded_zero_duration`, `excluded_unconfirmed_sign`,
  `excluded_alignment`.
- Coverage = `observed_duration / expected_duration`.
- Do not scale observed energy to fill missing coverage.

## Coverage Policy

- `coverage_fraction < 1.0` means the period is partially observed.
- Missing energy is **unknown**, not zero.
- Presentation must show observed energy separately from
  coverage fraction.
- No threshold for "acceptable coverage" is defined in U2.0.

## Invalid Cases Identified

| Case | Detection | Handling |
|---|---|---|
| Timestamp repeated | Quality ordering (U1.2) | Exclude zero-duration interval |
| Timestamp out of order | Quality ordering (U1.2) | Sort or reject with lineage note |
| NaN/Inf in power | Plausibility (U1.3) | Exclude interval |
| None in power | All quality layers | Exclude interval |
| Sign unknown | PowerSignProfile status=unknown | Exclude interval |
| AC/DC mixed in balance | Contract enforcement | Prohibit balance |
| Apparent power treated as active | Type system / contract | Reject, flag |

## Human Gates

| Gate | What is needed | Status |
|---|---|---|
| Grid sign confirmation | Night window, known load, zero PV, meter reading | Pending |
| Battery sign confirmation | Charge window (PV), discharge window (night), SOC delta | Pending |
| Temporal semantics | Source documentation or experimental validation | Pending |
| Measurement points | CT clamp placement, inverter wiring, BMS connection | Pending |

## Deferred Decisions

| Decision | Deferred to | Reason |
|---|---|---|
| Integration method | U2.2 | Depends on temporal semantics |
| Grid energy normalization | U2.3 | Depends on sign profile |
| Battery energy normalization | U2.4 | Depends on sign profile |
| Physical balance equation | U2.5 | Needs all preconditions |
| Cumulative counter as validation | U2.7 | Needs counter behavior documented |
| Inverter efficiency for DC→AC | U2.5 | Needs manufacturer data |

## Proposed U2 Implementation Plan

| Phase | Goal | Depends on |
|---|---|---|
| U2.1 | PowerSignProfile + directional normalization functions | U2.0 human gates |
| U2.2 | Generic temporal integration W→Wh | U2.1 |
| U2.3 | Grid metrics (import/export, hourly/daily) | U2.2 |
| U2.4 | Battery metrics (charge/discharge, SOC-derived) | U2.2 |
| U2.5 | PV production and consumption metrics | U2.2 |
| U2.6 | Coverage, aggregations, hourly profiles | U2.3–U2.5 |
| U2.7 | Reconciliation with cumulative counters, U2 QA | U2.3–U2.6 |

## Stop Conditions

U2.0 is complete when:

- Signal inventory is comprehensive and classified.
- AC/DC and physical points are documented.
- Fiscal and operational authority are separated.
- Known and unknown signs are explicit.
- No sign has been normalized without a profile.
- No energy has been calculated.
- Gap and coverage policies exist.
- Temporal integration contract is proposed.
- ADR-008 remains Proposed (human gates pending).
- U2.1–U2.7 sequence is planned.
- CI is green.
- PR remains draft.
- No productive code changes.

## Rollback

- Revert the documentary commit.
- No code changes to revert.
- Main remains intact.

## Artifacts Produced

| File | Purpose |
|---|---|
| `docs/domain/ENERGY_SEMANTICS.md` | Complete signal inventory, authority hierarchy, sign conventions, conceptual contracts |
| `docs/decisions/ADR-008-energy-integration-and-sign-profiles.md` | Architectural decision: sign profiles, directional normalization, integration contract |
| `docs/qa_reports/U2_ENERGY_DISCOVERY_2026-07-21.md` | This QA report |

## Next Step

U2.1 — PowerSignProfile contract implementation and sign normalization
functions. Prerequisites: human gate sign confirmation windows
(grid and battery).

The normalization for Casabero requires private evidence of:
- Known grid import (night, zero PV, meter verification).
- Known battery charge and discharge (windows with confirmed SOC delta).
- Temporal semantics of each export source.
- Physical measurement point for each signal.
