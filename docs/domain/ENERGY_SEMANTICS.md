# Energy Semantics — Signal Inventory, Authority and Sign Conventions

## Purpose

Establish the scientific foundation for U2 energy calculations before any
Wh/kWh integration. This document captures:

1. What each power signal represents.
2. Where it is physically measured.
3. Whether it is AC or DC.
4. What sign convention each source uses.
5. Which source holds authority for each use case.
6. Whether temporal integration is currently safe.
7. How import, export, charge and discharge will be represented.
8. How gaps, misalignment, coverage and invalid samples will be treated.

This document is the **DISCOVERY result of U2.0** — it does not produce
operational energy metrics.

---

## Signal Inventory

### Canonical Signals Currently Present in CanonicalSample

| Canonical field | Source | Original name | Unit | Power or Energy | AC or DC | Physical point | Physical direction | Sign convention | Confirmation status | Authority | Currently integrable | Evidence | Risks | Next gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `flow_potencia_produccion_w` | SolarMAN plant flow | `Potencia de producción(W)` | W | Power | AC | Inverter AC output (post-inversion) | Generation | Unsigned magnitude (≥0) | **provisional** | Operational | No | SolarMAN docs describe "producción" as output power; parser copies raw float | May include parasitic consumption not disaggregated | Confirm with inverter datasheet whether this is AC gross or net |
| `flow_potencia_consumo_w` | SolarMAN plant flow | `Potencia de consumo(W)` | W | Power | AC | Load side (household distribution) | Consumption | Unsigned magnitude (≥0) | **provisional** | Operational | No | SolarMAN docs describe "consumo" as total load; parser copies raw float | May conflate household consumption with system losses | Confirm measurement point (CT clamp location) |
| `flow_grid_w` | SolarMAN plant flow | `Energía de la red(W)` | W | Power | AC | Grid connection point (meter-side) | Bidirectional net | **Original SolarMAN sign preserved** — negative may = import (purchase), positive may = export (delivery). NOT normalized. | **provisional** | Operational | No | solarman-plant-flow.md: "puede usar signo negativo para compra y positivo para posible entrega"; column misnamed "energía" but stores W | Column name "energía" is misleading (stores power, not energy); sign not yet confirmed with private data | Human gate: night window with known consumption and zero PV |
| `flow_battery_w` | SolarMAN plant flow | `Potencia de la batería(W)` | W | Power | DC | Battery terminals (aggregate plant view) | Bidirectional net | **Documented as negative=charge, positive=discharge** — but sign normalization NOT performed in parser. | **provisional** | Operational | No | CanonicalSample description: "carga negativa, descarga positiva"; PlantFlowSample description: "signo canónico se calcula en parser" but parser does no normalization | Contradiction: PlantFlowSample claims parser normalizes, parser does not normalize; no source evidence for sign convention | Human gate: known charge/discharge window |
| `flow_soc_pct` | SolarMAN plant flow | `SoC(%)` | % | State (not power/energy) | N/A | BMS (via inverter/plant flow aggregation) | State-of-charge | 0–100 %, no sign | **provisional** | Operational | N/A | Raw SOC copied from plant flow; SolarMAN docs imply BMS origin | SOC from plant flow may differ from inverter telemetry SOC; aggregation method unknown | Confirm BMS source and aggregation |
| `telemetry_pv_power_w` | Inverter telemetry | `Potencia CC PV1(W)` + `Potencia CC PV2(W)` | W | Power | **DC** | PV MPPT inputs (panel side, before inverter) | Generation | Unsigned magnitude (≥0), summed from two MPPT channels | **provisional** | Operational | No | `_pv_power(t)` = pv1 + pv2; both original names describe "CC" (DC); zero preserved since U1.1 fix | Sum assumes both channels are active; single-channel failure may underreport | Confirm MPPT channel count and independence |
| `telemetry_grid_power_w` | Inverter telemetry | `Total Active Power Of The Grid(W)` | W | Power | AC | Grid connection point (inverter-side) | Bidirectional net | **Original inverter sign preserved** — NOT normalized | **provisional** | Operational | No | Using `total_active_power_of_the_grid_w` (index 50); corrected from `potencia_total_ca_w` in U1.4.0 | This is active power at grid port of the inverter, NOT at the fiscal meter; sign may differ from flow_grid_w | Human gate: compare with flow_grid_w in known windows |
| `telemetry_battery_power_w` | Inverter telemetry | `Potencia de batería(W)` | W | Power | DC | Battery terminals (inverter-side measurement) | Bidirectional net | **Original inverter sign preserved** — NOT normalized. No sign convention documented. | **unknown** | Operational | No | Joins from `potencia_de_bateria_w` (index 85); SIGNAL_SPECS marks as POWER_W but no direction declared | No evidence whether positive=charge or positive=discharge; may differ from flow_battery_w | Human gate: known charge window from PV or known grid charge |
| `telemetry_soc_pct` | Inverter telemetry | `SoC(%)` | % | State | N/A | BMS (via inverter telemetry) | State-of-charge | 0–100 %, no sign | **provisional** | Operational | N/A | Joins from `soc_pct` (index 86); consistency with flow_soc_pct evaluated in U1.4 | BMS accuracy and sampling may differ from plant flow aggregation | Confirm BMS model and accuracy |
| `telemetry_inverter_state` | Inverter telemetry | `Current state of machine` | text | Status | N/A | Inverter logic board | Machine state | N/A | **provisional** | Operational | N/A | Preserved via `get_text` since U1.1; states include standby, idle, waiting, fault | State labels are inverter-specific, not standardized | Confirm state machine documentation for this inverter model |

