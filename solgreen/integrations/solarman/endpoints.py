"""SOLARMAN API endpoint definitions and read-only enforcement."""

from __future__ import annotations

import re

ALLOWED_ENDPOINTS: frozenset[tuple[str, ...]] = frozenset(
    {
        ("account", "v1.0", "token", "POST"),
        ("account", "v1.0", "token", "GET"),
        ("station", "v1.0", "list", "POST"),
        ("station", "v1.0", "info", "POST"),
        ("station", "v1.0", "device", "POST"),
        ("station", "v1.0", "device", "list", "POST"),
        ("device", "v1.0", "list", "POST"),
        ("device", "v1.0", "currentData", "POST"),
        ("station", "v1.0", "currentData", "POST"),
        ("device", "v1.0", "historyData", "POST"),
        ("station", "v1.0", "historyData", "POST"),
        ("alarm", "v1.0", "list", "POST"),
        ("quota", "v1.0", "query", "POST"),
    }
)

PROHIBITED_METHODS: frozenset[str] = frozenset(
    {
        "PUT",
        "PATCH",
        "DELETE",
    }
)

PROHIBITED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(create|add|new)"),
    re.compile(r"(?i)(update|edit|modify|change)"),
    re.compile(r"(?i)(delete|remove|destroy)"),
    re.compile(r"(?i)(bind|unbind)"),
    re.compile(r"(?i)(configure|config)"),
    re.compile(r"(?i)(remote[_\s]?control|send[_\s]?command)"),
    re.compile(r"(?i)(change[_\s]?password|reset[_\s]?password)"),
)


def is_endpoint_allowed(endpoint_path: str, method: str) -> bool:
    """
    Return True if the endpoint+method is allowed by the read-only connector.

    endpoint_path should be a clean relative path like "account/v1.0/token".
    """
    parts = [p.strip() for p in endpoint_path.strip("/").split("/")]
    if len(parts) < 2:
        return False
    method_upper = method.upper()
    key = tuple([*parts, method_upper])
    if key in ALLOWED_ENDPOINTS:
        return True
    if method_upper in PROHIBITED_METHODS or method_upper == "POST":
        for pattern in PROHIBITED_PATTERNS:
            if pattern.search(endpoint_path):
                return False
    return False
