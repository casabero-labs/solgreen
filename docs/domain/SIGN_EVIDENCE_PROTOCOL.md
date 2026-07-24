# Private Sign-Evidence Protocol

## Purpose

Define a reproducible, privacy-preserving protocol for collecting evidence
about the sign convention of bidirectional power signals in a solar plant.

The protocol produces **per-field decisions** — `confirmed`, `provisional`,
`inconclusive`, or `contradictory` — based on private, reproducible evidence
only.

The protocol is **generic**. It must not contain real conclusions for any
specific plant. Each plant runs the protocol separately, against its own
private exports, and only the owner of the plant can authorize a
`confirmed` decision.

## Scope

The protocol applies to bidirectional signals of type `power_w`:

- grid flow (`flow_grid_w`)
- inverter telemetry grid (`telemetry_grid_power_w`)
- battery flow (`flow_battery_w`)
- inverter telemetry battery (`telemetry_battery_power_w`)

Each field is decided **independently**. Two signals may measure different
physical points, use opposite sign conventions, apply different filters, or
carry different offsets. Reusing a conclusion from one signal to another is
**forbidden**.

## Privacy Boundary

All private evidence MUST live under git-ignored paths:

```
data/private/<protocol_id>/
reports/private/<protocol_id>/
```

These paths must already be listed in `.gitignore`. Before any copy:

```sh
git check-ignore -v data/private/<protocol_id>/
git check-ignore -v reports/private/<protocol_id>/
```

If either command does not confirm gitignore coverage, **stop and report
the gap** before continuing.

Private artifacts must NEVER contain:

- original file names of private exports
- absolute paths on the host
- host usernames
- inverter serial numbers
- physical addresses
- customer account or contract numbers
- credentials of any kind
- screenshots or images
- manual excerpts
- exact timestamps row by row
- detailed occupancy patterns
- kWh, Wh, or any cumulative energy values

Public artifacts may only mention **opaque IDs**, **SHA-256 hashes**,
**daypart descriptions**, **sample counts**, and **aggregate conclusions**.

## Inputs

### Mandatory

At minimum, the protocol requires:

- at least one export of plant flow from SolarMAN
- at least one export of inverter telemetry
- overlapping temporal windows between the two sources
- timestamps with known timezone or explicit local-time interpretation

### Desirable (strengthens evidence, but not required)

- meter or official app observation during grid import
- SolarMAN capture during a known grid event
- battery state-of-charge log
- installer confirmation of CT placement, wiring, or measurement point
- inverter or BMS manual documenting sign convention

If mandatory inputs are absent, the protocol MUST NOT invent a decision.

## Manifest

Every run produces an `evidence_manifest.json` with **opaque IDs only**:

```json
{
  "protocol_id": "u2_1b",
  "execution_mode": "private_analysis",
  "data_class": "private|real|synthetic",
  "plant_decision_scope": "none|casabero|<other>",
  "casabero_evidence": "unavailable|available",
  "profile_decisions_authorized": false,
  "evidence": [
    {
      "evidence_id": "opaque-uuid-1",
      "logical_type": "flow|telemetry|meter_observation|manual|installer_note",
      "sha256": "full hex sha256",
      "byte_size": 0,
      "temporal_range_utc": {"start": "iso", "end": "iso"},
      "interpreted_timezone": "iana name or explicit UTC offset",
      "parser": "module.symbol",
      "row_count": 0,
      "quality_observations": ["short string", "..."]
    }
  ]
}
```

The manifest is private. It must never be committed, pushed, or rendered in
public CI artifacts.

## Using Existing Contracts

The protocol **must reuse existing Solgreen contracts**. Do not write a
parallel parser.

- Plant flow: `solgreen.importer.parsers.solarman_flow` (CSV / XLSX)
- Inverter telemetry: `solgreen.importer.parsers.solarman_telemetry` (CSV / XLSX)
- Sample alignment: `solgreen.timeline.join` and `CanonicalSample`

Parsers are **read-only**. The protocol must not modify production parsers
while gathering evidence.

## Window Selection

The protocol identifies candidate windows per gate type:

### Grid import

- production approximately zero
- load positive
- battery stable, idle, or in a known direction
- grid available
- external observation available if possible

### Grid export

- production greater than load
- battery possibly charging
- external observation available if possible
- the protocol MUST NOT provoke an export event

### Battery charge

- state-of-charge increasing
- production or known source active
- battery signal with stable sign
- duration enough to distinguish real variation from noise
- no manual configuration changes

### Battery discharge

- state-of-charge decreasing
- load positive
- production low or zero
- battery signal with stable sign
- no simultaneous known charge

### Battery idle

- state-of-charge approximately stable
- battery power close to zero
- enough consecutive samples
- idle windows characterize noise, deadband, and flow vs telemetry
  discrepancy; they MUST NOT confirm charge or discharge by themselves