### Additional Signals Available But Not Yet in CanonicalSample

| Canonical field (conceptual) | Source | Original name | Unit | Power or Energy | AC or DC | Physical point | Sign convention | Confirmation status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `l1_utility_active_power_w` | Inverter telemetry | `L1 Utility Active Power(W)` | W | Power | AC | Grid L1 (inverter-side) | Original, unknown direction | **unknown** | Separate L1 measurement; could help disambiguate net vs directional |
| `l2_utility_active_power_w` | Inverter telemetry | `L2 Utility Active Power(W)` | W | Power | AC | Grid L2 (inverter-side) | Original, unknown direction | **unknown** | Separate L2 measurement |
| `potencia_de_carga_l1_w` | Inverter telemetry | `Potencia de carga L1(W)` | W | Power | AC | Load L1 (inverter-side) | Unsigned, consumption | **provisional** | Load-side measurement, potentially more granular |
| `potencia_de_carga_l2_w` | Inverter telemetry | `Potencia de carga L2(W)` | W | Power | AC | Load L2 (inverter-side) | Unsigned, consumption | **provisional** | Load-side measurement, L2 |
| `potencia_de_consumo_total_w` | Inverter telemetry | `Potencia de consumo total(W)` | W | Power | AC | Load side (total) | Unsigned, consumption | **provisional** | Total load from inverter telemetry |
| `potencia_total_ca_w` | Inverter telemetry | `Potencia total CA (activa)(W)` | W | Power | AC | Inverter AC output | Unsigned, generation | **provisional** | Total AC active output; previously misused as grid power (fixed U1.4.0) |
| `mains_charging_power_w` | Inverter telemetry | `Mains Charging Power(W)` | W | Power | AC → DC (battery) | Grid-to-battery charging path | Unsigned, charge from grid | **provisional** | Could confirm grid-to-battery flow |
| `pv_total_charging_power_w` | Inverter telemetry | `PV Total Charging Power(W)` | W | Power | DC | PV-to-battery charging path | Unsigned, charge from PV | **provisional** | Could confirm PV-to-battery flow |
| `total_charging_power_w` | Inverter telemetry | `Total Charging Power (PV + Mains)(W)` | W | Power | DC | Combined battery charging | Unsigned, charge | **provisional** | Total battery charging from all sources |
| `energia_de_carga_total_kwh` | Inverter telemetry | `Energía de carga total(kWh)` | kWh | **Energy** | DC | Battery (cumulative) | Cumulative charge, increasing | **provisional** | Cumulative accumulator — could provide truth for integration validation |
| `energia_de_descarga_total_kwh` | Inverter telemetry | `Energía de descarga total(kWh)` | kWh | **Energy** | DC | Battery (cumulative) | Cumulative discharge, increasing | **provisional** | Cumulative accumulator |
| `alimentacion_acumulada_de_red_kwh` | Inverter telemetry | `Alimentación acumulada de red(kWh)` | kWh | **Energy** | AC | Grid (cumulative) | Cumulative grid feed-in | **provisional** | Cumulative export energy |
| `energia_adquirida_acumulada_kwh` | Inverter telemetry | `Energía adquirida acumulada(kWh)` | kWh | **Energy** | AC | Grid (cumulative) | Cumulative grid import | **provisional** | Cumulative import energy |
| `produccion_acumulada_kwh` | Inverter telemetry | `Producción acumulada (activa)(kWh)` | kWh | **Energy** | AC | Inverter AC output (cumulative) | Cumulative production | **provisional** | Cumulative AC production |
| `produccion_diaria_kwh` | Inverter telemetry | `Producción diaria (activa)(kWh)` | kWh | **Energy** | AC | Inverter AC output (daily) | Daily production | **provisional** | Daily AC production reset |
| `consumo_total_kwh` | Inverter telemetry | `Consumo total(kWh)` | kWh | **Energy** | AC | Load side (cumulative) | Cumulative consumption | **provisional** | Cumulative load energy |
| `consumo_diario_kwh` | Inverter telemetry | `Consumo diario(kWh)` | kWh | **Energy** | AC | Load side (daily) | Daily consumption | **provisional** | Daily consumption reset |
| `flow_potencia_de_carga_w` | SolarMAN plant flow | `Potencia de carga(W)` | W | Power | DC | Battery (plant flow) | Unsigned magnitude | **provisional** | Plant flow charge power |
| `flow_poder_de_descarga_w` | SolarMAN plant flow | `Poder de descarga(W)` | W | Power | DC | Battery (plant flow) | Unsigned magnitude | **provisional** | Plant flow discharge power |
| `flow_poder_adquisitivo_w` | SolarMAN plant flow | `Poder adquisitivo(W)` | W | Power | AC | Grid (purchase) | Unsigned magnitude | **provisional** | Documented as non-authority in solarman-plant-flow.md |
| `flow_potencia_de_alimentacion_w` | SolarMAN plant flow | `Potencia de alimentación(W)` | W | Power | AC | Grid (feed-in) | Unsigned magnitude | **provisional** | Documented as non-authority in solarman-plant-flow.md |

