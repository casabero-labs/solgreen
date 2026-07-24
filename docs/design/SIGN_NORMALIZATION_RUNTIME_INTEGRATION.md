# Sign Normalization — Integración Runtime

## Estado pre-PR

- Código de biblioteca mergeado en `develop/solgreen-unified` (ex-PR #27):
  - `solgreen/energy/sign_profiles.py` — `PowerSignProfile`, `PowerSignProfileRegistry`, enums.
  - `solgreen/energy/registry_seeds.py` — `build_telemetry_sign_profile_registry()`, `build_production_sign_profile_registry()`.
  - `solgreen/energy/normalization.py` — `normalize_power_value()`, `DirectionalPowerResult`.
  - `solgreen/energy/registry_d10_proposal.py` — 4 perfiles D1.0 con evidencia por dirección.
  - `docs/decisions/ADR-009-direction-evidence-status.md` — Accepted.
- **No existe ningún caller runtime de `normalize_power_value`.**
- El pipeline de importación (`_parse_single_file` en `cli.py:126`) no invoca normalización.
- Este diseño cubre **exclusivamente** la integración runtime. No toca la biblioteca existente.

---

## 1. Modo de tres estados

```python
# solgreen/importer/normalize.py

from enum import StrEnum

class SignNormalizationMode(StrEnum):
    OFF = "off"
    LEGACY = "legacy"
    D10 = "d10"
```

| Modo   | Construye registry | Ejecuta normalización | Conserva comportamiento actual |
|--------|---------------------|------------------------|--------------------------------|
| OFF    | No                  | No                     | Sí (byte-identical)            |
| LEGACY | `build_telemetry_sign_profile_registry()` | Sí (4 perfiles legacy) | No                              |
| D10    | `build_production_sign_profile_registry(effective_from=...)` | Sí (8 perfiles con cutover) | No |

No se aceptan strings desconocidos.

---

## 2. Matriz estricta de configuración

| Modo   | effective_from presente | Resultado                        |
|--------|-------------------------|----------------------------------|
| OFF    | Sí                      | **Error de configuración**       |
| OFF    | No                      | Válido                           |
| LEGACY | Sí                      | **Error de configuración**       |
| LEGACY | No                      | Válido                           |
| D10    | No                      | **Error de configuración**       |
| D10    | Sí, naive               | **Error de configuración**       |
| D10    | Sí, timezone-aware      | Válido                           |

No se ignora silenciosamente ninguna variable sobrante.

---

## 3. ImportNormalizationContext

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ImportNormalizationContext:
    sign_registry: PowerSignProfileRegistry | None  # None solo en modo OFF
    registry_mode: SignNormalizationMode
    effective_from: datetime | None                  # None excepto en D10
    plant_id: str
```

- No usa `Any`.
- No es singleton.
- No usa estado global.
- Construido una vez por ejecución del comando `import`.

---

## 4. Ubicación de imports

```python
# Desde sign_profiles.py:
from solgreen.energy.sign_profiles import (
    CanonicalPowerField,
    PowerSignProfileRegistry,
    SourceSystem,
)

# Desde registry_seeds.py:
from solgreen.energy.registry_seeds import (
    build_production_sign_profile_registry,
    build_telemetry_sign_profile_registry,
)
```

El código nuevo reside en `solgreen/importer/normalize.py` (no en `solgreen/energy/`), evitando cualquier riesgo de import circular con submódulos de `solgreen.energy`.

---

## 5. Construcción única por comando

```
CLI import command
  → parse options (--sign-normalization-mode, --sign-registry-effective-from)
  → build_normalization_context()  ← UNA sola llamada
  → loop: _parse_single_file(file, plant_id, repo, norm_ctx)
    → parse file → samples
    → if norm_ctx.mode != OFF: normalize_telemetry_signals(samples, norm_ctx)
    → quality → summarize → build batch → return
```

No se construye el registry por archivo ni por muestra.

---

## 6. Mapping inicial: 3 señales raw

Solo señales realmente presentes en `InverterTelemetrySample.signals`:

| raw_signal_name                     | canonical_field                    | source_system            | unit |
|-------------------------------------|------------------------------------|--------------------------|------|
| `potencia_de_bateria_w`             | `TELEMETRY_BATTERY`                | `INVERTER_TELEMETRY`     | W    |
| `total_active_power_of_the_grid_w`  | `TELEMETRY_GRID`                   | `INVERTER_TELEMETRY`     | W    |
| `pv_total_charging_power_w`         | `TELEMETRY_PV`                     | `INVERTER_TELEMETRY`     | W    |

**Verificación de contrato** (contra `SIGNAL_SPECS` en `inverter_telemetry.py:866,518,378`):
- `potencia_de_bateria_w`: index=85, `SignalKind.POWER_W`, unit=`"W"` ✅
- `total_active_power_of_the_grid_w`: index=50, `SignalKind.POWER_W`, unit=`"W"` ✅
- `pv_total_charging_power_w`: index=36, `SignalKind.POWER_W`, unit=`"W"` ✅

**No se normalizan todavía:**
- `PlantFlow` (ni `FLOW_CONSUMO` ni `FLOW_PRODUCCION` ni `FLOW_GRID` ni `FLOW_BATTERY`).
- `E_Puse_t1`, `B_C1`, `DP1`, `DP2`, `C_P_L1`, `C_P_L2`, `UAP1`, `UAP2`.
- Campos expresados en kWh.

---

## 7. Binding tipado (no tuplas)

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class SignalBinding:
    raw_signal_name: str
    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    expected_unit: Literal["W"]

TELEMETRY_SIGNAL_BINDINGS: tuple[SignalBinding, ...] = (
    SignalBinding(
        raw_signal_name="potencia_de_bateria_w",
        canonical_field=CanonicalPowerField.TELEMETRY_BATTERY,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
    SignalBinding(
        raw_signal_name="total_active_power_of_the_grid_w",
        canonical_field=CanonicalPowerField.TELEMETRY_GRID,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
    SignalBinding(
        raw_signal_name="pv_total_charging_power_w",
        canonical_field=CanonicalPowerField.TELEMETRY_PV,
        source_system=SourceSystem.INVERTER_TELEMETRY,
        expected_unit="W",
    ),
)
```

---

## 8. Modelado de resultados

### NormalizedSignalResult

```python
from pydantic import BaseModel, ConfigDict

class NormalizedSignalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_field: CanonicalPowerField
    source_system: SourceSystem
    timestamp_utc: datetime
    raw_signal_name: str
    normalization: DirectionalPowerResult
```

Nota: `source_type` del diseño original es redundante — `source_system` ya codifica la fuente (telemetry vs. flow). Se omite.

### NormalizationSummary

```python
from pydantic import BaseModel, ConfigDict, Field

class NormalizationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    eligible_count: int          # samples × |TELEMETRY_SIGNAL_BINDINGS| = intentos de normalización
    missing_count: int           # MISSING_VALUE (raw_power_w is None)
    result_count: int            # eligible_count - missing_count
    normalized_count: int        # NORMALIZED
    not_confirmed_count: int     # PROFILE_NOT_CONFIRMED
    not_found_count: int         # PROFILE_NOT_FOUND
    error_count: int             # NONFINITE_VALUE + FIELD_MISMATCH + any unexpected
    warning_count: int           # not_confirmed_count + not_found_count

    @property
    def invariant_holds(self) -> bool:
        return (
            self.eligible_count
            == self.missing_count
            + self.normalized_count
            + self.not_confirmed_count
            + self.not_found_count
            + self.error_count
        ) and (self.result_count == self.eligible_count - self.missing_count)
```

No se usa el nombre `total_signals_normalized` para resultados no normalizados.

---

## 9. Política de resultados

| NormalizationStatus   | Acción                                          | Contador             |
|-----------------------|-------------------------------------------------|----------------------|
| NORMALIZED            | Conservar `raw_power_w` + magnitudes direccionales | `normalized_count`   |
| PROFILE_NOT_CONFIRMED | Conservar raw + warnings; continuar import      | `not_confirmed_count`, `warning_count` |
| PROFILE_NOT_FOUND     | Conservar resultado; continuar import           | `not_found_count`, `warning_count`     |
| MISSING_VALUE         | **No** crear `NormalizedSignalResult`           | `missing_count`      |
| NONFINITE_VALUE       | Conservar resultado; incrementar error_count    | `error_count`        |
| FIELD_MISMATCH        | Conservar resultado; incrementar error_count    | `error_count`        |

- `FIELD_MISMATCH` en los tres bindings autorizados solo puede ocurrir por bug (los pares field/source son compatibles por contrato).
- Señales no mapeadas simplemente no son elegibles para normalización.
- El import **no se aborta** por errores de normalización en esta primera versión.

---

## 10. Persistencia inicial (solo reportes)

### JSON (`*.import.json`)

Se añade una key `"normalization"` al payload:

```json
{
  "batch": { ... },
  "validity": { ... },
  "normalization": {
    "summary": { ... NormalizationSummary ... },
    "mode": "legacy",
    "effective_from": null,
    "results": [ ... ]   // resultados completos (NormalizedSignalResult[])
  }
}
```

- `"normalization"` se omite completamente cuando `mode == OFF` (regresión byte-identical).
- `"results"` contiene el array completo. Si resulta demasiado grande (>10k entradas), se puede escribir como artefacto separado `*.normalization.json` y referenciar con un path relativo. El límite se define como constante `MAX_INLINE_NORMALIZATION_RESULTS = 10_000`.

### Markdown (`*.import.md`)

Se añade una sección `## Sign Normalization` **solo cuando mode != OFF**:

```markdown
## Sign Normalization

- Mode: `legacy`
- Effective from: (none)
- Eligible: 300
- Missing: 12
- Results: 288
- Normalized: 275
- Not confirmed: 8
- Not found: 3
- Errors: 2
- Warnings: 11
- Invariant: OK

### Warning details (sample, max 20)

| Signal               | Timestamp                    | Status                  | Detail                      |
|----------------------|------------------------------|-------------------------|-----------------------------|
| total_active_power.. | 2026-07-21T16:20:00+00:00   | profile_not_confirmed   | negative_means not CONFIRMED |
| ...                  | ...                          | ...                     | ...                         |
```

- Constante `MAX_MD_WARNING_DETAILS = 20`.
- No se incluyen resultados completos en Markdown.

### No se modifica:
- Base de datos.
- Migraciones.
- Esquema SQL.

---

## 11. CLI

```bash
solgreen import -f telemetry.csv \
  --sign-normalization-mode legacy                    # default: off

solgreen import -f telemetry.csv \
  --sign-normalization-mode d10 \
  --sign-registry-effective-from 2026-08-01T00:00:00Z
```

| Flag                                  | Env var                              | Default | Válido con            |
|---------------------------------------|--------------------------------------|---------|-----------------------|
| `--sign-normalization-mode`           | `SOLGREEN_SIGN_NORMALIZATION_MODE`   | `off`   | siempre               |
| `--sign-registry-effective-from`      | `SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM` | —    | solo `mode=d10`       |

Ambas flags pasan por una única función `build_normalization_context()` que valida la matriz de configuración.

**Variable de entorno mapeada:**
```python
sign_normalization_mode_env = os.environ.get("SOLGREEN_SIGN_NORMALIZATION_MODE")
sign_registry_effective_from_env = os.environ.get("SOLGREEN_SIGN_REGISTRY_EFFECTIVE_FROM")
```

---

## 12. Plan de pruebas

### 12.1 Configuración (`tests/unit/test_importer/test_normalize_config.py`)

| ID     | Descripción                                | Esperado                     |
|--------|--------------------------------------------|------------------------------|
| CFG-01 | Default OFF preserva comportamiento        | context.mode == OFF, registry is None |
| CFG-02 | Modo inválido (`"invalid"`)                | `ValueError`                 |
| CFG-03 | OFF con `effective_from`                   | `ValueError`                 |
| CFG-04 | LEGACY con `effective_from`                | `ValueError`                 |
| CFG-05 | D10 sin `effective_from`                   | `ValueError`                 |
| CFG-06 | D10 con `effective_from` naive             | `ValueError`                 |
| CFG-07 | D10 con `effective_from` timezone-aware    | context válido, registry != None |
| CFG-08 | LEGACY sin `effective_from`                | context válido, registry != None |

### 12.2 Dependency Injection (`tests/unit/test_importer/test_normalize_context.py`)

| ID     | Descripción                                          |
|--------|------------------------------------------------------|
| DI-01  | Registry se construye una vez por `build_normalization_context()` |
| DI-02  | Dos llamadas consecutivas producen instancias distintas |
| DI-03  | Múltiples archivos reutilizan el mismo contexto       |
| DI-04  | No existe estado global entre tests (no `module`-level singleton) |

### 12.3 Mapping (`tests/unit/test_importer/test_normalize_bindings.py`)

| ID     | Descripción                                          |
|--------|------------------------------------------------------|
| MAP-01 | Solo 3 señales en `TELEMETRY_SIGNAL_BINDINGS`        |
| MAP-02 | Todas declaran `expected_unit == "W"`                |
| MAP-03 | Cada `SignalBinding.canonical_field` ∈ `_TELEMETRY_FIELDS` |
| MAP-04 | Cada `SignalBinding.source_system == INVERTER_TELEMETRY` |
| MAP-05 | `raw_signal_name` existe en `CANONICAL_NAME_TO_INDEX` |
| MAP-06 | `is_power_field_source_compatible` retorna True para cada binding |
| MAP-07 | Supporting signals (`B_C1`, `DP1`, etc.) no aparecen en bindings |
| MAP-08 | `FLOW_CONSUMO` no tiene binding de telemetría        |

### 12.4 Pipeline (`tests/unit/test_importer/test_normalize_pipeline.py`)

| ID     | Descripción                                          |
|--------|------------------------------------------------------|
| PIP-01 | Batería positiva (discharge) → NORMALIZED, battery_discharge_w poblado |
| PIP-02 | Batería negativa (charge) → NORMALIZED, battery_charge_w poblado |
| PIP-03 | Grid negativo (import) → NORMALIZED, grid_import_w poblado |
| PIP-04 | Grid positivo (export) → PROFILE_NOT_CONFIRMED (legacy export not assessed) |
| PIP-05 | PV positivo (generation) → NORMALIZED, pv_generation_w poblado |
| PIP-06 | PV negativo → PROFILE_NOT_CONFIRMED (legacy negative=UNKNOWN) |
| PIP-07 | Muestras mixtas antes y después del cutover (D10) → resuelve perfil correcto por timestamp |
| PIP-08 | Cada muestra usa su propio `timestamp_utc` para `registry.resolve()` |
| PIP-09 | `raw_power_w is None` → MISSING_VALUE, no crea `NormalizedSignalResult` |
| PIP-10 | Deadband (±5W) → NORMALIZED con `within_zero_deadband=True` |
| PIP-11 | `raw_power_w` preservado en `NormalizedSignalResult.normalization.raw_power_w` |
| PIP-12 | Contadores del summary cumplen invariantes |
| PIP-13 | 100 samples × 3 bindings → eligible_count == 300 |
| PIP-14 | `result_count == eligible_count - missing_count` |
| PIP-15 | Muestra con solo 2 de 3 señales presentes → 2 results + 1 missing |

### 12.5 Regresión (`tests/unit/test_cli.py` cambios en tests existentes)

| ID     | Descripción                                          |
|--------|------------------------------------------------------|
| REG-01 | `--sign-normalization-mode off` (default) → JSON/MD byte-idénticos a actual |
| REG-02 | Sin flag `--sign-normalization-mode` → mismos outputs que versión actual |
| REG-03 | Parsers CSV/XLSX no cambian su output               |
| REG-04 | Quality analysis no cambia                           |
| REG-05 | Reportes antiguos con `normalization_summary` ausente son válidos |
| REG-06 | `_parse_single_file` con `norm_ctx=None` → sin normalización |

---

## 13. No hacer

- No implementar carga de `FLOW_CONSUMO`.
- No modificar base de datos ni crear migraciones.
- No configurar Coolify.
- No seleccionar `effective_from` (es input del operador/deploy).
- No mezclar con PR #27 (el código de biblioteca ya está mergeado).
- No crear commits en esta sesión.
- No usar `total_signals_normalized` como nombre para contadores no normalizados.

---

## 14. Resumen de archivos involucrados

### Nuevos

| Archivo                                  | Contenido                                          |
|------------------------------------------|----------------------------------------------------|
| `solgreen/importer/normalize.py`         | `SignNormalizationMode`, `SignalBinding`, `TELEMETRY_SIGNAL_BINDINGS`, `ImportNormalizationContext`, `NormalizedSignalResult`, `NormalizationSummary`, `build_normalization_context()`, `normalize_telemetry_signals()` |

### Modificados

| Archivo                        | Cambio                                                       |
|--------------------------------|--------------------------------------------------------------|
| `solgreen/cli.py`              | Nuevos flags CLI; `_parse_single_file` acepta `norm_ctx`     |
| `solgreen/importer/reporter.py`| `write_report_json`/`write_report_markdown` extienden reportes |
| `solgreen/importer/__init__.py`| Exportar símbolos públicos de `normalize.py` (opcional)       |

### No modificados

| Archivo                                | Razón                                |
|----------------------------------------|--------------------------------------|
| `solgreen/energy/sign_profiles.py`     | Biblioteca ya mergeada               |
| `solgreen/energy/registry_seeds.py`    | Biblioteca ya mergeada               |
| `solgreen/energy/normalization.py`     | Biblioteca ya mergeada               |
| `solgreen/energy/registry_d10_proposal.py` | Biblioteca ya mergeada            |
| `solgreen/contracts/inverter_telemetry.py` | Contrato inalterado               |
| `solgreen/db/`                         | Sin cambios de esquema               |
| `solgreen/timeline/`                   | Normalización es pre-timeline         |
| `solgreen/quality/`                    | Sin cambios                          |

---

## 15. Riesgos identificados

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| JSON demasiado grande con resultados inline (>10k entradas) | Media | Constante `MAX_INLINE_NORMALIZATION_RESULTS` + artefacto separado |
| Romper regresión OFF por campo nuevo en JSON | Alta | `"normalization"` key se omite completamente en modo OFF |
| `from __future__ import annotations` en `inverter_telemetry.py` puede interferir con `get_type_hints` en tests de binding | Baja | Verificación estática en `TELEMETRY_SIGNAL_BINDINGS` no requiere runtime type hints |
| `normalize_power_value` tiene validación estricta de `timestamp_utc` timezone-aware | Baja | `InverterTelemetrySample.timestamp_utc` ya es UTC por contrato del parser |
| Overhead de normalización para archivos grandes (100k+ rows) | Media | 3 llamadas por muestra son O(n); el registry.resolve es O(p) con p=4 u 8 perfiles. Aceptable para primera versión. |

---

## 16. Veredicto

**READY_FOR_NEW_PR.** El diseño es completo, autoconsistente, y verificado contra la base de código existente. Todos los puntos del usuario están cubiertos. Las tres señales fueron verificadas contra `SIGNAL_SPECS` (todas `POWER_W`, unidad `W`). No hay conflictos con la biblioteca mergeada.

---

## 17. Siguiente prompt recomendado

```
Aplicar diseño de integración runtime de sign normalization.
Crear rama feat/sign-normalization-runtime desde develop/solgreen-unified.
Implementar en orden:
  1. solgreen/importer/normalize.py (modelos + binding + contexto)
  2. tests/unit/test_importer/test_normalize_config.py (CFG-01 a CFG-08)
  3. tests/unit/test_importer/test_normalize_bindings.py (MAP-01 a MAP-08)
  4. tests/unit/test_importer/test_normalize_pipeline.py (PIP-01 a PIP-15)
  5. solgreen/cli.py (flags + integración en _parse_single_file)
  6. solgreen/importer/reporter.py (extensión JSON + MD)
  7. tests de regresión (REG-01 a REG-06)
  8. ruff check + mypy + pytest
No modificar base de datos ni Coolify.
```
