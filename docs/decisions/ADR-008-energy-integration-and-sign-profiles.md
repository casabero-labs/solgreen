# ADR-008 — Energy Integration and Sign Profiles

## Status

**Proposed** — pending human gate sign confirmation and temporal semantics evidence.

## Context

Solgreen currently has:

- `CanonicalSample` with 7 power/energy-related fields storing instantaneous
  power values in Watts (W).
- Two data sources: SolarMAN plant flow (12 columns, ~5 min sampling) and
  inverter telemetry (120 columns, ~5 min sampling).
- No sign profile: all grid and battery power signals preserve their
  original sign convention without normalization.
- No temporal integration: all values are in W; no Wh or kWh calculation.
- Authority hierarchy documented but not enforced: SolarMAN is operational,
  Afinia fiscal meter is authoritative for billing.
- FOUNDATIONS.md declares canonical directional conventions
  (`grid_import_w ≥ 0`, `grid_export_w ≥ 0`, `battery_charge_w ≥ 0`,
  `battery_discharge_w ≥ 0`) but no implementation exists.
- U1 quality system validates ordering, gaps, plausibility, and
  cross-source consistency (SOC only), but does not evaluate energy
  semantics.

The project must now move from instantaneous power data to integrated
energy metrics without introducing false assumptions about sign, direction,
or temporal semantics.

## Decision

### 1. Sign Profiles Are Versioned Contracts

Each power signal that carries a bidirectional net value MUST have a
declared `PowerSignProfile` before normalization.

The profile declares:

- Which canonical field it applies to.
- What measurement point the signal represents.
- What positive values mean and what negative values mean.
- What evidence supports the declaration.
- What version applies and when it became valid.

A profile with `status = unknown` forbids normalization. A profile
with `status = provisional` forbids fiscal presentation. Only
`status = confirmed` with cited evidence allows normalization and
energy calculation.

### 2. Directional Magnitudes Do Not Replace Raw Values

Directional fields (`grid_import_w ≥ 0`, `grid_export_w ≥ 0`,
`battery_charge_w ≥ 0`, `battery_discharge_w ≥ 0`) are **derived**
fields that coexist with raw net fields.

- The raw value and its sign are always preserved.
- Import is never represented as a negative number in a "grid power" variable.
- Export is never represented as a positive of the same net variable.
- Import and export cannot both be positive for the same net signal at
  the same timestamp (instantaneous net cannot both import and export).
- Charge and discharge follow the same mutual-exclusion rule.

### 3. Temporal Integration Depends on Source Semantics

Energy (Wh) is the time integral of power (W):

```
energy_wh = Σ method(p_i, p_{i+1}, Δt_i) / 3600
```

The integration `method` (left rectangular, right rectangular,
trapezoidal, sample-and-hold, or interval average) depends on what
each sample represents temporally: instantaneous reading, interval
average, or held value.

U2.0 does **not** select the method. U2.1 will select after gathering
evidence about temporal semantics of each source. Until then, no Wh
or kWh values are produced.

### 4. Gaps Are Not Interpolated

Gaps in the timeline produce states: `observed`, `missing`,
`excluded_nonfinite`, `excluded_zero_duration`,
`excluded_unconfirmed_sign`, `excluded_alignment`.

Missing energy is **not** estimated by scaling observed energy to
fill the period. Coverage is measured as:

```
coverage_fraction = observed_duration / expected_duration
```

A coverage of 0 means no energy is computed. A coverage of 0.8 means
80 % of the window has observed energy — the remaining 20 % is unknown.

### 5. No Physical Balance Without Preconditions

A global energy balance equation will only be computed when:

- All signals belong to compatible physical points.
- AC vs DC is identified.
- All signs are normalized with confirmed profiles.
- Timestamps are aligned.
- Losses and efficiencies are accounted for.

Until all conditions are met, do not compute residual balances or
use residuals to infer sign conventions.

### 6. Authority Hierarchy

| Use case | Primary authority | Operational source |
|---|---|---|
| Grid import/export (fiscal) | Fiscal meter + official invoice | SolarMAN, inverter |
| Battery state and flow | BMS (to be confirmed) | Inverter, SolarMAN |
| PV production | MPPT measurements (DC), inverter output (AC) | SolarMAN plant flow |
| Load consumption | Load-side measurements | Inverter telemetry |

SolarMAN and inverter data are **operational estimates**. They do not
substitute the fiscal meter for billing, regulatory reporting, or
subsidy calculations.

### 7. Do Not Infer Sign From Balance

A residual in an energy balance equation is evidence of uncertainty,
not evidence of sign convention error. Sign conventions require
independent evidence from windows of known physical behavior.

### 8. Energy Accumulators as Validation

The inverter telemetry contains cumulative energy counters:

- `alimentacion_acumulada_de_red_kwh` — cumulative grid export.
- `energia_adquirida_acumulada_kwh` — cumulative grid import.
- `energia_de_carga_total_kwh` — cumulative battery charge.
- `energia_de_descarga_total_kwh` — cumulative battery discharge.
- `produccion_acumulada_kwh` — cumulative AC production.
- `consumo_total_kwh` — cumulative consumption.

These counters MAY serve as validation references for integrated
energy, but MUST first be verified for:

- Counter reset behavior (daily, manual, overflow).
- Registration accuracy vs. direct measurement.
- Agreement with instantaneous power measurements.

## Rationale

### Why Not Normalize Signs Now

The sign of `flow_grid_w` is documented as "negative may equal import"
in the data dictionary, but this has not been confirmed against a
private observation window with known physical behavior. Normalizing
without evidence would propagate errors through all downstream
energy calculations.

### Why Directional Fields Are Additive, Not Replacements

Preserving raw values ensures:

- Analyses remain reprodudible with future profile versions.
- Contradictions between profiles can be detected and investigated.
- Historical data can be re-normalized when profiles are corrected.

### Why Temporal Semantics Matter

If samples represent instantaneous readings at the timestamp, a
trapezoidal rule is appropriate. If samples represent an average over
the preceding 5-minute interval, a left-rectangular rule (or direct
use) is appropriate. Using the wrong method introduces systematic
energy bias that accumulates over hours and days.

### Why Gaps Are Not Filled

Linear interpolation assumes constant rate of change across the gap.
Sample-and-hold assumes the last known value persists. Both
assumptions can be wrong during events (dropouts, surges, mode
changes) and would hide the very phenomena Solgreen is designed to
detect.

## Consequences

### Positive

- Clear contract for when energy calculation is safe.
- Versioned sign profiles enable reproducible analysis and re-normalization.
- Directional magnitudes prevent sign ambiguity in reports and visualizations.
- Gap policy ensures missing data is explicit, not hidden.
- Authority hierarchy prevents operational data from being presented as fiscal.

### Negative

- Energy metrics are blocked until human gates confirm sign conventions.
- Additional modeling and test burden for PowerSignProfile and normalization.
- Temporal semantics investigation may delay integration.
- Physical balances deferred until all preconditions met.

### Neutral

- CanonicalSample fields for raw power values remain unchanged.
- Quality system (U1) continues operating on instantaneous power signals.
- Episode detection (U3) uses instantaneous power, not energy.

## Alternatives Considered

### Normalize signs by assuming SolarMAN convention

**Rejected.** The data dictionary says "puede usar signo negativo para
compra" — this is not a confirmed convention. Assuming it would
silently propagate errors.

### Use cumulative energy counters directly

**Rejected.** Cumulative counters may have different reset behavior,
accuracy, and synchronization than instantaneous power. They are
validation targets, not primary integration sources.

### Interpolate gaps with linear or last-known-value

**Rejected.** Would hide dropout events, grid losses, and battery
transitions — exactly the phenomena U3 is designed to detect.

### Allow sign inference from balance residual

**Rejected.** A residual can indicate many things: sign error,
measurement error, timing misalignment, unmodeled losses, or
unmeasured load. It does not uniquely identify sign convention error.

## Human Gates

The following gates MUST be passed before U2.1 sign normalization begins:

1. **Grid sign gate:** Private observation window confirming
   `flow_grid_w` sign convention (night, zero PV, known load).
2. **Battery sign gate:** Private observation window confirming
   `flow_battery_w` and `telemetry_battery_power_w` sign conventions
   (charge from PV, discharge at night).
3. **Temporal semantics gate:** Source documentation or experimental
   evidence on what each sample timestamp represents (instantaneous,
   average, held value).
4. **Measurement point gate:** Confirmation of CT clamp placement,
   inverter measurement point, and BMS-to-inverter wiring.

Without these gates, no sign normalization or energy integration
shall proceed.

## References

- `docs/domain/ENERGY_SEMANTICS.md` — Complete signal inventory and semantics.
- `docs/domain/FOUNDATIONS.md` — Domain foundations (power, energy, sign conventions).
- `docs/domain/data-dictionary/solarman-plant-flow.md` — Plant flow dictionary.
- `docs/domain/data-dictionary/solarman-inverter-telemetry.md` — Inverter telemetry dictionary.
- `solgreen/timeline/canonical.py` — CanonicalSample implementation.
- `solgreen/timeline/join.py` — join_by_tolerance and field mapping.
- `solgreen/contracts/plant_flow.py` — PlantFlowSample contract.
- `solgreen/contracts/inverter_telemetry.py` — InverterTelemetrySample and SIGNAL_SPECS.
- `solgreen/importer/parsers/solarman_flow.py` — Flow parser (no sign normalization).
- `config/plant-profiles/casabero.example.yaml` — Plant profile.
