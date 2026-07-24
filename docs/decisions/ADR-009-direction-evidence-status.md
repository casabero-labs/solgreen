# ADR-009 — Per-Direction Evidence Status in PowerSignProfile

## Status

**Accepted** — implements asymmetric evidence in `PowerSignProfile` and
re-anchors normalization to the per-direction gate. The contractual
decision was accepted. Runtime activation is pending: `effective_from`
must be supplied by the operator or deployment configuration at cutover
time. The code contains no reference to the private evidence window.

## Context

ADR-008 introduced `PowerSignProfile` with a single `profile.status`
(CONFIRMED / PROVISIONAL / UNKNOWN) as the gate for normalization.
This made `profile.status` an all-or-nothing flag that collapsed two
independent questions into one:

- "Is the meaning of positive raw values owner-anchored?"
- "Is the meaning of negative raw values owner-anchored?"

The D1.0 SOLARMAN telemetry upgrade produced real evidence that exposes
this collapse concretely:

- T_A_P_O_G (total grid active power) has `n=4` private samples aligned
  with `ST_PG1='Purchasing energy'` (ap=4). The negative direction is
  owner-anchored: **import is confirmed**.
- T_A_P_O_G has `n=0` positive samples aligned with `ST_PG1='Selling
  energy'`. The positive direction is unanchored: **export is deferred**
  until a natural authorized export event occurs.

Under the previous schema, the only schema-valid ways to express this
state were:

- **Option A — keep `profile.status=CONFIRMED`** for both directions:
  rejected by validator (`_validate_confirmed_directions_not_unknown`)
  because positive_means=UNKNOWN is forbidden for non-PV/non-LOAD fields.
- **Option B — use `profile.status=PROVISIONAL`** for the whole profile:
  accepted by the schema, but `normalize_power_value` short-circuits to
  `PROFILE_NOT_CONFIRMED` for **every** event, including the
  already-confirmed import direction. This loses a known-good capability.

Neither option expresses the actual evidence state. Both directions of
evidence are independent; the schema forces them to be co-dependent.

## Decision

Introduce per-direction evidence status.

### 1. New enum

```python
class DirectionEvidenceStatus(StrEnum):
    NOT_ASSESSED = "not_assessed"   # no anchor collected for this direction
    PROVISIONAL = "provisional"     # anchor present but not yet confirmed
    CONFIRMED = "confirmed"         # owner-anchored, normalize this direction
    CONTRADICTED = "contradicted"   # anchor contradicts the assigned meaning
```

### 2. New fields on `PowerSignProfile`

```python
positive_evidence_status: DirectionEvidenceStatus | None = None
negative_evidence_status: DirectionEvidenceStatus | None = None
```

Both default to `None` for backward compatibility. A model validator
derives them when not explicitly set.

### 3. `profile.status` is now administrative only

`profile.status` (CONFIRMED / PROVISIONAL / UNKNOWN) remains on the model
for documentation, owner-review gating, and tooling. It is **not** the
gate for normalization. The actual gate is per-direction.

Additional administrative invariant: a profile with
`profile.status=UNKNOWN` cannot claim `positive_evidence_status=CONFIRMED`
or `negative_evidence_status=CONFIRMED`. The `_validate_unknown_status_directions`
validator enforces this — if any per-direction evidence is explicitly
CONFIRMED, the administrative state must be PROVISIONAL or CONFIRMED.

### 4. Backward-compat derivation

When `positive_evidence_status` / `negative_evidence_status` is `None`:

| direction        | profile.status | derived `*_evidence_status` |
|------------------|----------------|------------------------------|
| `UNKNOWN`        | (any)          | `NOT_ASSESSED`               |
| (known)          | `CONFIRMED`    | `CONFIRMED`                  |
| (known)          | `PROVISIONAL`  | `PROVISIONAL`                |
| (known)          | `UNKNOWN`      | `NOT_ASSESSED`               |

