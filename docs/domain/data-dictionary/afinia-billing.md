# Diccionario de datos — Facturación Afinia y economía energética

## Propósito

Definir los contratos mínimos para calcular, proyectar y conciliar facturas sin acoplar la lógica a un recibo, municipio, estrato o periodo específico.

Los valores históricos incluidos en fixtures privados sirven para regresión. No son tarifas vigentes.

## Reglas generales

- Moneda: `COP`.
- Energía: `kWh`.
- Potencia: `W` o `kW`.
- Montos monetarios: enteros en centavos de COP cuando se persisten.
- Fechas de vigencia: intervalo semiabierto `[valid_from, valid_to)`.
- Toda tarifa debe citar una fuente y una versión.
- Ningún límite subsidiable, porcentaje o CU se hardcodea en el motor.
- El recibo oficial y el medidor fiscal tienen prioridad sobre SolarMAN para conciliación económica.

## `TariffProfile`

Perfil versionado utilizado por el motor de facturación.

| Campo | Tipo | Requerido | Descripción |
|---|---|---:|---|
| `id` | UUID | sí | Identificador interno. |
| `provider` | string | sí | Comercializador, por ejemplo `afinia`. |
| `profile_version` | semver | sí | Versión del contrato. |
| `status` | enum | sí | `draft`, `verified`, `expired`, `historical_reference`. |
| `currency` | string | sí | Siempre `COP` para este perfil. |
| `valid_from` | date | sí | Inicio de vigencia. |
| `valid_to` | date/null | no | Fin exclusivo. |
| `territory` | object | sí | Departamento, municipio y zona tarifaria cuando aplique. |
| `customer_segment` | object | sí | Estrato, uso, altitud o clasificación aplicable. |
| `energy_charge_cop_per_kwh` | decimal | sí | CU del periodo. |
| `subsidy_policy` | object/null | no | Regla aplicable al bloque subsidiable. |
| `non_energy_charges` | array | no | Aseo, alumbrado, ajustes y otros cargos parametrizados. |
| `rounding_policy` | object | sí | Escala y momento del redondeo. |
| `source` | object | sí | Documento, URL o hash, fecha de consulta y autoridad. |
| `notes` | array[string] | no | Limitaciones y contexto. |

### `SubsidyPolicy`

| Campo | Tipo | Descripción |
|---|---|---|
| `method` | enum | `discount_per_kwh`, `protected_rate`, `percentage`, `none`. |
| `eligible_limit_kwh` | decimal/null | Máximo de energía elegible. |
| `discount_cop_per_kwh` | decimal/null | Diferencia monetaria aplicable. |
| `protected_rate_cop_per_kwh` | decimal/null | Tarifa protegida alternativa. |
| `percentage` | decimal/null | Porcentaje cuando la fuente lo defina así. |
| `eligibility_source` | object | Fuente y versión de la regla. |

Solo uno de los mecanismos debe ser autoridad en una ejecución. El parser de recibo puede inferir valores observados, pero debe marcarlos como `observed`, no como norma vigente.

### `NonEnergyChargeRule`

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | string | `waste_collection`, `public_lighting`, `adjustment`, etc. |
| `calculation_type` | enum | `fixed`, `percentage`, `observed_only`, `external`. |
| `amount_cop_cents` | integer/null | Monto fijo. |
| `rate` | decimal/null | Tasa cuando aplique. |
| `source` | object | Autoridad y vigencia. |

## `InvoiceDocument`

Representación normalizada de un recibo cargado.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador interno. |
| `file_hash_sha256` | string | Hash del original. |
| `provider` | string | Comercializador observado. |
| `billing_cycle_id` | UUID | Ciclo asociado. |
| `issue_date` | date/null | Fecha de emisión. |
| `due_date` | date/null | Fecha límite. |
| `meter_id_redacted` | string/null | Medidor redactado. |
| `account_id_redacted` | string/null | Cuenta o NIC redactado. |
| `observed_total_cop_cents` | integer | Total facturado. |
| `parser_version` | semver | Versión del extractor. |
| `parse_confidence` | decimal | 0 a 1. |
| `review_status` | enum | `unreviewed`, `reviewed`, `rejected`. |

El archivo original no se envía completo al LLM.

## `BillingCycle`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador. |
| `plant_id` | string | Planta asociada. |
| `period_start_local` | datetime | Inicio inclusivo. |
| `period_end_local` | datetime | Fin exclusivo. |
| `timezone` | string | Zona local. |
| `days` | decimal | Duración real. |
| `meter_reading_start_kwh` | decimal/null | Lectura fiscal inicial. |
| `meter_reading_end_kwh` | decimal/null | Lectura fiscal final. |
| `billed_energy_kwh` | decimal/null | Energía oficial del recibo. |
| `tariff_profile_id` | UUID/null | Perfil aplicado. |
| `status` | enum | `open`, `projected`, `closed`, `reconciled`. |

## `InvoiceLine`

| Campo | Tipo | Descripción |
|---|---|---|
| `line_id` | UUID | Identificador. |
| `invoice_id` | UUID | Recibo. |
| `code` | string | Código canónico. |
| `label_observed` | string | Texto original. |
| `quantity` | decimal/null | Cantidad observada. |
| `unit` | string/null | `kWh`, `%`, etc. |
| `unit_rate` | decimal/null | Tarifa observada. |
| `amount_cop_cents` | integer | Importe. |
| `sign` | enum | `charge` o `credit`. |
| `epistemic_level` | enum | `measured`, `normalized`, `calculated`. |
| `source_location` | object | Página, región o línea del documento. |

