"""SOLARMAN connector error types."""


class SolarmanError(Exception):
    """Base exception for SOLARMAN connector errors."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        self.request_id = request_id
        super().__init__(message)


class SolarmanAuthenticationError(SolarmanError):
    """Raised when authentication fails (401)."""

    pass


class SolarmanForbiddenError(SolarmanError):
    """Raised when endpoint is not allowed for this connector (403)."""

    pass


class SolarmanRateLimitError(SolarmanError):
    """Raised when rate limit is hit (429)."""

    def __init__(
        self,
        message: str,
        *,
        request_id: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, request_id=request_id)


class SolarmanServerError(SolarmanError):
    """Raised for 5xx errors from SOLARMAN API."""

    pass


class SolarmanTimeoutError(SolarmanError):
    """Raised when connection or read timeout occurs."""

    pass


class SolarmanRedactionError(SolarmanError):
    """Raised when redaction fails."""

    pass


class ReadOnlyViolationError(SolarmanError):
    """Raised when attempting a write operation on a read-only connector."""

    def __init__(self, operation: str, endpoint: str) -> None:
        self.operation = operation
        self.endpoint = endpoint
        super().__init__(
            f"Write operation '{operation}' on endpoint '{endpoint}' is not permitted. "
            "This connector is read-only."
        )


class SolarmanConfigurationError(SolarmanError):
    """Raised when configuration is invalid or secrets are missing."""

    pass
