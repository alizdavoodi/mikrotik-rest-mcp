"""Tests for MikrotikMcpError exceptions."""

from __future__ import annotations

import pytest

from mikrotik_rest_mcp.exceptions import (
    MikrotikConnectionError,
    MikrotikMcpError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_mikrotik_mcp_error_is_base(self) -> None:
        assert issubclass(MikrotikConnectionError, MikrotikMcpError)

    def test_connection_error_message(self) -> None:
        error = MikrotikConnectionError("Failed to connect")
        assert str(error) == "Failed to connect"

    def test_catch_base_class(self) -> None:
        with pytest.raises(MikrotikMcpError):
            raise MikrotikConnectionError("connection error")

    def test_catch_specific_class(self) -> None:
        with pytest.raises(MikrotikConnectionError):
            raise MikrotikConnectionError("connection error")

    def test_different_exception_types(self) -> None:
        try:
            raise MikrotikConnectionError("error")
        except MikrotikMcpError as e:
            assert isinstance(e, MikrotikConnectionError)