This preserves the previous behavior of all existing profiles in
`registry_seeds.py` and existing test fixtures without manual edits.

### 5. Combination validator

After derivation, the validator `_validate_direction_evidence_combination`
enforces the cross-product:

- `direction = UNKNOWN` requires `evidence_status ∈ {NOT_ASSESSED, PROVISIONAL}`.
- `direction ≠ UNKNOWN` requires `evidence_status ∈ {PROVISIONAL, CONFIRMED, CONTRADICTED}`.
- `direction = UNKNOWN` + `evidence_status = CONFIRMED` is rejected
  (a "confirmed" UNKNOWN would mean we confirmed a meaning of UNKNOWN).
- `direction ≠ UNKNOWN` + `evidence_status = NOT_ASSESSED` is rejected
  (a known meaning implies some evidence must exist).

The previous validator `_validate_confirmed_directions_not_unknown` is
removed. Its job is now done by the combination validator and the
asymmetric CONFIRMED + UNKNOWN case is allowed when the UNKNOWN
direction's evidence is `NOT_ASSESSED` (or `PROVISIONAL`).

### 6. Normalization contract

`normalize_power_value` no longer short-circuits on `profile.status`.
The per-field normalizers consult the per-direction evidence:

```text
if |raw| <= zero_deadband_w:
    raw_power_w = raw          (PRESERVED — never mutated)
    status      = NORMALIZED
    within_zero_deadband = True
    applicable magnitudes forced to 0.0
    warnings include "within zero deadband"
elif raw > 0:
    direction = positive_means
    direction_status = positive_evidence_status
elif raw < 0:
    direction = negative_means
    direction_status = negative_evidence_status
if direction == UNKNOWN or direction_status != CONFIRMED:
    return PROFILE_NOT_CONFIRMED
else:
    return NORMALIZED with the corresponding magnitude populated
```

#### 6.1. Raw observation vs. normalized output

The normalizer MUST preserve the original observation in
`DirectionalPowerResult.raw_power_w`. The contract is:

- `raw_power_w` = the value reported by the source (never mutated).
- `grid_import_w`, `grid_export_w`, etc. = the **normalized** outputs.
- Within the deadband, `raw_power_w` is preserved (e.g., 3.0 W) but the
  applicable directional magnitudes are forced to 0.0; the
  `within_zero_deadband` flag and a `warnings` entry make this explicit.
- Outside the deadband, `raw_power_w` equals the input value and the
  directional magnitudes match its absolute value (modulo the
  per-direction gate).

Consumers must treat `raw_power_w` as the immutable observation and the
directional magnitudes as the normalized projection.

#### 6.2. CONTRADICTED never normalizes

A direction marked `CONTRADICTED` is never normalized: the gate
`direction_status != CONFIRMED` is true, so the result is
`PROFILE_NOT_CONFIRMED`. CONTRADICTED is reserved for evidence that
contradicts the assigned meaning (e.g., a profile that says positive
means GRID_EXPORT but the evidence shows positive means GRID_IMPORT in
the same regime).

#### 6.3. Deadband flag and validator bypass

`DirectionalPowerResult` carries a `within_zero_deadband: bool = False`
field. When `True`:

- `raw_power_w` is preserved (the original observation).
- Applicable directional magnitudes are forced to `0.0`.
- The magnitude-conservation validator is bypassed (the deadband
  consumes the magnitude; direction is undetermined).
- The `profile_status=CONFIRMED` invariant is bypassed (the deadband
  path does not consult per-direction evidence).

When `False`:

- `profile_status` must be CONFIRMED.
- Magnitudes must conserve `abs(raw_power_w)` exactly.

### 7. Temporal semantics

The proposal does NOT define a default cutover timestamp.
`registry_d10_proposal.py` exposes:

