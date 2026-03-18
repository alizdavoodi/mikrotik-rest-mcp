"""Tests for tools/__init__.py helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastmcp import Context
from fastmcp.exceptions import ToolError

from mikrotik_rest_mcp.connection import MikrotikConnectionManager
from mikrotik_rest_mcp.tools import get_manager


class TestGetManager:
    """Tests for get_manager helper function."""

    def test_get_manager_returns_connection_manager(self) -> None:
        mock_manager = MagicMock(spec=MikrotikConnectionManager)
        ctx = MagicMock(spec=Context)
        ctx.lifespan_context = {"connection_manager": mock_manager}

        result = get_manager(ctx)

        assert result is mock_manager

    def test_get_manager_raises_when_missing(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.lifespan_context = {}

        with pytest.raises(ToolError) as exc_info:
            get_manager(ctx)

        assert "connection manager is not available" in str(exc_info.value)

    def test_get_manager_raises_when_wrong_type(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.lifespan_context = {"connection_manager": "not a manager"}

        with pytest.raises(ToolError) as exc_info:
            get_manager(ctx)

        assert "connection manager is not available" in str(exc_info.value)
