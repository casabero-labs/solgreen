from solgreen.sanitization import sanitize_error


class TestSanitizeError:
    def test_postgresql_dsn(self) -> None:
        msg = "connection failed: postgresql://user:secret123@host:5432/mydb"
        result = sanitize_error(msg)
        assert "secret123" not in result
        assert "mydb" not in result
        assert "postgresql" in result.lower()

    def test_password_redaction(self) -> None:
        msg = "auth failed: password=mysecretpass"
        result = sanitize_error(msg)
        assert "mysecretpass" not in result
        assert "password" in result.lower()

    def test_token_redaction(self) -> None:
        msg = "api error: token=ghp_abc123xyz"
        result = sanitize_error(msg)
        assert "ghp_abc123xyz" not in result
        assert "token" in result.lower()

    def test_app_secret_redaction(self) -> None:
        msg = "config error: app_secret=my_app_secret_value"
        result = sanitize_error(msg)
        assert "my_app_secret_value" not in result

    def test_station_id_redaction(self) -> None:
        msg = "station_id=abc123def456 not found"
        result = sanitize_error(msg)
        assert "abc123def456" not in result
        assert "ST****" in result

    def test_device_sn_redaction(self) -> None:
        msg = "device_sn=XYZ123ABC789 invalid"
        result = sanitize_error(msg)
        assert "XYZ123ABC789" not in result
        assert "SN****" in result

    def test_email_redaction(self) -> None:
        msg = "user error: test@example.com not found"
        result = sanitize_error(msg)
        assert "test@example.com" not in result
        assert "***@***.***" in result

    def test_multiple_secrets(self) -> None:
        msg = "dsn=postgresql://user:pass@host/db token=abc123 email=test@test.com"
        result = sanitize_error(msg)
        assert "pass" not in result
        assert "abc123" not in result
        assert "test@test.com" not in result

    def test_clean_message_unchanged(self) -> None:
        msg = "connection timeout after 30s"
        result = sanitize_error(msg)
        assert result == msg

    def test_unicode_email(self) -> None:
        msg = "error: user@example.com"
        result = sanitize_error(msg)
        assert "user@example.com" not in result
        assert "***@***.***" in result