### Confirmation Status Definitions

| Status | Meaning | Permitted actions |
|---|---|---|
| `confirmed` | Sign convention verified with human evidence | Normalization, energy calculation, fiscal presentation |
| `provisional` | Documented from sources, plausible but not verified | Operational estimates, reconciliation, profiles (marked) |
| `unknown` | No source evidence for sign convention | Cannot normalize, cannot calculate directional energy |
| `not_applicable` | No sign convention needed (e.g. SOC, state text) | N/A |

---

## Why Certain Comparisons Are Invalid

### PV DC Power vs AC Consumption

- `telemetry_pv_power_w` is **DC power at MPPT inputs** (before the inverter).
- `flow_potencia_consumo_w` is **AC power at the load side** (after the inverter).
- The inverter has conversion losses (typically 3–8 %).
- PV DC may partially charge battery instead of serving loads.
- **Cannot directly compare or balance PV DC with AC consumption without accounting for inverter efficiency and battery flow.**

### Apparent Power vs Active Power

- Signals like `potencia_aparente_de_consumo_total_va` (VA) measure **apparent power**.
- Real power (W) = apparent power (VA) × power factor (PF).
- Power factor may vary by load type and is typically 0.7–1.0.
- **Apparent power in VA must not be treated as active power in W.**

### W vs Wh

