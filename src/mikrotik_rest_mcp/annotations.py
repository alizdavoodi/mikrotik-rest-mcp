"""MCP tool annotation presets describing the side-effect class of a tool."""

from __future__ import annotations

from typing import Any

READ: dict[str, Any] = {"readOnlyHint": True, "destructiveHint": False}
WRITE: dict[str, Any] = {"readOnlyHint": False, "destructiveHint": False}
DESTRUCTIVE: dict[str, Any] = {"readOnlyHint": False, "destructiveHint": True}
