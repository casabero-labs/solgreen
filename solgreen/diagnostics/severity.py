from __future__ import annotations

from typing import Literal

type SeverityLevel = Literal["info", "low", "medium", "high", "critical"]

SEVERITY_ORDER: dict[SeverityLevel, int] = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def severity_gte(a: SeverityLevel, b: SeverityLevel) -> bool:
    return SEVERITY_ORDER[a] >= SEVERITY_ORDER[b]