Códigos iniciales:

- `energy_gross`;
- `energy_subsidy`;
- `energy_subtotal`;
- `waste_collection`;
- `public_lighting`;
- `previous_balance`;
- `adjustment`;
- `other_charge`;
- `invoice_total`.

## `BillingEstimate`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador. |
| `cycle_id` | UUID | Ciclo proyectado o cerrado. |
| `analysis_run_id` | UUID | Ejecución reproducible. |
| `tariff_profile_id` | UUID | Perfil usado. |
| `estimated_import_kwh` | decimal | Energía estimada. |
| `energy_gross_cop_cents` | integer | Cargo bruto. |
| `subsidy_cop_cents` | integer | Crédito calculado. |
| `energy_subtotal_cop_cents` | integer | Subtotal. |
| `non_energy_charges_cop_cents` | integer | Otros cargos. |
| `estimated_total_cop_cents` | integer | Total P50. |
| `p10_total_cop_cents` | integer/null | Límite bajo. |
| `p90_total_cop_cents` | integer/null | Límite alto. |
| `coverage_score` | decimal | 0 a 1. |
| `confidence_score` | decimal | 0 a 1. |
| `assumptions` | array | Supuestos explícitos. |
| `calculation_trace` | array | Fórmula, inputs y redondeos. |

## `BillingReconciliation`

| Campo | Tipo | Descripción |
|---|---|---|
| `estimate_id` | UUID | Estimación reproducida sobre ciclo cerrado. |
| `invoice_id` | UUID | Recibo oficial. |
| `estimated_energy_kwh` | decimal | Importación integrada. |
| `billed_energy_kwh` | decimal | Energía facturada. |
| `energy_delta_kwh` | decimal | Diferencia. |
| `energy_delta_pct` | decimal/null | Diferencia relativa. |
| `estimated_total_cop_cents` | integer | Total estimado. |
| `observed_total_cop_cents` | integer | Total oficial. |
| `amount_delta_cop_cents` | integer | Diferencia. |
| `candidate_explanations` | array | Hipótesis determinísticas. |
| `status` | enum | `within_tolerance`, `review`, `unreconciled`. |
| `human_review` | object/null | Revisión y conclusión. |

## `HourlyEnergyProfile`

| Campo | Tipo | Descripción |
|---|---|---|
| `plant_id` | string | Planta. |
| `window_start` | datetime | Inicio del periodo agregado. |
| `window_end` | datetime | Fin. |
| `local_hour` | integer | 0 a 23. |
| `day_class` | enum | `all`, `weekday`, `weekend`, `holiday`. |
| `sample_days` | integer | Días cubiertos. |
| `coverage_score` | decimal | Cobertura. |
| `load_kwh_mean` | decimal | Consumo medio. |
| `pv_kwh_mean` | decimal | Producción media. |
| `grid_import_kwh_mean` | decimal | Compra media. |
| `grid_export_kwh_mean` | decimal | Exportación media. |
| `battery_charge_kwh_mean` | decimal | Carga media. |
| `battery_discharge_kwh_mean` | decimal | Descarga media. |
| `soc_start_pct_mean` | decimal/null | SOC inicial medio. |
| `soc_end_pct_mean` | decimal/null | SOC final medio. |
| `p50_load_w` | decimal/null | Potencia P50. |
| `p90_load_w` | decimal/null | Potencia P90. |
| `p95_load_w` | decimal/null | Potencia P95. |
| `max_load_w` | decimal/null | Máximo observado. |

## `ApplianceProfile`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador. |
| `plant_id` | string | Planta. |
| `name` | string | Nombre legible. |
| `category` | string | Aire, lavadora, bomba, etc. |
| `rated_power_w` | decimal/null | Potencia declarada. |
| `startup_power_w` | decimal/null | Pico de arranque. |
| `duration_minutes` | integer/null | Duración típica. |
| `interruptible` | boolean | Puede interrumpirse. |
| `supervision_required` | boolean | Requiere presencia. |
| `allowed_windows` | array | Horarios permitidos. |
| `priority` | integer | Prioridad doméstica. |
| `source` | enum | `user_declared`, `smart_plug`, `circuit_meter`, `estimated`. |
| `confidence_score` | decimal | Confianza. |

## `LoadRecommendation`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador. |
| `appliance_id` | UUID/null | Equipo o clase de carga. |
| `valid_for_date` | date | Vigencia. |
| `recommended_start` | datetime | Inicio sugerido. |
| `recommended_end` | datetime | Fin sugerido. |
| `avoid_windows` | array | Ventanas críticas. |
| `expected_grid_delta_kwh` | object | P10/P50/P90. |
| `expected_cost_delta_cop_cents` | object | P10/P50/P90. |
| `expected_soc_delta_pct` | object/null | Impacto estimado. |
| `constraints_applied` | array | Reserva, potencia, confort, supervisión. |
| `evidence_refs` | array[string] | Evidencias existentes. |
| `confidence_score` | decimal | 0 a 1. |
| `status` | enum | `active`, `expired`, `dismissed`, `accepted`. |

## Prohibiciones de contrato

- No representar COP como `float` persistido.
- No mezclar potencia y energía.
- No asumir que SolarMAN equivale al medidor fiscal.
- No reutilizar un perfil vencido sin marcarlo explícitamente.
- No inferir el electrodoméstico desde una curva agregada como hecho.
- No ocultar supuestos ni reglas de redondeo.
