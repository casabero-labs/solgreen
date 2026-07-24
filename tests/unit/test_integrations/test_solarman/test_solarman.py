"""Tests for solgreen.integrations.solarman."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import patch

import httpx
import pydantic
import pytest

from solgreen.integrations.solarman import (
    HistoricalQuery,
    ReadOnlyViolationError,
    SolarmanAuthenticationError,
    SolarmanClient,
    SolarmanConfigurationError,
    SolarmanRateLimitError,
    SolarmanServerError,
    SolarmanSettings,
    SolarmanTimeoutError,
    TokenResponse,
    build_settings_from_env,
    is_sensitive_key,
    redact_dict,
)

# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------


class TestSolarmanSettings:
    def test_valid_settings(self) -> None:
        s = SolarmanSettings(
            solarman_base_url="https://api.solarman.cn",
            solarman_app_id="my-app-id",
            solarman_app_secret="my-secret",
            solarman_email="test@example.com",
            solarman_password_sha256="a" * 64,
        )
        assert s.solarman_base_url == "https://api.solarman.cn"
        assert s.timeout_seconds == 30.0
        assert s.max_retries == 3

    def test_custom_timeout_and_retries(self) -> None:
        s = SolarmanSettings(
            solarman_base_url="https://api.solarman.cn",
            solarman_app_id="my-app-id",
            solarman_app_secret="my-secret",
            solarman_email="test@example.com",
            solarman_password_sha256="b" * 64,
            timeout_seconds=60.0,
            max_retries=5,
        )
        assert s.timeout_seconds == 60.0
        assert s.max_retries == 5

    def test_invalid_url(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SolarmanSettings(
                solarman_base_url="not-a-url",
                solarman_app_id="x",
                solarman_app_secret="x",
                solarman_email="x@x.com",
                solarman_password_sha256="c" * 64,
            )

    def test_invalid_sha256_too_short(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SolarmanSettings(
                solarman_base_url="https://api.solarman.cn",
                solarman_app_id="x",
                solarman_app_secret="x",
                solarman_email="x@x.com",
                solarman_password_sha256="abc",
            )

    def test_invalid_sha256_non_hex(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            SolarmanSettings(
                solarman_base_url="https://api.solarman.cn",
                solarman_app_id="x",
                solarman_app_secret="x",
                solarman_email="x@x.com",
                solarman_password_sha256="g" * 64,
            )

    def test_repr_hides_secrets(self) -> None:
        s = SolarmanSettings(
            solarman_base_url="https://api.solarman.cn",
            solarman_app_id="my-app-id",
            solarman_app_secret="my-secret",
            solarman_email="test@example.com",
            solarman_password_sha256="a" * 64,
        )
        repr_str = repr(s)
        assert "my-secret" not in repr_str
        assert "my-app-id" not in repr_str
        assert "test@example.com" not in repr_str
        assert "https://api.solarman.cn" in repr_str

    def test_url_strips_trailing_slash(self) -> None:
        s = SolarmanSettings(
            solarman_base_url="https://api.solarman.cn/",
            solarman_app_id="x",
            solarman_app_secret="x",
            solarman_email="x@x.com",
            solarman_password_sha256="a" * 64,
        )
        assert not s.solarman_base_url.endswith("/")

    def test_sha256_normalized_to_lowercase(self) -> None:
        s = SolarmanSettings(
            solarman_base_url="https://api.solarman.cn",
            solarman_app_id="x",
            solarman_app_secret="x",
            solarman_email="x@x.com",
            solarman_password_sha256="ABCD" * 16,
        )
        assert s.solarman_password_sha256 == ("abcd" * 16)


class TestBuildSettingsFromEnv:
    def test_missing_variable(self) -> None:
        env = {
            "SOLARMAN_BASE_URL": "https://api.solarman.cn",
            "SOLARMAN_APP_ID": "",
            "SOLARMAN_APP_SECRET": "",
            "SOLARMAN_EMAIL": "",
            "SOLARMAN_PASSWORD_SHA256": "",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(SolarmanConfigurationError) as exc_info:
                build_settings_from_env()
            assert "Missing required" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Redaction tests
# ---------------------------------------------------------------------------


class TestRedaction:
    def test_sensitive_key_redacted(self) -> None:
        data = {"email": "test@example.com", "password": "supersecret", "name": "John"}
        result = redact_dict(data)
        assert result["email"] == "te***om"
        assert result["password"] == "su***et"
        assert result["name"] == "John"

    def test_device_sn_redacted(self) -> None:
        data = {"deviceSn": "ABC123456789XYZ"}
        result = redact_dict(data)
        assert result["deviceSn"] == "AB***YZ"

    def test_nested_redaction(self) -> None:
        data = {"user": {"email": "a@b.com", "token": "tok1234567890"}}
        result = redact_dict(data)
        assert result["user"]["email"] == "a@***om"
        assert result["user"]["token"] == "to***90"

    def test_list_redaction(self) -> None:
        data = {"devices": [{"serial": "ABC123"}, {"serial": "XYZ789"}]}
        result = redact_dict(data)
        assert result["devices"][0]["serial"] == "AB***23"
        assert result["devices"][1]["serial"] == "XY***89"

    def test_is_sensitive_key(self) -> None:
        sensitive = [
            "email",
            "password",
            "token",
            "deviceSn",
            "stationId",
            "appId",
            "appSecret",
            "address",
        ]
        for k in sensitive:
            assert is_sensitive_key(k), f"{k} should be sensitive"
        safe = ["name", "status", "timestamp", "data", "code"]
        for k in safe:
            assert not is_sensitive_key(k), f"{k} should not be sensitive"


# ---------------------------------------------------------------------------
# Endpoint allowlist tests
# ---------------------------------------------------------------------------


class TestEndpoints:
    def test_allowed_read_endpoints(self) -> None:
        from solgreen.integrations.solarman.endpoints import is_endpoint_allowed

        assert is_endpoint_allowed("account/v1.0/token", "POST")
        assert is_endpoint_allowed("station/v1.0/list", "POST")
        assert is_endpoint_allowed("station/v1.0/info", "POST")
        assert is_endpoint_allowed("station/v1.0/device", "POST")
        assert is_endpoint_allowed("station/v1.0/device/list", "POST")
        assert is_endpoint_allowed("device/v1.0/list", "POST")
        assert is_endpoint_allowed("device/v1.0/currentData", "POST")
        assert is_endpoint_allowed("device/v1.0/historyData", "POST")
        assert is_endpoint_allowed("station/v1.0/currentData", "POST")
        assert is_endpoint_allowed("station/v1.0/historyData", "POST")
        assert is_endpoint_allowed("alarm/v1.0/list", "POST")
        assert is_endpoint_allowed("quota/v1.0/query", "POST")

    def test_post_only_for_allowed_endpoints(self) -> None:
        from solgreen.integrations.solarman.endpoints import is_endpoint_allowed

        assert not is_endpoint_allowed("station/v1.0/list", "GET")
        assert not is_endpoint_allowed("station/v1.0/device", "GET")
        assert not is_endpoint_allowed("device/v1.0/currentData", "GET")

    def test_blocked_write_endpoints(self) -> None:
        from solgreen.integrations.solarman.endpoints import is_endpoint_allowed

        assert not is_endpoint_allowed("station/v1.0/create", "POST")
        assert not is_endpoint_allowed("device/v1.0/update", "POST")
        assert not is_endpoint_allowed("device/v1.0/delete", "POST")
        assert not is_endpoint_allowed("device/v1.0/bind", "POST")
        assert not is_endpoint_allowed("device/v1.0/unbind", "POST")
        assert not is_endpoint_allowed("device/v1.0/configure", "POST")
        assert not is_endpoint_allowed("device/v1.0/remoteControl", "POST")
        assert not is_endpoint_allowed("device/v1.0/sendCommand", "POST")
        assert not is_endpoint_allowed("account/v1.0/changePassword", "POST")

    def test_unknown_endpoint_returns_false(self) -> None:
        from solgreen.integrations.solarman.endpoints import is_endpoint_allowed

        assert not is_endpoint_allowed("station/v1.0/unknown", "GET")
        assert not is_endpoint_allowed("device/v1.0/firmware", "GET")


# ---------------------------------------------------------------------------
# Token response tests
# ---------------------------------------------------------------------------


class TestTokenResponse:
    def test_valid_token(self) -> None:
        data = {
            "accessToken": "tok123",
            "refreshToken": "ref456",
            "expiresIn": 3600,
            "success": True,
            "code": 0,
            "requestId": "req-abc",
        }
        token = TokenResponse.model_validate(data)
        assert token.access_token == "tok123"
        assert token.refresh_token == "ref456"
        assert token.expires_in == 3600
        assert token.success is True

    def test_missing_access_token_raises(self) -> None:
        data = {"success": True}
        with pytest.raises(pydantic.ValidationError):
            TokenResponse.model_validate(data)

    def test_failed_response_raises(self) -> None:
        data = {"success": False, "code": 400, "msg": "Bad request"}
        with pytest.raises(pydantic.ValidationError):
            TokenResponse.model_validate(data)


# ---------------------------------------------------------------------------
# Client tests (mocked HTTP)
# ---------------------------------------------------------------------------


class TestSolarmanClient:
    @pytest.fixture
    def settings(self) -> SolarmanSettings:
        return SolarmanSettings(
            solarman_base_url="https://api.solarman.cn",
            solarman_app_id="test-id",
            solarman_app_secret="test-secret",
            solarman_email="test@example.com",
            solarman_password_sha256="a" * 64,
            timeout_seconds=10.0,
            max_retries=2,
        )

    @pytest.fixture
    def auth_settings(self) -> dict[str, str]:
        return {
            "SOLARMAN_BASE_URL": "https://api.solarman.cn",
            "SOLARMAN_APP_ID": "test-id",
            "SOLARMAN_APP_SECRET": "test-secret",
            "SOLARMAN_EMAIL": "test@example.com",
            "SOLARMAN_PASSWORD_SHA256": "a" * 64,
        }

    def test_obtain_token_success(self, settings: SolarmanSettings) -> None:
        mock_response = httpx.Response(
            200,
            json={
                "accessToken": "new-token-xyz",
                "refreshToken": "refresh-xyz",
                "expiresIn": 3600,
                "success": True,
                "code": 0,
                "requestId": "req-123",
            },
        )
        with patch("httpx.post", return_value=mock_response) as mock_post:
            from solgreen.integrations.solarman.auth import SolarmanAuth

            auth = SolarmanAuth(settings)
            token = auth.obtain_token()
            assert token.access_token == "new-token-xyz"
            mock_post.assert_called_once()

    def test_obtain_token_auth_failure(self, settings: SolarmanSettings) -> None:
        mock_response = httpx.Response(
            401, json={"msg": "Invalid credentials", "requestId": "req-1"}
        )
        with patch("httpx.post", return_value=mock_response):
            from solgreen.integrations.solarman.auth import SolarmanAuth

            auth = SolarmanAuth(settings)
            with pytest.raises(SolarmanAuthenticationError):
                auth.obtain_token()

    def test_obtain_token_server_error(self, settings: SolarmanSettings) -> None:
        mock_response = httpx.Response(500, json={"msg": "Internal error"})
        with patch("httpx.post", return_value=mock_response):
            from solgreen.integrations.solarman.auth import SolarmanAuth

            auth = SolarmanAuth(settings)
            with pytest.raises(SolarmanServerError):
                auth.obtain_token()

    def test_timeout_raises_timeout_error(self, settings: SolarmanSettings) -> None:
        from solgreen.integrations.solarman.auth import SolarmanAuth

        with patch("httpx.post", side_effect=httpx.TimeoutException("connection timeout")):
            auth = SolarmanAuth(settings)
            with pytest.raises(SolarmanTimeoutError):
                auth.obtain_token()

    def test_read_only_violation_raises(self, settings: SolarmanSettings) -> None:
        with patch("httpx.post"):
            client = SolarmanClient(settings)
            with pytest.raises(ReadOnlyViolationError) as exc_info:
                client._request("POST", "device/v1.0/create")
            assert "read-only" in str(exc_info.value).lower()

    def test_list_station_devices_response_parsing(self) -> None:
        from solgreen.integrations.solarman.models import DeviceInfo

        resp_data = {
            "total": 2,
            "deviceListItems": [
                {
                    "deviceId": 240607325,
                    "deviceSn": "3541560332",
                    "deviceType": "COLLECTOR",
                    "connectStatus": 1,
                    "collectionTime": 1784769998,
                },
                {
                    "deviceId": 264283253,
                    "deviceSn": "SR-2411060049-301530",
                    "deviceType": "INVERTER",
                    "connectStatus": 1,
                    "collectionTime": 1784769998,
                },
            ],
        }
        items = resp_data.get("deviceListItems", [])
        devices = [DeviceInfo.model_validate(d) for d in items]
        assert len(devices) == 2
        assert devices[0].device_id == "240607325"
        assert devices[0].device_sn == "3541560332"
        assert devices[0].device_type == "COLLECTOR"
        assert devices[0].status == 1
        assert devices[1].device_id == "264283253"
        assert devices[1].device_sn == "SR-2411060049-301530"
        assert devices[1].device_type == "INVERTER"
        assert devices[1].status == 1

    def test_get_device_current_data_response_parsing(self) -> None:
        from solgreen.integrations.solarman.models import CurrentDataRecord

        resp_data = {
            "deviceId": 264283253,
            "deviceSn": "SR-2411060049-301530",
            "deviceType": "INVERTER",
            "deviceState": 1,
            "collectionTime": 1784769998,
            "dataList": [
                {"key": "PV_O_C_V", "value": "550", "unit": "V", "name": "PV Open Circuit Voltage"},
                {"key": "P_ro2", "value": "8000.00", "unit": "W", "name": "Rated Output Power"},
                {"key": "BCS1", "value": "75", "unit": "%", "name": "Battery State of Charge"},
            ],
        }
        record = CurrentDataRecord.model_validate(resp_data)
        assert record.device_id == "264283253"
        assert record.device_sn == "SR-2411060049-301530"
        assert record.device_type == "INVERTER"
        assert record.device_state == 1
        assert record.collection_time == 1784769998
        assert len(record.data_list) == 3
        assert record.data_list[0]["key"] == "PV_O_C_V"
        assert record.data_list[1]["key"] == "P_ro2"
        assert record.data_list[2]["key"] == "BCS1"


class TestDeviceModels:
    def test_device_info_int_device_id_coerced_to_str(self) -> None:
        from solgreen.integrations.solarman.models import DeviceInfo

        device = DeviceInfo.model_validate(
            {
                "deviceId": 240607325,
                "deviceSn": "3541560332",
                "deviceType": "COLLECTOR",
                "connectStatus": 1,
            }
        )
        assert device.device_id == "240607325"
        assert isinstance(device.device_id, str)

    def test_device_info_connect_status_alias(self) -> None:
        from solgreen.integrations.solarman.models import DeviceInfo

        device = DeviceInfo.model_validate(
            {
                "deviceId": 123,
                "deviceSn": "TEST",
                "deviceType": "INVERTER",
                "connectStatus": 1,
            }
        )
        assert device.status == 1

    def test_current_data_record_int_device_id_coerced(self) -> None:
        from solgreen.integrations.solarman.models import CurrentDataRecord

        record = CurrentDataRecord.model_validate(
            {
                "deviceId": 264283253,
                "deviceSn": "TEST",
                "deviceType": "INVERTER",
                "deviceState": 1,
                "collectionTime": 1784769998,
                "dataList": [{"key": "PV_O_C_V", "value": "550", "unit": "V", "name": "PV"}],
            }
        )
        assert record.device_id == "264283253"
        assert isinstance(record.device_id, str)


class TestHistoricalQuery:
    def test_valid_query(self) -> None:
        q = HistoricalQuery(
            device_id="dev-123",
            station_id="sta-456",
            start_time=datetime(2026, 7, 1, tzinfo=UTC),
            end_time=datetime(2026, 7, 2, tzinfo=UTC),
        )
        assert q.start_iso() == "2026-07-01T00:00:00+00:00"
        assert q.end_iso() == "2026-07-02T00:00:00+00:00"

    def test_invalid_range_raises(self) -> None:
        with pytest.raises(ValueError, match=r"end.*must be after.*start"):
            HistoricalQuery(
                device_id="dev-123",
                station_id="sta-456",
                start_time=datetime(2026, 7, 2, tzinfo=UTC),
                end_time=datetime(2026, 7, 1, tzinfo=UTC),
            )


# ---------------------------------------------------------------------------
# Error hierarchy tests
# ---------------------------------------------------------------------------


class TestErrors:
    def test_solarman_error_request_id(self) -> None:
        err = SolarmanAuthenticationError("fail", request_id="req-123")
        assert err.request_id == "req-123"

    def test_rate_limit_error_retry_after(self) -> None:
        err = SolarmanRateLimitError("rate limited", retry_after=30.0)
        assert err.retry_after == 30.0

    def test_read_only_violation(self) -> None:
        err = ReadOnlyViolationError(operation="POST", endpoint="device/v1.0/create")
        assert "read-only" in str(err).lower()
        assert err.operation == "POST"
        assert err.endpoint == "device/v1.0/create"


# ---------------------------------------------------------------------------
# Privacy tests — no secrets in code/fixtures
# ---------------------------------------------------------------------------


class TestNoSecretsInCode:
    def test_no_real_credentials_in_tests(self) -> None:
        import solgreen.integrations.solarman as sm

        if hasattr(sm, "__file__") and sm.__file__:
            with open(sm.__file__) as f:
                src = f.read()
        else:
            src = ""
        sensitive = ["my-secret", "my-app-id", "test@example.com", "secret123"]
        for secret in sensitive:
            assert secret not in src, f"Secret '{secret}' found in module source"
