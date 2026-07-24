"""SOLARMAN OpenAPI read-only connector.

Architecture:
    solgreen/integrations/solarman/
        auth.py       — Token management and authentication
        client.py     — Read-only HTTP client with retry/backoff
        contracts.py  — Historical query contracts
        endpoints.py  — Read-only endpoint allowlist
        errors.py     — Exception hierarchy
        models.py     — Pydantic response models
        redaction.py  — Automatic PII redaction for logs
        settings.py   — Typed configuration from environment
"""

from solgreen.integrations.solarman.auth import SolarmanAuth
from solgreen.integrations.solarman.client import SolarmanClient
from solgreen.integrations.solarman.contracts import HistoricalQuery
from solgreen.integrations.solarman.errors import (
    ReadOnlyViolationError,
    SolarmanAuthenticationError,
    SolarmanConfigurationError,
    SolarmanError,
    SolarmanForbiddenError,
    SolarmanRateLimitError,
    SolarmanServerError,
    SolarmanTimeoutError,
)
from solgreen.integrations.solarman.models import (
    AlarmRecord,
    CurrentDataRecord,
    DeviceInfo,
    HistoricalDataPoint,
    QuotaInfo,
    StationInfo,
    TokenResponse,
)
from solgreen.integrations.solarman.redaction import (
    is_sensitive_key,
    redact_dict,
    sanitize_for_logging,
)
from solgreen.integrations.solarman.settings import SolarmanSettings, build_settings_from_env

__all__ = [
    "AlarmRecord",
    "CurrentDataRecord",
    "DeviceInfo",
    "HistoricalDataPoint",
    "HistoricalQuery",
    "QuotaInfo",
    "ReadOnlyViolationError",
    "SolarmanAuth",
    "SolarmanAuthenticationError",
    "SolarmanClient",
    "SolarmanConfigurationError",
    "SolarmanError",
    "SolarmanForbiddenError",
    "SolarmanRateLimitError",
    "SolarmanServerError",
    "SolarmanSettings",
    "SolarmanTimeoutError",
    "StationInfo",
    "TokenResponse",
    "build_settings_from_env",
    "is_sensitive_key",
    "redact_dict",
    "sanitize_for_logging",
]
