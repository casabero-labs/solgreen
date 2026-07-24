"""SOLARMAN API authentication — token management."""

from __future__ import annotations

import threading
import time

import httpx

from solgreen.integrations.solarman.errors import (
    SolarmanAuthenticationError,
    SolarmanServerError,
    SolarmanTimeoutError,
)
from solgreen.integrations.solarman.models import TokenResponse
from solgreen.integrations.solarman.settings import SolarmanSettings


class AuthToken:
    """In-memory auth token with expiry tracking. Thread-safe."""

    def __init__(self, access_token: str, expires_in: int) -> None:
        self.access_token = access_token
        self.expires_at: float = time.monotonic() + expires_in - 30
        self._lock = threading.Lock()

    def is_expired(self) -> bool:
        with self._lock:
            return time.monotonic() >= self.expires_at

    def is_near_expiry(self, *, buffer_seconds: float = 60.0) -> bool:
        with self._lock:
            return time.monotonic() >= (self.expires_at - buffer_seconds)


class SolarmanAuth:
    """Handles SOLARMAN authentication lifecycle."""

    def __init__(self, settings: SolarmanSettings) -> None:
        self._settings = settings
        self._token: AuthToken | None = None
        self._lock = threading.Lock()

    def obtain_token(self) -> TokenResponse:
        """Authenticate and obtain a new access token."""
        url = f"{self._settings.solarman_base_url}/account/v1.0/token"
        params = {"appId": self._settings.solarman_app_id, "language": "en"}
        payload = {
            "email": self._settings.solarman_email,
            "password": self._settings.solarman_password_sha256,
            "appSecret": self._settings.solarman_app_secret,
        }
        try:
            response = httpx.post(
                url,
                params=params,
                json=payload,
                timeout=self._settings.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise SolarmanTimeoutError(
                f"Timeout while obtaining token: {exc}",
            ) from exc

        if response.status_code == 401:
            body = response.json() if response.text else {}
            raise SolarmanAuthenticationError(
                f"Authentication rejected: {body.get('msg', 'invalid credentials')}",
                request_id=response.headers.get("requestId"),
            )
        if response.status_code >= 500:
            raise SolarmanServerError(
                f"SOLARMAN auth server error: {response.status_code}",
                request_id=response.headers.get("requestId"),
            )
        if response.status_code != 200:
            raise SolarmanAuthenticationError(
                f"Unexpected status {response.status_code} during authentication",
                request_id=response.headers.get("requestId"),
            )

        data = response.json()
        token_response = TokenResponse.model_validate(data)

        assert token_response.access_token is not None, (
            "TokenResponse model ensures access_token is set"
        )
        self._token = AuthToken(
            access_token=token_response.access_token,
            expires_in=token_response.expires_in or 3600,
        )
        return token_response

    def get_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid access token, refreshing if expired or near expiry."""
        if self._token is None or force_refresh or self._token.is_near_expiry():
            self.obtain_token()
        assert self._token is not None
        return self._token.access_token

    def get_authorization_header(self) -> dict[str, str]:
        """Return the Authorization header dict with current token."""
        return {"Authorization": f"Bearer {self.get_token()}"}
