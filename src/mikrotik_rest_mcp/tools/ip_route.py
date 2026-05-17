"""Bespoke ip/route tools.

Route CRUD is registered from submenus. This module holds tools that don't fit
the Submenu shape: routing table views, route cache, default/blackhole
shortcuts, statistics.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from ..app import READ, WRITE
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_get_routing_table", annotations=READ)
    async def get_routing_table(
        table_name: str | None = "main",
        protocol_filter: str | None = None,
        active_only: bool = True,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Get a specific routing table."""
        manager = get_manager(ctx)
        rows = await manager.get_list("ip/route")
        if not rows:
            return []
        filtered: list[dict[str, Any]] = rows
        if table_name:
            filtered = [
                r for r in filtered if r.get("routing-table", "main") == table_name
            ]
        if protocol_filter:
            filtered = [r for r in filtered if r.get("protocol") == protocol_filter]
        if active_only:
            filtered = [r for r in filtered if r.get("active") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_check_route_path", annotations=READ)
    async def check_route_path(
        destination: Annotated[str, Field(min_length=3)],
        source: str | None = None,
        routing_mark: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Check the route path to a destination."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/route")
        if not rows:
            return {"destination": destination, "source": source, "matches": []}
        active = [r for r in rows if r.get("active") == "true"]
        if routing_mark:
            active = [r for r in active if r.get("routing-mark") == routing_mark]
        matches = [
            r
            for r in active
            if destination in str(r.get("dst-address", ""))
            or r.get("dst-address") == "0.0.0.0/0"
        ]
        return {
            "destination": destination,
            "source": source,
            "routing_mark": routing_mark,
            "matches": matches,
        }

    @mcp.tool(name="mikrotik_get_route_cache", annotations=READ)
    async def get_route_cache(ctx: Context = CurrentContext()) -> list[dict[str, Any]]:
        """Get the route cache."""
        manager = get_manager(ctx)
        return await manager.get("ip/route/cache") or []

    @mcp.tool(name="mikrotik_flush_route_cache", annotations=WRITE)
    async def flush_route_cache(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Flush the route cache."""
        manager = get_manager(ctx)
        await manager.delete("ip/route/cache")
        return {"flushed": True}

    @mcp.tool(name="mikrotik_add_default_route", annotations=WRITE)
    async def add_default_route(
        gateway: Annotated[str, Field(min_length=1)],
        distance: int = 1,
        comment: str | None = None,
        check_gateway: str = "ping",
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Add a default route."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "dst-address": "0.0.0.0/0",
            "gateway": gateway,
            "distance": distance,
            "check-gateway": check_gateway,
        }
        if comment:
            payload["comment"] = comment
        result = await manager.put("ip/route", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_add_blackhole_route", annotations=WRITE)
    async def add_blackhole_route(
        dst_address: Annotated[str, Field(min_length=3)],
        distance: int = 1,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Add a blackhole route."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "dst-address": dst_address,
            "distance": distance,
            "type": "blackhole",
        }
        if comment:
            payload["comment"] = comment
        result = await manager.put("ip/route", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_get_route_statistics", annotations=READ)
    async def get_route_statistics(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Get routing table statistics."""
        manager = get_manager(ctx)
        routes = await manager.get("ip/route") or []
        return {
            "total": len(routes),
            "active": len([r for r in routes if r.get("active") == "true"]),
            "disabled": len([r for r in routes if r.get("disabled") == "true"]),
            "dynamic": len([r for r in routes if r.get("dynamic") == "true"]),
            "static": len([r for r in routes if r.get("static") == "true"]),
        }
