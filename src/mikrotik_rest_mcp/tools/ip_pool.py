"""Bespoke IP-pool tools.

Pool CRUD is registered from submenus. This module holds tools that don't fit
the Submenu shape: listing used addresses, and appending ranges to an
existing pool.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from ..app import READ, WRITE
from ..exceptions import MikrotikNotFound
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_ip_pool_used", annotations=READ)
    async def list_ip_pool_used(
        pool_name: str | None = None,
        address_filter: str | None = None,
        mac_filter: str | None = None,
        info_filter: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List used addresses from IP pools."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool/used") or []
        filtered = rows
        if pool_name:
            filtered = [r for r in filtered if r.get("pool") == pool_name]
        if address_filter:
            filtered = [
                r for r in filtered if address_filter in str(r.get("address", ""))
            ]
        if mac_filter:
            filtered = [
                r
                for r in filtered
                if mac_filter.lower() in str(r.get("info", "")).lower()
            ]
        if info_filter:
            filtered = [
                r
                for r in filtered
                if info_filter.lower() in str(r.get("info", "")).lower()
            ]
        return filtered

    @mcp.tool(name="mikrotik_expand_ip_pool", annotations=WRITE)
    async def expand_ip_pool(
        name: Annotated[str, Field(min_length=1)],
        additional_ranges: Annotated[str, Field(min_length=3)],
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Expand an existing IP pool by appending more ranges."""
        manager = get_manager(ctx)
        rows = await manager.get_list("ip/pool")
        current_ranges = ""
        pool_id = None
        for p in rows:
            if p.get("name") == name:
                current_ranges = p.get("ranges", "")
                pool_id = p.get(".id")
                break
        if not pool_id:
            raise MikrotikNotFound("ip/pool", name)
        new_ranges = (
            f"{current_ranges},{additional_ranges}"
            if current_ranges
            else additional_ranges
        )
        await manager.patch(f"ip/pool/{pool_id}", json={"ranges": new_ranges})
        return {"expanded": True, "id": pool_id, "new_ranges": new_ranges}
