"""Tests for MikrotikConfig validation and settings."""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.config import McpServerSettings, MikrotikConfig, get_settings


class TestMikrotikConfig:
    """Tests for MikrotikConfig validation."""

    def test_minimal_config_with_required_fields(self) -> None:
        config = MikrotikConfig(
            host="192.168.88.1",
            password="testpass",
        )
        assert config.host == "192.168.88.1"
        assert config.password == "testpass"
        assert config.username == "admin"
        assert config.port == 80
        assert config.use_ssl is False
        assert config.ssl_verify is False

    def test_full_config(self) -> None:
        config = MikrotikConfig(
            host="192.168.88.1",
            username="customuser",
            password="testpass",
            port=8080,
            use_ssl=True,
            ssl_verify=True,
        )
        assert config.host == "192.168.88.1"
        assert config.username == "customuser"
        assert config.port == 8080
        assert config.use_ssl is True
        assert config.ssl_verify is True

    def test_base_url_http(self) -> None:
        config = MikrotikConfig(
            host="192.168.88.1",
            password="testpass",
            port=80,
            use_ssl=False,
        )
        assert config.base_url == "http://192.168.88.1:80"

    def test_base_url_https(self) -> None:
        config = MikrotikConfig(
            host="192.168.88.1",
            password="testpass",
            port=443,
            use_ssl=True,
        )
        assert config.base_url == "https://192.168.88.1:443"

    def test_missing_host_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MikrotikConfig(password="testpass")
        assert "host" in str(exc_info.value)

    def test_missing_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MikrotikConfig(host="192.168.88.1")
        assert "password" in str(exc_info.value)

    def test_invalid_port_too_low(self) -> None:
        with pytest.raises(ValidationError):
            MikrotikConfig(host="192.168.88.1", password="testpass", port=0)

    def test_invalid_port_too_high(self) -> None:
        with pytest.raises(ValidationError):
            MikrotikConfig(host="192.168.88.1", password="testpass", port=65536)

    def test_valid_port_boundary(self) -> None:
        config = MikrotikConfig(host="192.168.88.1", password="testpass", port=1)
        assert config.port == 1
        config = MikrotikConfig(host="192.168.88.1", password="testpass", port=65535)
        assert config.port == 65535


class TestMcpServerSettings:
    """Tests for McpServerSettings validation."""

    def test_defaults(self) -> None:
        settings = McpServerSettings()
        assert settings.transport == "stdio"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

    def test_custom_settings(self) -> None:
        settings = McpServerSettings(
            transport="sse",
            host="127.0.0.1",
            port=9000,
        )
        assert settings.transport == "sse"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000

    def test_invalid_port(self) -> None:
        with pytest.raises(ValidationError):
            McpServerSettings(port=0)
        with pytest.raises(ValidationError):
            McpServerSettings(port=65536)

    def test_invalid_transport(self) -> None:
        with pytest.raises(ValidationError):
            McpServerSettings(transport="invalid")


class TestGetSettings:
    """Tests for get_settings singleton."""

    def test_get_settings_caching(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIKROTIK_HOST", "10.0.0.1")
        monkeypatch.setenv("MIKROTIK_PASSWORD", "cachedpass")

        get_settings.cache_clear()

        config1 = get_settings()
        config2 = get_settings()

        assert config1 is config2
        assert config1.host == "10.0.0.1"

    def test_get_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIKROTIK_HOST", "172.16.0.1")
        monkeypatch.setenv("MIKROTIK_PASSWORD", "envpass")
        monkeypatch.setenv("MIKROTIK_USERNAME", "envuser")
        monkeypatch.setenv("MIKROTIK_PORT", "8080")

        get_settings.cache_clear()

        config = get_settings()

        assert config.host == "172.16.0.1"
        assert config.password == "envpass"
        assert config.username == "envuser"
        assert config.port == 8080

    def test_mcp_settings_defaults(self) -> None:
        config = MikrotikConfig(host="192.168.88.1", password="testpass")
        assert config.mcp.transport == "stdio"
        assert config.mcp.host == "0.0.0.0"
        assert config.mcp.port == 8000

    def test_mcp_settings_custom(self) -> None:
        config = MikrotikConfig(
            host="192.168.88.1",
            password="testpass",
            mcp=McpServerSettings(transport="sse", port=9000),
        )
        assert config.mcp.transport == "sse"
        assert config.mcp.port == 9000
