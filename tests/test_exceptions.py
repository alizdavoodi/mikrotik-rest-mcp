"""Tests for MikrotikMcpError exceptions."""

from __future__ import annotations

import pytest

from mikrotik_rest_mcp.exceptions import (
    ConnectionError,
    MikrotikMcpError,
    NotFoundError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_mikrotik_mcp_error_is_base(self) -> None:
        assert issubclass(ConnectionError, MikrotikMcpError)
        assert issubclass(NotFoundError, MikrotikMcpError)
        assert issubclass(ValidationError, MikrotikMcpError)

    def test_connection_error_message(self) -> None:
        error = ConnectionError("Failed to connect")
        assert str(error) == "Failed to connect"

    def test_not_found_error_message(self) -> None:
        error = NotFoundError("Resource not found: *1")
        assert str(error) == "Resource not found: *1"

    def test_validation_error_message(self) -> None:
        error = ValidationError("Invalid configuration")
        assert str(error) == "Invalid configuration"

    def test_catch_base_class(self) -> None:
        with pytest.raises(MikrotikMcpError):
            raise ConnectionError("connection error")

    def test_catch_specific_class(self) -> None:
        with pytest.raises(ConnectionError):
            raise ConnectionError("connection error")

    def test_different_exception_types(self) -> None:
        try:
            raise ConnectionError("error")
        except MikrotikMcpError as e:
            assert isinstance(e, ConnectionError)

        try:
            raise NotFoundError("not found")
        except MikrotikMcpError as e:
            assert isinstance(e, NotFoundError)

        try:
            raise ValidationError("validation failed")
        except MikrotikMcpError as e:
            assert isinstance(e, ValidationError)
