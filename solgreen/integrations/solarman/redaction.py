"""Automatic redaction for sensitive fields in SOLARMAN API responses."""

from __future__ import annotations

import re
from typing import Any

_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(secret|password|token|email|serial|account|address)"),
    re.compile(r"(?i)(device[_\s]?(sn|ssn|id))"),
    re.compile(r"(?i)(station[_\s]?(id))"),
    re.compile(r"(?i)(device[_\s]?(id))"),
    re.compile(r"(?i)(app[_\s]?(id|secret))"),
)


def is_sensitive_key(key: str) -> bool:
    """Return True if the key name suggests sensitive content."""
    return any(pattern.search(key) is not None for pattern in _SENSITIVE_PATTERNS)


def redact_value(value: Any) -> str:
    """Replace a sensitive value with a safe placeholder."""
    if isinstance(value, str) and len(value) > 4:
        return f"{value[:2]}***{value[-2:]}"
    return "***"


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of data with all sensitive keys redacted.

    Keys matching is_sensitive_key are replaced with their value replaced
    by '***'. Nested dicts and lists are handled recursively.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            result[key] = redact_value(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item)
                if isinstance(item, dict)
                else redact_value(item)
                if is_sensitive_key(str(item))
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def sanitize_for_logging(data: dict[str, Any]) -> dict[str, Any]:
    """Alias for redact_dict — used in logging paths."""
    return redact_dict(data)