- All CanonicalSample signals are **instantaneous power in Watts (W)**.
- Watts are a **rate** (joules per second), not a quantity.
- To obtain energy (Wh), power must be **integrated over time**: `energy_wh = ∫ power_w dt / 3600`.
- Summing W values without accounting for time intervals produces a number with **no physical meaning**.
- **W must never be treated as Wh or kWh without explicit temporal integration.**

### Net Signal vs Two Directional Records

- A single bidirectional net signal (e.g. `flow_grid_w` which can be positive or negative) represents the **algebraic sum** of import and export at a given instant.
- It does **not** decompose into two separate directional magnitudes.
- The fact that `flow_grid_w = −1500` at some timestamp does **not** prove that grid import was 1500 W and export was 0 W — it only proves the net flow was 1500 W towards import.
- **A net signal must not be treated as two registers without a validated sign profile.**

### Name Similarity Does Not Prove Physical Equivalence

- `flow_grid_w` and `telemetry_grid_power_w` both describe "grid power" at the same physical site.
- However, `flow_grid_w` comes from the **SolarMAN plant flow aggregator**, while `telemetry_grid_power_w` comes from the **inverter directly**.
- These may represent the same physical quantity measured at different points (inverter side vs. aggregator), with different sign conventions, different sampling, and different accuracy.
- **Naming similarity does not demonstrate physical equivalence — each signal must be traced to its measurement point.**

---

## Authority Hierarchy

### Billing and Grid Exchange

**Primary authority (fiscal):**

1. Fiscal meter (Afinia or equivalent utility meter).
2. Official invoice document.
3. Official records from the utility or grid operator.

**Operational source (non-fiscal):**

1. SolarMAN plant flow — useful for estimation, reconciliation, and hourly profiles.
2. Inverter telemetry — useful for cross-validation and granular analysis.

SolarMAN and inverter readings **do not substitute** the fiscal meter for billing or regulatory purposes. Any presentation of grid energy must clearly distinguish:

- **Estimated** — from SolarMAN/inverter integration.
- **Billed** — from the fiscal meter.
- **Reconciled** — after comparison.

### Battery

Battery authority depends on:

- **BMS** (Battery Management System) — typically the most accurate source for SOC, voltage, current, and cumulative energy.
- **Inverter** — may report battery power with its own measurement and sign convention.
- **SolarMAN plant flow** — aggregates data, possibly with additional processing.

Currently, **no final battery authority is declared** because:

- BMS model, firmware, and wiring are not yet confirmed with manufacturer evidence.
- Inverter battery measurement point relative to BMS is not verified.
- SolarMAN aggregation method for battery is not documented.

### PV Production

Three distinct measurements exist:

| Measurement | Source | Type | Use case |
|---|---|---|---|
| PV DC power (MPPT) | Inverter telemetry (`potencia_cc_pv1_w`, `potencia_cc_pv2_w`) | DC, panel side | Technical diagnostics, MPPT performance, shading analysis |
| PV AC power (inverter output) | Inverter telemetry (`potencia_total_ca_w`) | AC, post-inversion | Net production delivered to AC bus |
| Plant flow production | SolarMAN (`flow_potencia_produccion_w`) | AC, aggregated | Operational overview, may include corrections |

These three measurements represent **different physical points** in the system and must not be used interchangeably without explicit conversion accounting for inverter efficiency.

---

## Sign Convention Profile (Conceptual Design)

### PowerSignProfile — Conceptual Contract

