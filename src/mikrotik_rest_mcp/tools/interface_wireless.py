"""Bespoke wireless tools.

Wireless interface CRUD is registered from submenus. This module holds the
scan + registration-table tools, which don't fit the Submenu shape.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext

from ..app import READ
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_scan_wireless_networks", annotations=READ)
    async def scan_wireless_networks(
        interface: str, ctx: Context = CurrentContext()
    ) -> list[dict[str, Any]]:
        """Scan for nearby wireless networks on an interface."""
        manager = get_manager(ctx)
        await manager.post(f"interface/wireless/{interface}/scan", json={})
        rows = await manager.get("interface/wireless/scan") or []
        return rows

    @mcp.tool(name="mikrotik_get_wireless_registration_table", annotations=READ)
    async def get_wireless_registration_table(
        interface: str | None = None, ctx: Context = CurrentContext()
    ) -> list[dict[str, Any]]:
        """Return the wireless registration table (associated clients)."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireless/registration-table") or []
        if interface:
            rows = [row for row in rows if row.get("interface") == interface]
        return rows
