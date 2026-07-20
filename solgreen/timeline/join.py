from datetime import timedelta
from typing import Annotated

from pydantic import Field

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.timeline.canonical import CanonicalSample

DEFAULT_TOLERANCE: Annotated[timedelta, Field(description="Mitad del intervalo de muestreo de 5 min.")] = timedelta(minutes=2, seconds=30)


def join_by_tolerance(
    flow_samples: list[PlantFlowSample],
    telemetry_samples: list[InverterTelemetrySample],
    *,
    tolerance: timedelta = DEFAULT_TOLERANCE,
) -> list[CanonicalSample]:
    sorted_flow = sorted(flow_samples, key=lambda s: s.timestamp_utc)
    sorted_telemetry = sorted(telemetry_samples, key=lambda s: s.timestamp_utc)

    result: list[CanonicalSample] = []
    used_telemetry: set[int] = set()

    for f in sorted_flow:
        best_idx: int | None = None
        best_delta: timedelta | None = None

        for idx, t in enumerate(sorted_telemetry):
            if idx in used_telemetry:
                continue
            delta = abs(t.timestamp_utc - f.timestamp_utc)
            if delta <= tolerance and (best_delta is None or delta < best_delta):
                    best_delta = delta
                    best_idx = idx

        if best_idx is not None:
            used_telemetry.add(best_idx)
            t = sorted_telemetry[best_idx]
            confidence = _compute_confidence(best_delta, tolerance)
            result.append(
                CanonicalSample(
                    timestamp_axis=f.timestamp_utc,
                    source="merged",
                    time_delta=best_delta,
                    flow_potencia_produccion_w=f.potencia_de_produccion_w,
                    flow_potencia_consumo_w=f.potencia_de_consumo_w,
                    flow_grid_w=f.energia_de_la_red_w,
                    flow_soc_pct=f.soc_pct,
                    flow_battery_w=f.potencia_de_la_bateria_w,
                    telemetry_pv_power_w=_pv_power(t),
                    telemetry_grid_power_w=t.get_float("potencia_total_ca_w"),
                    telemetry_battery_power_w=t.get_float("potencia_de_bateria_w"),
                    telemetry_soc_pct=t.get_float("soc_pct"),
                    telemetry_inverter_state=t.get_text("current_state_of_machine"),
                    quality_level="normalized",
                    confidence=confidence,
                )
            )
        else:
            result.append(
                CanonicalSample(
                    timestamp_axis=f.timestamp_utc,
                    source="flow",
                    time_delta=None,
                    flow_potencia_produccion_w=f.potencia_de_produccion_w,
                    flow_potencia_consumo_w=f.potencia_de_consumo_w,
                    flow_grid_w=f.energia_de_la_red_w,
                    flow_soc_pct=f.soc_pct,
                    flow_battery_w=f.potencia_de_la_bateria_w,
                    quality_level="measured",
                    confidence=1.0,
                )
            )

    for idx, t in enumerate(sorted_telemetry):
        if idx not in used_telemetry:
            result.append(
                CanonicalSample(
                    timestamp_axis=t.timestamp_utc,
                    source="telemetry",
                    time_delta=None,
                    telemetry_pv_power_w=_pv_power(t),
                    telemetry_grid_power_w=t.get_float("potencia_total_ca_w"),
                    telemetry_battery_power_w=t.get_float("potencia_de_bateria_w"),
                    telemetry_soc_pct=t.get_float("soc_pct"),
                    telemetry_inverter_state=t.signals.get("current_state_of_machine") if t.signals.get("current_state_of_machine") is not None else None,
                    quality_level="measured",
                    confidence=1.0,
                )
            )

    result.sort(key=lambda s: s.timestamp_axis)
    return result


def _pv_power(t: InverterTelemetrySample) -> float | None:
    pv1 = t.get_float("potencia_cc_pv1_w")
    pv2 = t.get_float("potencia_cc_pv2_w")
    if pv1 is not None and pv2 is not None:
        return pv1 + pv2
    if pv1 is not None:
        return pv1
    if pv2 is not None:
        return pv2
    return None


def _compute_confidence(delta: timedelta | None, tolerance: timedelta) -> float:
    if delta is None:
        return 1.0
    ratio = delta / tolerance
    return max(0.0, 1.0 - ratio)