Each signal requires a versioned, evidence-backed sign profile before normalization.

| Field | Type | Description |
|---|---|---|
| `canonical_field` | string | e.g. `flow_grid_w`, `telemetry_battery_power_w` |
| `source_system` | string | `solarman_plant_flow`, `inverter_telemetry` |
| `measurement_point` | string | Physical location (grid meter, inverter port, BMS, MPPT) |
| `unit` | string | `W` |
| `positive_means` | string | `import`, `export`, `charge`, `discharge`, `generation`, `consumption`, `unknown` |
| `negative_means` | string | Inverse of positive |
| `zero_means` | string | `no_flow`, `unknown` |
| `status` | enum | `confirmed`, `provisional`, `unknown` |
| `evidence_source` | string | Private data window description (redacted), manufacturer manual, installer confirmation |
| `profile_version` | semver | Version of this sign profile |
| `valid_from` | datetime | When this profile becomes effective |
| `valid_to` | datetime or null | Expiration or invalidation date |
| `notes` | string | Limitations, inverter firmware version, context |

### Direction Vocabulary

**Grid:**
- `import` — power flows from grid to premises (purchase).
- `export` — power flows from premises to grid (delivery/injection).
- `bidirectional_net` — single net signal where sign indicates direction per profile.
- `unknown` — direction not determined.

**Battery:**
- `charge` — power flows into battery (increasing SOC).
- `discharge` — power flows out of battery (decreasing SOC).
- `bidirectional_net` — single net signal.
- `unknown` — direction not determined.

**PV and consumption:**
- `generation` — power produced by PV panels or inverter.
- `consumption` — power consumed by loads.
- `unsigned_magnitude` — always ≥0, no sign needed.
- `unknown` — direction not determined.

### Mandatory Rules

1. **`status = unknown` forbids normalization.** No energy calculation permitted.
2. **`status = provisional` forbids fiscal presentation.** Must be clearly marked as estimated.
3. **`status = confirmed` requires evidence.** Human gate with documented observation window.
4. **Do not infer sign from energy balance.** A residual does not prove direction.
5. **Do not reuse a profile across signals.** Each `canonical_field` requires its own profile.
6. **Profile must be versioned and linked to plant/source.** Changes to firmware or wiring may invalidate it.
7. **Profile changes must be recorded with timestamps.** Historical analyses using an old profile remain valid for that period.

---

## Directional Normalized Contract (Conceptual Design)

When sign profiles are confirmed, power signals will be normalized into directional magnitudes:

| Normalized field | Type | Constraint | Meaning |
|---|---|---|---|
| `grid_import_w` | float or None | ≥ 0 | Power imported from grid |
| `grid_export_w` | float or None | ≥ 0 | Power exported to grid |
| `battery_charge_w` | float or None | ≥ 0 | Power charging the battery |
| `battery_discharge_w` | float or None | ≥ 0 | Power discharging from battery |
| `pv_generation_w` | float or None | ≥ 0 | PV generation power |
| `load_consumption_w` | float or None | ≥ 0 | Consumption/load power |

### Principles

1. **Always preserve the raw value and its original sign.** Normalized fields are additions, not replacements.
2. **Never represent import as a negative number** in a "grid power" variable — use `grid_import_w ≥ 0`.
3. **Never represent export as a positive of the same net variable** — use `grid_export_w ≥ 0`.
4. **Never have both import and export positive simultaneously** for the same net signal and sample.
5. **Never have both charge and discharge positive simultaneously** for the same net signal and sample.
6. **Measured zero is preserved as zero** in the appropriate directional field.
7. **Unknown sign produces `unavailable` state, not zero.** All directional fields remain None.
8. **Conversion must record `profile_version` and `lineage`** (which profile was applied, when).
9. **Normalization function must be pure** — same input + same profile = same output.

---

## Temporal Integration Contract (Conceptual Design)

### What Each Sample Means