Every selection criterion must be **explicit and reproducible** in the
private report. No hidden thresholds.

## Independence

Each of the four fields receives its own decision:

- `flow_grid_w`
- `telemetry_grid_power_w`
- `flow_battery_w`
- `telemetry_battery_power_w`

Reusing a conclusion between fields is forbidden.

## Minimum Evidence

To propose `confirmed` for a bidirectional signal, the protocol requires:

- at least three valid windows per direction
- at least two distinct days when data allows
- stable sign within each window
- no material contradiction
- independent physical confirmation: state-of-charge, official meter,
  inverter or BMS state, or documented manual

This rule may be **tightened** in a given run. It must never be silently
**relaxed**.

If either direction lacks evidence, the field decision is `provisional` or
`inconclusive`. **Never `confirmed`.**

A technical manual may complement missing windows, but only when:

- the manual matches the exact model
- the manual documents the exact variable
- the manual states sign and measurement point
- the manual is referenced by title, version, and hash
- the manual is **not** a generic web capture

## Decision Outcomes

| Outcome      | When                                                                                                          |
|--------------|----------------------------------------------------------------------------------------------------------------|
| `confirmed`     | both directions are observed with stable sign, no contradictions, independent confirmation, point identified |
| `provisional`   | one direction strongly observed, the other direction inferred only from a complementary source               |
| `inconclusive`  | few windows, noisy data, missing SOC, insufficient alignment, no independent confirmation                    |
| `contradictory` | same sign appears for opposite physical states, or flow contradicts telemetry contradicts confirmation    |

`contradictory` blocks both registration and normalization.

## Temporal Semantics

The protocol may record observations about cadence and structure:

- nominal cadence
- Δt distribution
- consecutive repetitions
- duplicate timestamps
- retained values
- possible interval averages
- available cumulative fields

The protocol MUST NOT decide a temporal integration method:

- left rectangle
- right rectangle
- trapezoidal
- sample-and-hold
- interval average

That decision belongs to a later phase.

## Window Hashing

For each valid window:

1. sort samples by timestamp
2. serialize only the columns actually used
3. use a deterministic format
4. compute SHA-256
5. record the hash in the private report

Public artifacts may mention:

- opaque window ID (e.g. `EW-GRID-IMPORT-001`)
- SHA-256 hash
- general daypart (morning, night, etc.)
- sample count
- aggregate conclusion

Public artifacts MUST NOT include exact timestamps, row-by-row values,
occupancy patterns, original files, or serials.

## Per-Field Decision Table

The private report must include:

| Field | Positive means | Negative means | Outcome | Evidence | Blockers |

The `Outcome` column holds one of:

- `confirmed`
- `provisional`
- `inconclusive`
- `contradictory`
- `not_assessed` — only when evidence is unavailable (e.g. synthetic-only run)

`not_assessed` is reserved for runs that do not have real evidence. It is
NOT a real decision.

## Human Gate

A `confirmed` or `provisional` decision is **never** automatic. The owner
of the plant must approve each field explicitly. Without explicit approval:

- no public gate report
- no profile YAML
- no modification of the production registry
- no entry into the next phase

## Public Gate Report

Only after explicit human approval, the protocol allows the creation of:

```
docs/qa_reports/U2_SIGN_EVIDENCE_GATE_<YYYY-MM-DD>.md
```

The gate report must contain only:

- gate state
- fields evaluated
- approved outcome per field
- opaque window IDs
- SHA-256 hashes
- window count
- general dayparts
- supporting sources
- limitations
- authorized profiles for future materialization
- blocked profiles
- explicit human gate approval
- next phase

The gate report must NEVER contain raw values, exact timestamps, serials,
addresses, or any item classified under the privacy boundary above.

## Rollback

A run is fully reversible by removing the contents of:

```
data/private/<protocol_id>/
reports/private/<protocol_id>/
```

No profile has been materialized. No production parser has changed. The
git history is unaffected.

## Anti-Patterns

The protocol explicitly forbids:

- inferring one direction from the opposite of the other
- using energy balance as a substitute for sign observation
- using the canonical model to decide physical sign
- interpolating missing samples
- fabricating values
- accepting a sign because the alternative was never observed
- disabling AFCI, protections, or inverter controls
- forcing charge, discharge, grid export, or islanding
- triggering events to capture evidence
- reading values off a screenshot of the official app
- trusting a generic web capture as a manual reference

## Status of This Document

This protocol is generic. It is valid for any plant that runs it. The
outcomes for the Casabero plant in particular are documented only in the
private report and, after owner approval, in the corresponding public gate
report.

If a future change to this protocol changes decision criteria, the change
is documented through a new revision of this file and a fresh protocol run.