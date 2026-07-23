"""Pydantic models for SOLARMAN API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pydantic


class TokenResponse(pydantic.BaseModel):
    """Token obtain response from SOLARMAN /account/v1.0/token endpoint."""

    model_config = pydantic.ConfigDict(extra="allow")

    access_token: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("accessToken", "access_token"),
    )
    refresh_token: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("refreshToken", "refresh_token"),
    )
    expires_in: int | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("expiresIn", "expires_in"),
    )

    @pydantic.model_validator(mode="after")
    def _coerce_expires_in(self) -> TokenResponse:
        if isinstance(self.expires_in, str):
            self.expires_in = int(self.expires_in)
        return self

    success: bool | None = pydantic.Field(default=True)
    code: int | None = None
    msg: str | None = None
    request_id: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("requestId", "request_id"),
    )

    @pydantic.model_validator(mode="after")
    def _check_success(self) -> TokenResponse:
        if not self.success:
            raise ValueError(f"SOLARMAN token request failed: code={self.code} msg={self.msg}")
        if not self.access_token:
            raise ValueError("SOLARMAN token response missing access_token")
        return self


class StationInfo(pydantic.BaseModel):
    """Station information returned by SOLARMAN API."""

    model_config = pydantic.ConfigDict(extra="allow")

    station_id: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("stationId", "id"),
    )
    station_name: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("stationName", "name"),
    )
    station_code: str | None = pydantic.Field(default=None, validation_alias="stationCode")
    latitude: float | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("latitude", "locationLat"),
    )
    longitude: float | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("longitude", "locationLng"),
    )
    timezone: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("timezone", "regionTimezone"),
    )
    installed_date: str | None = pydantic.Field(default=None, validation_alias="installedDate")
    capacity: float | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("capacity", "installedCapacity"),
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _coerce_int_to_str_before(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("stationId", "id"):
                if key in data and isinstance(data[key], int):
                    data[key] = str(data[key])
        return data


class DeviceInfo(pydantic.BaseModel):
    """Device information returned by SOLARMAN API."""

    model_config = pydantic.ConfigDict(extra="allow")

    device_id: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("deviceId", "id"),
    )
    device_sn: str | None = pydantic.Field(default=None, validation_alias="deviceSn")
    device_type: str | None = pydantic.Field(default=None, validation_alias="deviceType")
    device_name: str | None = pydantic.Field(default=None, validation_alias="deviceName")
    station_id: str | None = pydantic.Field(default=None, validation_alias="stationId")
    status: int | None = pydantic.Field(default=None, validation_alias="connectStatus")
    collection_time: int | None = pydantic.Field(default=None, validation_alias="collectionTime")

    @pydantic.model_validator(mode="before")
    @classmethod
    def _coerce_int_to_str(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("deviceId", "id"):
                if key in data and isinstance(data[key], int):
                    data[key] = str(data[key])
        return data


class CurrentDataRecord(pydantic.BaseModel):
    """A single current data point from SOLARMAN API.

    The SOLARMAN current data response contains a flat list of key-value-unit-name
    records in the ``dataList`` field, not a nested ``data`` dict.
    """

    model_config = pydantic.ConfigDict(extra="allow")

    device_id: str | None = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasChoices("deviceId", "id"),
    )
    device_sn: str | None = pydantic.Field(default=None, validation_alias="deviceSn")
    device_type: str | None = pydantic.Field(default=None, validation_alias="deviceType")
    device_state: int | None = pydantic.Field(default=None, validation_alias="deviceState")
    collection_time: int | None = pydantic.Field(default=None, validation_alias="collectionTime")
    data_list: list[dict[str, Any]] | None = pydantic.Field(
        default=None,
        validation_alias="dataList",
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _coerce_device_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("deviceId", "id"):
                if key in data and isinstance(data[key], int):
                    data[key] = str(data[key])
        return data


class HistoricalDataPoint(pydantic.BaseModel):
    """A single historical data point from SOLARMAN API."""

    model_config = pydantic.ConfigDict(extra="allow")

    device_id: str | None = pydantic.Field(default=None, validation_alias="deviceId")
    device_sn: str | None = pydantic.Field(default=None, validation_alias="deviceSn")
    timestamp: datetime | None = None
    data: dict[str, Any] | None = None


class AlarmRecord(pydantic.BaseModel):
    """Alarm record from SOLARMAN API."""

    model_config = pydantic.ConfigDict(extra="allow")

    alarm_id: str | None = pydantic.Field(default=None, validation_alias="alarmId")
    alarm_code: str | None = pydantic.Field(default=None, validation_alias="alarmCode")
    alarm_name: str | None = pydantic.Field(default=None, validation_alias="alarmName")
    device_id: str | None = pydantic.Field(default=None, validation_alias="deviceId")
    device_sn: str | None = pydantic.Field(default=None, validation_alias="deviceSn")
    station_id: str | None = pydantic.Field(default=None, validation_alias="stationId")
    alarm_time: datetime | None = pydantic.Field(default=None, validation_alias="alarmTime")
    alarm_status: str | None = pydantic.Field(default=None, validation_alias="alarmStatus")
    severity: str | None = None


class QuotaInfo(pydantic.BaseModel):
    """Quota / usage information from SOLARMAN API."""

    model_config = pydantic.ConfigDict(extra="allow")

    total: int | None = None
    used: int | None = None
    remaining: int | None = None
    reset_time: str | None = pydantic.Field(default=None, validation_alias="resetTime")
    request_id: str | None = pydantic.Field(default=None, validation_alias="requestId")


class ApiResponse[p](pydantic.BaseModel):
    """Generic SOLARMAN API response wrapper."""

    model_config = pydantic.ConfigDict(extra="allow")

    success: bool | None = pydantic.Field(default=True)
    code: int | None = None
    msg: str | None = None
    request_id: str | None = pydantic.Field(default=None, validation_alias="requestId")
    data: list[p] | None = None
    total: int | None = None
    page_no: int | None = pydantic.Field(default=None, validation_alias="pageNo")
    page_size: int | None = pydantic.Field(default=None, validation_alias="pageSize")