The temporal semantics of the data must be determined before choosing an integration method. Current unknowns:

| Unknown | SolarMAN flow | Inverter telemetry |
|---|---|---|
| Sample nature | Unknown: instantaneous read, interval average, or held value | Unknown: instantaneous read, interval average, or held value |
| Sampling interval | Nominally 5 min, not guaranteed (gaps observed) | Nominally 5 min, not guaranteed |
| Timestamp meaning | Unknown: start, end, or center of interval | Unknown: start, end, or center of interval |
| Order guarantee | Not guaranteed by source system | Not guaranteed by source system |
| Zero-duration handling | Not applicable (single timestamp per row) | Not applicable |

### Integration Methods Under Consideration

The choice of integration method depends on evidence about temporal semantics:

| Method | Formula | When appropriate | Evidence needed |
|---|---|---|---|
| Left rectangular | `E = P(t₁) × (t₂ − t₁)` | Timestamp marks interval start | Source documentation confirming "sample captures value at timestamp" |
| Right rectangular | `E = P(t₂) × (t₂ − t₁)` | Timestamp marks interval end | Source documentation confirming same |
| Trapezoidal | `E = (P(t₁) + P(t₂)) × (t₂ − t₁) / 2` | Samples are instantaneous readings at known times | Known sample timing + no sawtooth artifacts |
| Sample-and-hold | `E = P × hold_duration` | Signal is held until next update | Evidence of register/SCADA hold behavior |
| Interval average | `E = P_avg × Δt` | Source provides average over interval | Explicit column or documentation for power average |

**U2.0 does not select a method.** U2.1 will select after gathering evidence about sample semantics.

### General Integration Formula

```
energy_wh = integral(power_w dt) / 3600
```

For discrete samples:

```
energy_wh = Σ method(p_i, p_{i+1}, Δt_i) / 3600
```

Where `method` depends on source semantics and is selected per signal.

### Edge Cases

| Case | Handling |
|---|---|
| First sample in window | May not have valid Δt (no predecessor). Document integration method for first point. |
| Last sample in window | Same consideration. |
| Repeated timestamps | Exclude zero-duration intervals. Flag in quality. |
| Out-of-order timestamps | Reject the sample or sort-by-timestamp with lineage note. |
| None/NaN/Inf values | Exclude the interval. Do not interpolate. |
| Zero-duration intervals | Exclude. Flag as `excluded_zero_duration`. |

---

## Gap Treatment Policy

### Default Principle

**Do not interpolate or assume constant power across an unauthorized gap.**

### Explicit States

| State | Meaning |
|---|---|
| `observed` | Valid sample, valid interval, energy computed |
| `missing` | Sample absent at expected timestamp |
| `excluded_nonfinite` | Sample exists but value is NaN, Inf, or None |
| `excluded_zero_duration` | Consecutive samples share same timestamp |
| `excluded_unconfirmed_sign` | Sample exists but sign cannot be resolved |
| `excluded_alignment` | Timestamp misalignment exceeds tolerance |
| `not_applicable` | Period outside valid range or signal not supported |

### Energy Separation

Future energy results must separate:

- `energy_wh_observed` — energy from valid, integrated intervals.
- `observed_duration` — sum of validated interval durations.
- `expected_duration` — total duration of the analysis window.
- `coverage_fraction = observed_duration / expected_duration` (0 to 1).
- `missing_duration` — sum of gap durations.
- `excluded_duration` — sum of excluded-interval durations.
- `interval_count` — total intervals considered.
- `excluded_interval_count` — intervals excluded for any reason.

**Do not scale observed energy to "fill" 100 % of the period.** A coverage of 80 % means 80 % of the expected duration has data — the remaining 20 % is unknown, not zero.

---

## Conceptual Energy Result Models

### EnergyInterval (U2.1/U2.2)

