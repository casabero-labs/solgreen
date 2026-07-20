from __future__ import annotations

from solgreen.diagnostics.rule import Rule

SEED_RULES: list[Rule] = [
    Rule(
        rule_id="DATA-001",
        version="1.0.0",
        name="Intervalo ausente",
        category="data",
        question="¿Hay huecos de telemetría superiores al umbral esperado?",
        signals_required=("timestamp_axis",),
        base_severity="low",
        parameters={"max_gap_minutes": 30},
        known_false_positives=("Parada programada del inversor.",),
    ),
    Rule(
        rule_id="BAT-001",
        version="1.0.0",
        name="SOC bajo",
        category="battery",
        question="¿El SOC de la batería está por debajo del umbral crítico?",
        signals_required=("flow_soc_pct",),
        signals_optional=("telemetry_soc_pct",),
        base_severity="medium",
        parameters={"soc_threshold_pct": 20},
        known_false_positives=("Batería en modo de mantenimiento.",),
    ),
    Rule(
        rule_id="PV-001",
        version="1.0.0",
        name="Dropout FV con voltaje presente",
        category="pv",
        question="¿La potencia FV cae a cero mientras el voltaje MPPT sigue presente?",
        signals_required=("telemetry_pv_power_w",),
        signals_optional=(
            "flow_potencia_produccion_w",
            "telemetry_pv_voltage_v",
        ),
        base_severity="medium",
        parameters={"min_voltage_v": 100},
        known_false_positives=("Nublado transitorio extremo.",),
    ),
    Rule(
        rule_id="GRID-003",
        version="1.0.0",
        name="Pérdida de red",
        category="grid",
        question="¿Los voltajes de red caen a cero indicando un outage?",
        signals_required=("telemetry_grid_power_w",),
        signals_optional=("flow_grid_w",),
        base_severity="high",
        parameters={"voltage_threshold_v": 10},
        known_false_positives=("Mantenimiento programado del transformador.",),
    ),
    Rule(
        rule_id="INV-002",
        version="1.0.0",
        name="Waiting prolongado",
        category="inverter",
        question="¿El inversor permanece en estado waiting más allá del umbral?",
        signals_required=("telemetry_inverter_state",),
        base_severity="medium",
        parameters={"max_waiting_minutes": 60},
        known_false_positives=("Espera de autorización de conexión del distribuidor.",),
    ),
]


class RuleCatalog:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self._rules: dict[str, Rule] = {}
        source = rules if rules is not None else SEED_RULES
        for rule in source:
            self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> Rule | None:
        return self._rules.get(rule_id)

    def list_rules(self) -> list[Rule]:
        return list(self._rules.values())

    def list_by_category(self, category: str) -> list[Rule]:
        return [r for r in self._rules.values() if r.category == category]
