"""Bespoke system_users tools.

User CRUD and group CRUD are registered from submenus. This module holds the
read-only ``mikrotik_get_active_users`` tool, which queries a session-like
endpoint (``/user/active``) rather than a CRUD submenu.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext

from ..app import READ
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_get_active_users", annotations=READ)
    async def get_active_users(ctx: Context = CurrentContext()) -> list[dict[str, Any]]:
        """Get currently active/logged-in users."""
        manager = get_manager(ctx)
        return await manager.get("user/active") or []
