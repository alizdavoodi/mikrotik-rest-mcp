from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class DhcpPoolCreate(BaseModel):
    name: str
    ranges: str
    next_pool: str | None = None
    comment: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_dhcp_pools", annotations=READ)
    async def list_dhcp_pools(
        name_filter: str | None = None,
        ranges_filter: str | None = None,
        include_used: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List DHCP address pools."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if ranges_filter:
            filtered = [
                r for r in filtered if ranges_filter in str(r.get("ranges", ""))
            ]
        if include_used:
            used = await manager.get("ip/pool/used") or []
            used_map: dict[str, list[dict[str, Any]]] = {}
            for entry in used:
                used_map.setdefault(str(entry.get("pool", "")), []).append(entry)
            for item in filtered:
                item["used_entries"] = used_map.get(str(item.get("name", "")), [])
        return filtered

    @mcp.tool(name="mikrotik_get_dhcp_pool", annotations=READ)
    async def get_dhcp_pool(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get one DHCP pool by name."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool", params={"name": name}) or []
        if not rows:
            raise ValueError(f"DHCP pool not found: {name}")
        return rows[0]

    @mcp.tool(name="mikrotik_create_dhcp_pool", annotations=WRITE)
    async def create_dhcp_pool(
        name: str,
        ranges: str,
        next_pool: str | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create DHCP pool entry."""
        manager = get_manager(ctx)
        payload = DhcpPoolCreate(
            name=name, ranges=ranges, next_pool=next_pool, comment=comment
        ).model_dump(exclude_none=True)
        if "next_pool" in payload:
            payload["next-pool"] = payload.pop("next_pool")
        result = await manager.put("ip/pool", json=payload)
        return {"created": True, "id": result.get(".id") if result else name}

    @mcp.tool(name="mikrotik_remove_dhcp_pool", annotations=DESTRUCTIVE)
    async def remove_dhcp_pool(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove DHCP pool by name."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool", params={"name": name}) or []
        if not rows:
            raise ValueError(f"DHCP pool not found: {name}")
        pool_id = str(rows[0].get(".id"))
        await manager.delete(f"ip/pool/{pool_id}")
        return {"removed": True, "id": pool_id}

    @mcp.tool(name="mikrotik_update_dhcp_pool", annotations=WRITE)
    async def update_dhcp_pool(
        name: str,
        new_name: str | None = None,
        ranges: str | None = None,
        next_pool: str | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update DHCP pool by name."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool", params={"name": name}) or []
        if not rows:
            raise ValueError(f"DHCP pool not found: {name}")
        pool_id = str(rows[0].get(".id"))
        payload: dict[str, Any] = {}
        if new_name is not None:
            payload["name"] = new_name
        if ranges is not None:
            payload["ranges"] = ranges
        if next_pool is not None:
            payload["next-pool"] = next_pool
        if comment is not None:
            payload["comment"] = comment
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"ip/pool/{pool_id}", json=payload)
        return {"updated": True, "id": pool_id}
