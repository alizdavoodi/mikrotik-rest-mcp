"""Tests for MikrotikMcpError exceptions."""

from __future__ import annotations

from mikrotik_rest_mcp.exceptions import (
    MikrotikConnectionError,
    MikrotikMcpError,
)


def test_mikrotik_mcp_error_is_base() -> None:
    assert issubclass(MikrotikConnectionError, MikrotikMcpError)
