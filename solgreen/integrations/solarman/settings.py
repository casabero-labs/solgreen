"""Tip typed configuration for SOLARMAN OpenAPI connector."""

from __future__ import annotations

import re

import pydantic


class SolarmanSettings(pydantic.BaseModel):
    """Typed configuration for the SOLARMAN OpenAPI connector.

    All secrets are hidden from repr(). URL is validated.
    """

    model_config = pydantic.ConfigDict(
        extra="forbid",
    )

    solarman_base_url: str = pydantic.Field(
        description="Base URL for the SOLARMAN OpenAPI endpoint.",
    )
    solarman_app_id: str = pydantic.Field(
        description="SOLARMAN application identifier.",
        min_length=1,
    )
    solarman_app_secret: str = pydantic.Field(
        description="SOLARMAN application secret.",
        min_length=1,
    )
    solarman_email: str = pydantic.Field(
        description="Account email address.",
        min_length=1,
    )
    solarman_password_sha256: str = pydantic.Field(
        description="SHA-256 hex digest of the account password.",
        min_length=64,
        max_length=64,
    )
    timeout_seconds: float = pydantic.Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="HTTP timeout for requests.",
    )
    max_retries: int = pydantic.Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for transient errors.",
    )
    retry_backoff_base: float = pydantic.Field(
        default=1.5,
        ge=1.0,
        le=10.0,
        description="Exponential backoff base for retries.",
    )

    @pydantic.field_validator("solarman_base_url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("must be a valid HTTP/HTTPS URL")
        return v.rstrip("/")

    @pydantic.field_validator("solarman_password_sha256")
    @classmethod
    def _validate_sha256(cls, v: str) -> str:
        if not re.fullmatch(r"[a-fA-F0-9]{64}", v):
            raise ValueError("must be a 64-character hexadecimal SHA-256 hash")
        return v.lower()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"solarman_base_url={self.solarman_base_url!r}, "
            f"timeout_seconds={self.timeout_seconds}, "
            f"max_retries={self.max_retries}"
            ")"
        )


def build_settings_from_env() -> SolarmanSettings:
    """Build SolarmanSettings from environment variables.

    Raises SolarmanConfigurationError if any required variable is missing.
    """
    import os

    from solgreen.integrations.solarman.errors import SolarmanConfigurationError

    missing: list[str] = []
    values: dict[str, str | float | int] = {}

    required_str = [
        "SOLARMAN_BASE_URL",
        "SOLARMAN_APP_ID",
        "SOLARMAN_APP_SECRET",
        "SOLARMAN_EMAIL",
        "SOLARMAN_PASSWORD_SHA256",
    ]
    for key in required_str:
        val = os.getenv(key)
        if val is None:
            missing.append(key)
        else:
            values[key.lower()] = val

    if missing:
        raise SolarmanConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}",
        )

    try:
        return SolarmanSettings(
            solarman_base_url=values["solarman_base_url"],
            solarman_app_id=values["solarman_app_id"],
            solarman_app_secret=values["solarman_app_secret"],
            solarman_email=values["solarman_email"],
            solarman_password_sha256=values["solarman_password_sha256"],
            timeout_seconds=float(os.getenv("SOLARMAN_TIMEOUT_SECONDS", "30.0")),
            max_retries=int(os.getenv("SOLARMAN_MAX_RETRIES", "3")),
            retry_backoff_base=float(os.getenv("SOLARMAN_RETRY_BACKOFF_BASE", "1.5")),
        )
    except pydantic.ValidationError as exc:
        first_error = exc.errors()[0]
        msg = first_error.get("msg", "validation error")
        input_val = first_error.get("input", "")
        field = first_error.get("loc", ("unknown",))
        field_name = str(field[0]) if field else "unknown"
        raise SolarmanConfigurationError(
            f"Missing required or invalid: {field_name} ({msg}): {input_val!r}",
        ) from exc
