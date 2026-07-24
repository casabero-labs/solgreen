"""Common operational error sanitization — no secrets in logs or output."""

from __future__ import annotations

import re

_DSN_RE = re.compile(r"(postgresql|postgres|postgis)://[^@]+@[^/]+/[^?]*", re.IGNORECASE)
_PASS_RE = re.compile(r"(password|passwd|pwd)[=:][^\s,;]+", re.IGNORECASE)
_TOKEN_RE = re.compile(r"(token|api_?key|auth)[=:][^\s,;]+", re.IGNORECASE)
_SECRET_RE = re.compile(r"(secret|app_?secret)[=:][^\s,;]+", re.IGNORECASE)
_STATION_ID_RE = re.compile(r"(station_?id)[=:][a-z0-9\-]{4,}", re.IGNORECASE)
_SERIAL_RE = re.compile(r"(device_?sn|serial)[=:][a-z0-9\-]{4,}", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}")


def sanitize_error(message: str) -> str:
    """Remove sensitive values from operational error messages."""
    msg = _DSN_RE.sub(r"\1://***:***@***/***", message)
    msg = _PASS_RE.sub(r"\1=***", msg)
    msg = _TOKEN_RE.sub(r"\1=***", msg)
    msg = _SECRET_RE.sub(r"\1=***", msg)
    msg = _STATION_ID_RE.sub(r"\1=ST****", msg)
    msg = _SERIAL_RE.sub(r"\1=SN****", msg)
    msg = _EMAIL_RE.sub("***@***.***", msg)
    return msg
