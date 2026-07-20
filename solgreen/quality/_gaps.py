from datetime import timedelta

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.quality._types import TemporalGap


def detect_gaps(
    samples: list[InverterTelemetrySample],
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
) -> tuple[TemporalGap, ...]:
    if len(samples) < 2:
        return ()

    sorted_samples = sorted(samples, key=lambda s: s.timestamp_utc)
    gaps: list[TemporalGap] = []
    threshold = expected_interval * gap_factor

    for i in range(len(sorted_samples) - 1):
        before = sorted_samples[i]
        after = sorted_samples[i + 1]
        delta = after.timestamp_utc - before.timestamp_utc
        if delta > threshold:
            gaps.append(
                TemporalGap(
                    before_index=i,
                    after_index=i + 1,
                    gap_duration=delta,
                    expected_interval=expected_interval,
                    gap_ratio=delta / expected_interval,
                )
            )

    return tuple(gaps)


def detect_gaps_flow(
    samples: list[PlantFlowSample],
    *,
    expected_interval: timedelta = timedelta(minutes=5),
    gap_factor: float = 1.5,
) -> tuple[TemporalGap, ...]:
    if len(samples) < 2:
        return ()

    sorted_samples = sorted(samples, key=lambda s: s.timestamp_utc)
    gaps: list[TemporalGap] = []
    threshold = expected_interval * gap_factor

    for i in range(len(sorted_samples) - 1):
        before = sorted_samples[i]
        after = sorted_samples[i + 1]
        delta = after.timestamp_utc - before.timestamp_utc
        if delta > threshold:
            gaps.append(
                TemporalGap(
                    before_index=i,
                    after_index=i + 1,
                    gap_duration=delta,
                    expected_interval=expected_interval,
                    gap_ratio=delta / expected_interval,
                )
            )

    return tuple(gaps)