| Field | Type | Description |
|---|---|---|
| `start` | datetime | Interval start (UTC) |
| `end` | datetime | Interval end (UTC) |
| `duration` | timedelta | `end − start` |
| `source_field` | string | Canonical field name |
| `raw_start_power_w` | float or None | Power at interval start (raw value) |
| `raw_end_power_w` | float or None | Power at interval end (raw value) |
| `normalized_direction` | string or None | `import`, `export`, `charge`, `discharge`, `generation`, `consumption` |
| `integration_method` | string | Method used (e.g. `trapezoidal`) |
| `energy_wh` | float | Integrated energy |
| `status` | string | `observed`, `missing`, `excluded_*` |
| `sign_profile_version` | string or None | Which PowerSignProfile was applied |
| `lineage` | list[str] | Transformation chain |
| `quality_flags` | dict | Per-interval quality markers |

### EnergySummary (U2.1/U2.2)

| Field | Type | Description |
|---|---|---|
| `period_start` | datetime | Summary window start |
| `period_end` | datetime | Summary window end |
| `source` | string | `flow`, `telemetry`, `merged` |
| `direction` | string | Directional category |
| `observed_energy_wh` | float | Sum of observed interval energies |
| `observed_energy_kwh` | float | Convenience: `observed_energy_wh / 1000` |
| `expected_duration` | timedelta | Total window duration |
| `observed_duration` | timedelta | Sum of observed interval durations |
| `missing_duration` | timedelta | Sum of gap durations |
| `coverage_fraction` | float | `observed_duration / expected_duration` |
| `interval_count` | int | Total intervals processed |
| `excluded_interval_count` | int | Intervals excluded |
| `sign_profile_version` | string or None | Active PowerSignProfile version |
| `warnings` | list[str] | Coverage issues, sign uncertainties |

---

## Physical Balances — Preconditions

### Balance Validity Requirements

A global energy balance equation will only be valid when:

1. All signals belong to **compatible physical points** in the system.
2. **AC vs DC** is identified for each signal.
3. All **signs are normalized** via confirmed PowerSignProfile.
4. All **timestamps are aligned** to a common axis.
5. **Losses and efficiencies** are accounted for (inverter, wiring, BMS).
6. All **units are compatible** (W for instantaneous, Wh for integrated).

### Currently Prohibited Balances

Do not directly mix in a single balance equation:

- PV DC power (`telemetry_pv_power_w`) with AC load consumption.
- Net grid power (`flow_grid_w`) without sign normalization.
- Battery power (`telemetry_battery_power_w`) without confirmed sign convention.
- Signals with different timestamps or alignment qualities.

**Do not use the balance residual to automatically decide a signal's sign convention.**

---

## Human Gate Procedure for Sign Confirmation

### Purpose

Confirm sign conventions using private data windows without altering inverter settings.

### Grid Sign Gate

**Windows to search (private data):**
- Nighttime with approximately zero PV.
- Known household consumption (positive, measurable).
- Battery stable (not charging/discharging, SOC steady).
- Grid meter or utility app showing active import.

**Simultaneous comparison:**
- `flow_grid_w` (SolarMAN plant flow).
- `telemetry_grid_power_w` (inverter).
- Battery state (flow and telemetry SOC).
- Consumption (flow and telemetry).
- Available official source (meter reading).

**Outcome:**
- `confirmed` — observation matches expected physical behavior.
- `inconclusive` — ambiguous due to noise, low values, or timing.
- `contradictory` — signals disagree beyond tolerance.

### Battery Sign Gate

**Windows to search:**
- Solar charging period (morning, PV active, SOC rising).
- Nighttime discharge (PV zero, SOC falling, known load).
- Battery idle (no appreciable power, SOC stable).

**Simultaneous comparison:**
- `flow_battery_w` (SolarMAN).
- `telemetry_battery_power_w` (inverter).
- SOC variation (ΔSOC over window, confirming direction).
- Inverter/BMS state.

