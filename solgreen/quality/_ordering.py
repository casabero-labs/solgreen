from collections import defaultdict
from datetime import datetime

from solgreen.contracts.inverter_telemetry import InverterTelemetrySample
from solgreen.contracts.plant_flow import PlantFlowSample
from solgreen.quality._types import DuplicateTimestamp, OrderingInfo


def _extract_ts_utc(sample: InverterTelemetrySample | PlantFlowSample) -> datetime:
    return sample.timestamp_utc


def _detect_duplicates(
    samples: list[InverterTelemetrySample],
) -> tuple[OrderingInfo, tuple[DuplicateTimestamp, ...]]:
    was_ordered = True
    seen_positions: dict[datetime, list[int]] = defaultdict(list)
    for i, s in enumerate(samples):
        ts = s.timestamp_utc
        if i > 0 and ts < samples[i - 1].timestamp_utc:
            was_ordered = False
        seen_positions[ts].append(i)

    dup_groups = []
    for ts, indices in seen_positions.items():
        if len(indices) > 1:
            dup_groups.append(
                DuplicateTimestamp(
                    index=indices[0],
                    timestamp=ts,
                    count=len(indices),
                    indices=tuple(indices),
                )
            )
    dup_groups.sort(key=lambda d: d.index)

    was_strict = len(dup_groups) == 0
    ordering = OrderingInfo(was_ordered=was_ordered, was_strict=was_strict)
    return ordering, tuple(dup_groups)


def _detect_duplicates_flow(
    samples: list[PlantFlowSample],
) -> tuple[OrderingInfo, tuple[DuplicateTimestamp, ...]]:
    was_ordered = True
    seen_positions: dict[datetime, list[int]] = defaultdict(list)
    for i, s in enumerate(samples):
        ts = s.timestamp_utc
        if i > 0 and ts < samples[i - 1].timestamp_utc:
            was_ordered = False
        seen_positions[ts].append(i)

    dup_groups = []
    for ts, indices in seen_positions.items():
        if len(indices) > 1:
            dup_groups.append(
                DuplicateTimestamp(
                    index=indices[0],
                    timestamp=ts,
                    count=len(indices),
                    indices=tuple(indices),
                )
            )
    dup_groups.sort(key=lambda d: d.index)

    was_strict = len(dup_groups) == 0
    ordering = OrderingInfo(was_ordered=was_ordered, was_strict=was_strict)
    return ordering, tuple(dup_groups)
