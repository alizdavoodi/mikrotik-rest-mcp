"""Pytest fixtures for MikroTik MCP server testing."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import Context

from mikrotik_rest_mcp.config import McpServerSettings, MikrotikConfig
from mikrotik_rest_mcp.connection import MikrotikConnectionManager


@pytest.fixture
def mock_settings() -> MikrotikConfig:
    """Create mock settings for testing."""
    return MikrotikConfig(
        host="192.168.88.1",
        username="admin",
        password="testpassword",
        port=80,
        use_ssl=False,
        ssl_verify=False,
        mcp=McpServerSettings(
            transport="stdio",
            host="0.0.0.0",
            port=8000,
        ),
    )


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Create mock httpx.AsyncClient for HTTP testing."""
    client = AsyncMock()
    client.request = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_connection_manager(mock_settings: MikrotikConfig) -> AsyncMock:
    """Create mock MikrotikConnectionManager for testing tools.

    This fixture provides a mock connection manager with all HTTP methods
    pre-configured as AsyncMock. Use this to test tool functions in isolation.
    """
    manager = AsyncMock(spec=MikrotikConnectionManager)
    manager.get = AsyncMock(return_value=[])
    manager.put = AsyncMock(return_value={".id": "*1"})
    manager.patch = AsyncMock(return_value={})
    manager.delete = AsyncMock(return_value={})
    manager.post = AsyncMock(return_value={})
    manager.request = AsyncMock(return_value={})
    return manager


@pytest.fixture
def mock_context(mock_connection_manager: AsyncMock) -> MagicMock:
    """Create mock FastMCP Context for testing tools.

    This fixture creates a Context mock with lifespan_context dict
    containing the mock connection manager. Pass this as the `ctx` parameter
    to tool functions.

    Usage:
        @pytest.mark.asyncio
        async def test_my_tool(mock_context):
            result = await my_tool(ctx=mock_context)
            assert result == expected
    """
    ctx = MagicMock(spec=Context)
    ctx.lifespan_context = {"connection_manager": mock_connection_manager}
    return ctx


@pytest.fixture
def sample_ip_address() -> dict[str, Any]:
    """Sample IP address response from RouterOS API."""
    return {
        ".id": "*1",
        "address": "192.168.88.1/24",
        "network": "192.168.88.0",
        "interface": "ether1",
        "disabled": "false",
        "dynamic": "false",
        "comment": "LAN gateway",
    }


@pytest.fixture
def sample_ip_addresses() -> list[dict[str, Any]]:
    """Sample list of IP addresses from RouterOS API."""
    return [
        {
            ".id": "*1",
            "address": "192.168.88.1/24",
            "network": "192.168.88.0",
            "interface": "ether1",
            "disabled": "false",
            "dynamic": "false",
        },
        {
            ".id": "*2",
            "address": "10.0.0.1/24",
            "network": "10.0.0.0",
            "interface": "ether2",
            "disabled": "true",
            "dynamic": "false",
        },
        {
            ".id": "*3",
            "address": "192.168.1.1/24",
            "network": "192.168.1.0",
            "interface": "ether1",
            "disabled": "false",
            "dynamic": "true",
        },
    ]


@pytest.fixture
def sample_firewall_rule() -> dict[str, Any]:
    """Sample firewall filter rule from RouterOS API."""
    return {
        ".id": "*1",
        "chain": "input",
        "action": "accept",
        "src-address": "192.168.88.0/24",
        "dst-address": None,
        "protocol": "tcp",
        "dst-port": "22",
        "in-interface": "ether1",
        "out-interface": None,
        "connection-state": "established,related",
        "disabled": "false",
        "comment": "Allow SSH from LAN",
    }


@pytest.fixture
def sample_firewall_rules() -> list[dict[str, Any]]:
    """Sample list of firewall filter rules from RouterOS API."""
    return [
        {
            ".id": "*1",
            "chain": "input",
            "action": "accept",
            "connection-state": "established,related",
            "disabled": "false",
        },
        {
            ".id": "*2",
            "chain": "input",
            "action": "accept",
            "protocol": "icmp",
            "disabled": "false",
        },
        {
            ".id": "*3",
            "chain": "input",
            "action": "drop",
            "in-interface": "ether1",
            "disabled": "true",
        },
        {
            ".id": "*4",
            "chain": "forward",
            "action": "accept",
            "connection-state": "established,related",
            "disabled": "false",
        },
        {
            ".id": "*5",
            "chain": "forward",
            "action": "drop",
            "connection-state": "invalid",
            "dynamic": "true",
        },
    ]