**Conditions:**
- Do NOT change inverter parameters.
- Do NOT force charge or discharge.
- Do NOT cause grid disconnection.
- Do NOT share raw private exports in Git.
- Record only redacted conclusions and hashes when applicable.

### Outcome Recording

The result of each human gate procedure SHALL be recorded as:
- `confirmed` — with redacted evidence reference and timestamp.
- `inconclusive` — documenting why the window was insufficient.
- `contradictory` — documenting the contradiction and blocking normalization.

---

## U2 Implementation Plan

| Sub-phase | Goal | Depends on |
|---|---|---|
| **U2.1** | PowerSignProfile contract implementation; sign normalization functions (pure); directional field computation | U2.0 human gates for sign confirmation |
| **U2.2** | Generic temporal integration W→Wh; integration method selection per source semantics; EnergyInterval model | U2.1 sign normalization |
| **U2.3** | Grid metrics: grid_import_wh, grid_export_wh, hourly/daily grid profiles | U2.2 integration |
| **U2.4** | Battery metrics: battery_charge_wh, battery_discharge_wh, SOC-derived energy | U2.2 integration |
| **U2.5** | PV production and consumption metrics; hourly/daily profiles | U2.2 integration |
| **U2.6** | Coverage analysis, aggregations (hourly/daily/weekly), percentile profiles | U2.3–U2.5 metrics |
| **U2.7** | Reconciliation, cross-validation with cumulative energy counters, U2 QA | U2.3–U2.6 |

---

## Exclusion Notes

U2.0 does NOT:
- Modify CanonicalSample fields.
- Create new Python modules for energy calculation.
- Compute any Wh or kWh values.
- Create directional power fields in production code.
- Implement balance equations.
- Connect to tariffs, billing, or economic models.
- Create frontend visualizations or endpoints.

These are U2.1–U2.7 activities.

---

## Unknowns and Deferred Decisions

| Unknown | Deferred to | Reason |
|---|---|---|
| Sample temporal semantics (instantaneous vs average) | U2.1 | Requires source documentation or experimental validation |
| Integration method selection | U2.2 | Depends on temporal semantics |
| Grid sign convention for Casabero | Human gate | Requires private data observation |
| Battery sign convention for Casabero | Human gate | Requires private data observation |
| BMS accuracy and model | U2.4 | May need manufacturer confirmation |
| Inverter efficiency curve | U2.5 | Required for DC→AC conversion if needed |
| CT clamp placement and accuracy | Human gate | Installation-specific |
| Whether cumulative energy counters can serve as integration validation | U2.7 | Requires counter reset behavior documented |

---

## References

- `solgreen/timeline/canonical.py` — CanonicalSample model (lines 1–76).
- `solgreen/timeline/join.py` — join_by_tolerance and _pv_power (lines 1–115).
- `solgreen/contracts/plant_flow.py` — PlantFlowSample (lines 1–48).
- `solgreen/contracts/inverter_telemetry.py` — SIGNAL_SPECS, InverterTelemetrySample (lines 1–1273).
- `solgreen/importer/parsers/solarman_flow.py` — Flow parser (lines 1–93).
- `solgreen/importer/parsers/solarman_telemetry.py` — Telemetry parser (lines 1–134).
- `docs/domain/FOUNDATIONS.md` — Domain foundations (power/energy, sign conventions).
- `docs/domain/DATA_CONTRACTS.md` — Data contracts.
- `docs/domain/data-dictionary/solarman-plant-flow.md` — Plant flow dictionary.
- `docs/domain/data-dictionary/solarman-inverter-telemetry.md` — Inverter telemetry dictionary.
- `docs/domain/data-dictionary/afinia-billing.md` — Billing dictionary.
- `config/plant-profiles/casabero.example.yaml` — Plant profile (example).
- `config/grid-profiles/colombia-split-phase-review-required.yaml` — Grid profile (pending review).