```python
def build_updated_profiles(
    *, effective_from: datetime
) -> dict[str, PowerSignProfile]:
    """Build the four authoritative PowerSignProfile instances.

    `effective_from` is REQUIRED. It must be a timezone-aware datetime
    (UTC offset set). Naive datetimes and None are rejected; the
    function never invents a cutover timestamp.
    """
```

`UPDATED_PROFILES` are **templates** (no `valid_from` field). The builder
is the only construction path. Promotion requires the operator to:

1. Choose a real cutover timestamp `T` approved by the operator.
2. Call `build_updated_profiles(effective_from=T)`.
3. Register the returned profiles in the production registry after
   closing the existing ones with `valid_to=T`.

The proposal never proposes, suggests, or hardcodes a cutover date.
Doing so would be a contract violation: only the operator can authorize
the actual cutover.

## Consequences

### Positive

- Asymmetric profiles express the real evidence state.
- The D1.0 grid profile can be promoted with `status=CONFIRMED`
  (administrative) and asymmetric per-direction evidence. Negative raw
  values normalize as `GRID_IMPORT`; positive raw values return
  `PROFILE_NOT_CONFIRMED` until export is anchored.
- Existing profiles in `registry_seeds.py` continue to work without
  modification (derivation handles backward compat).
- No new global status (CONFIRMED_PARTIAL) is needed.
- `raw_power_w` is never mutated; consumers can rely on it as the
  immutable observation.
- The cutover timestamp is supplied explicitly, not invented.

### Negative / Risks

- The contract for `INVALID_UNSIGNED_NEGATIVE` is narrowed: it no longer
  triggers automatically for any negative raw on unsigned fields. Tests
  that asserted on it (`test_pv_negative_rejected`,
  `test_load_negative_rejected`) are updated to assert on
  `PROFILE_NOT_CONFIRMED`. The status remains defined for future use.
- `_validate_confirmed_directions_not_unknown` is removed. Tests that
  asserted on it are updated to assert on the new combination validator
  (UNKNOWN direction + CONFIRMED evidence rejected).
- `DirectionalPowerResult` gains a `within_zero_deadband` flag. The
  validator treats the two paths (within-deadband vs. outside-deadband)
  differently. Consumers that check `raw_power_w != 0.0` to determine
  "real zero" must also check `within_zero_deadband`.
- `profile.status=UNKNOWN` now has stricter per-direction evidence
  compatibility (no per-direction=CONFIRMED allowed).
- Consumers downstream of `normalize_power_value` must understand
  per-direction semantics. As of this ADR, no such consumer exists in
  `solgreen/` (audit confirmed in `registry_d10_proposal.py::CONSUMER
  AUDIT`), so the blast radius is bounded.

## Alternatives considered

- **Introduce a new global `ProfileStatus.CONFIRMED_PARTIAL` value.**
  Rejected: contract-breaking, and the new status would carry
  information that already lives in the per-direction fields.
- **Promote only positive evidence, keep `status=PROVISIONAL`.**
  Rejected: forces ALL events (including confirmed import) to
  `PROFILE_NOT_CONFIRMED`. Loses a known-good capability.
- **Promote only positive evidence, keep `status=CONFIRMED`, accept
  the validator rejection.** Rejected: schema-invalid; breaks the
  integrity of `PowerSignProfile` for everyone.
- **Invent a default `EFFECTIVE_FROM` constant at module level.**
  Rejected: only the operator can authorize the cutover. A module-level
  constant would be a contract violation per the temporal semantics
  above. The builder pattern enforces explicit operator authorization.

## References

- ADR-008 — Energy Integration and Sign Profiles (predecessor contract).
- `solgreen/energy/sign_profiles.py` — schema implementation.
- `solgreen/energy/normalization.py` — normalization implementation.
- `solgreen/energy/registry_d10_proposal.py` — D1.0 proposal that
  motivated this ADR (grid profile is the canonical asymmetric case).
- `docs/domain/ENERGY_SEMANTICS.md` — directional conventions.