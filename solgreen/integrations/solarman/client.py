"""SOLARMAN read-only HTTP client with retry, backoff, and rate-limit handling."""

from __future__ import annotations

import contextlib
import random
import threading
import time
from typing import Any

import httpx

from solgreen.integrations.solarman.auth import SolarmanAuth
from solgreen.integrations.solarman.endpoints import is_endpoint_allowed
from solgreen.integrations.solarman.errors import (
    ReadOnlyViolationError,
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
)
from solgreen.integrations.solarman.settings import SolarmanSettings


def _jitter(base: float, attempt: int, max_delay: float = 30.0) -> float:
    """Exponential backoff with full jitter."""
    exp_delay = min(base**attempt, max_delay)
    return random.uniform(0.0, exp_delay)


class SolarmanClient:
    """
    Read-only SOLARMAN API client.

    All write operations raise ReadOnlyViolationError.
    Retries transient errors with exponential backoff + jitter.
    Respects Retry-After headers from 429 responses.
    Re-authenticates once on 401.
    """

    def __init__(self, settings: SolarmanSettings) -> None:
        self._settings = settings
        self._auth = SolarmanAuth(settings)
        self._client = httpx.Client(timeout=settings.timeout_seconds)
        self._reauth_in_progress = threading.Lock()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SolarmanClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        allow_redirects: bool = True,
    ) -> httpx.Response:
        """Make an HTTP request with full retry and reauth logic."""
        if not is_endpoint_allowed(path, method):
            raise ReadOnlyViolationError(operation=method, endpoint=path)

        headers = self._auth.get_authorization_header()
        url = f"{self._settings.solarman_base_url}/{path.lstrip('/')}"
        attempt = 0
        reauthenticated = False

        while True:
            attempt += 1
            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    follow_redirects=allow_redirects,
                )
            except httpx.TimeoutException as exc:
                raise SolarmanTimeoutError(
                    f"Timeout during {method} {path} (attempt {attempt}): {exc}",
                ) from exc
            except httpx.ConnectError as exc:
                if attempt > self._settings.max_retries:
                    raise SolarmanTimeoutError(
                        f"Connection failed after {attempt} attempts: {exc}",
                    ) from exc
                delay = _jitter(self._settings.retry_backoff_base, attempt)
                time.sleep(delay)
                continue

            if response.status_code == 401 and not reauthenticated:
                reauthenticated = True
                with self._reauth_in_progress:
                    self._auth.get_token(force_refresh=True)
                headers = self._auth.get_authorization_header()
                continue

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait: float | None = None
                if retry_after:
                    with contextlib.suppress(ValueError):
                        wait = float(retry_after)
                if wait is None:
                    wait = _jitter(self._settings.retry_backoff_base, attempt)
                if attempt > self._settings.max_retries:
                    raise SolarmanRateLimitError(
                        f"Rate limit hit after {attempt} attempts for {method} {path}",
                        retry_after=wait,
                    )
                time.sleep(wait)
                continue

            if response.status_code >= 500:
                if attempt > self._settings.max_retries:
                    raise SolarmanServerError(
                        f"SOLARMAN server error {response.status_code} after {attempt} attempts: {path}",
                        request_id=response.headers.get("requestId"),
                    )
                delay = _jitter(self._settings.retry_backoff_base, attempt)
                time.sleep(delay)
                continue

            if response.status_code == 403:
                raise SolarmanForbiddenError(
                    f"Endpoint forbidden: {method} {path}",
                    request_id=response.headers.get("requestId"),
                )

            return response

    def list_stations(self) -> list[StationInfo]:
        """List all stations (SOLARMAN uses POST)."""
        resp = self._request("POST", "station/v1.0/list", json={})
        data = resp.json()
        if not isinstance(data, dict):
            return []
        items = data.get("stationList", data.get("data", []))
        if not isinstance(items, list):
            items = []
        return [StationInfo.model_validate(s) for s in items]

    def get_station_information(self, station_id: str) -> StationInfo:
        """Get information for a specific station."""
        resp = self._request("POST", "station/v1.0/info", json={"stationId": station_id})
        data = resp.json()
        station = (data.get("data") or {}) if isinstance(data, dict) else {}
        return StationInfo.model_validate(station)

    def list_station_devices(self, station_id: str) -> list[DeviceInfo]:
        """List all devices in a station.

        Note: ``station/v1.0/device`` returns ``deviceListItems``, not ``data``.
        The endpoint ``station/v1.0/device/list`` is locked (returns 2101009).
        """
        resp = self._request("POST", "station/v1.0/device", json={"stationId": station_id})
        data = resp.json()
        if not isinstance(data, dict):
            return []
        items = data.get("deviceListItems", data.get("data", []))
        if not isinstance(items, list):
            items = []
        return [DeviceInfo.model_validate(d) for d in items]

    def list_devices(self) -> list[DeviceInfo]:
        """List all devices.

        Warning: ``device/v1.0/list`` requires a different auth scope (SmartAC)
        and will return ``auth invalid token`` with account credentials.
        """
        resp = self._request("POST", "device/v1.0/list", json={})
        data = resp.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [DeviceInfo.model_validate(d) for d in items]

    def get_device_current_data(self, device_id: str) -> CurrentDataRecord:
        """Get current data for a specific device."""
        resp = self._request("POST", "device/v1.0/currentData", json={"deviceId": device_id})
        data = resp.json()
        if not isinstance(data, dict):
            raise SolarmanServerError(f"Unexpected response type for current data: {type(data)}")
        return CurrentDataRecord.model_validate(data)

    def get_station_current_data(self, station_id: str) -> list[CurrentDataRecord]:
        """Get current data for all devices in a station."""
        resp = self._request("POST", "station/v1.0/currentData", json={"stationId": station_id})
        data = resp.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [CurrentDataRecord.model_validate(r) for r in items]

    def get_device_historical_data(
        self,
        device_id: str,
        start_time: str,
        end_time: str,
        *,
        time_zone: str = "America/Bogota",
    ) -> list[HistoricalDataPoint]:
        """Get historical data for a specific device."""
        resp = self._request(
            "POST",
            "device/v1.0/historyData",
            json={
                "deviceId": device_id,
                "startTime": start_time,
                "endTime": end_time,
                "timeZone": time_zone,
            },
        )
        data = resp.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [HistoricalDataPoint.model_validate(p) for p in items]

    def get_station_historical_data(
        self,
        station_id: str,
        start_time: str,
        end_time: str,
        *,
        time_zone: str = "America/Bogota",
    ) -> list[HistoricalDataPoint]:
        """Get historical data for all devices in a station."""
        resp = self._request(
            "POST",
            "station/v1.0/historyData",
            json={
                "stationId": station_id,
                "startTime": start_time,
                "endTime": end_time,
                "timeZone": time_zone,
            },
        )
        data = resp.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [HistoricalDataPoint.model_validate(p) for p in items]

    def get_alarm_list(
        self,
        station_id: str | None = None,
        device_id: str | None = None,
        page_no: int = 1,
        page_size: int = 20,
    ) -> list[AlarmRecord]:
        """Get alarm list with optional station/device filters."""
        body: dict[str, Any] = {"pageNo": page_no, "pageSize": page_size}
        if station_id:
            body["stationId"] = station_id
        if device_id:
            body["deviceId"] = device_id
        resp = self._request("POST", "alarm/v1.0/list", json=body)
        data = resp.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [AlarmRecord.model_validate(a) for a in items]

    def query_remaining_quota(self) -> QuotaInfo:
        """Query remaining API quota."""
        resp = self._request("POST", "quota/v1.0/query", json={})
        data = resp.json()
        info = (data.get("data") or {}) if isinstance(data, dict) else {}
        return QuotaInfo.model_validate(info)
