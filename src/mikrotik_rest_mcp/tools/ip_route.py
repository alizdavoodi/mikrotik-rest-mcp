from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class IpRouteCreate(BaseModel):
    dst_address: str = Field(min_length=3)
    gateway: str = Field(min_length=1)
    distance: int | None = Field(default=None, ge=1, le=255)
    scope: int | None = None
    target_scope: int | None = None
    routing_mark: str | None = None
    comment: str | None = None
    disabled: bool = False
    vrf_interface: str | None = None
    pref_src: str | None = None
    check_gateway: str | None = None


class IpRouteUpdate(BaseModel):
    dst_address: str | None = None
    gateway: str | None = None
    distance: int | None = Field(default=None, ge=1, le=255)
    scope: int | None = None
    target_scope: int | None = None
    routing_mark: str | None = None
    comment: str | None = None
    disabled: bool | None = None
    vrf_interface: str | None = None
    pref_src: str | None = None
    check_gateway: str | None = None


def _filter_routes(
    rows: list[dict[str, Any]],
    dst_filter: str | None,
    gateway_filter: str | None,
    routing_mark_filter: str | None,
    distance_filter: int | None,
    active_only: bool,
    disabled_only: bool,
    dynamic_only: bool,
    static_only: bool,
) -> list[dict[str, Any]]:
    filtered = rows
    if dst_filter:
        filtered = [r for r in filtered if dst_filter in str(r.get("dst-address", ""))]
    if gateway_filter:
        filtered = [r for r in filtered if gateway_filter in str(r.get("gateway", ""))]
    if routing_mark_filter:
        filtered = [r for r in filtered if r.get("routing-mark") == routing_mark_filter]
    if distance_filter is not None:
        filtered = [
            r for r in filtered if str(distance_filter) == str(r.get("distance"))
        ]
    if active_only:
        filtered = [r for r in filtered if r.get("active") == "true"]
    if disabled_only:
        filtered = [r for r in filtered if r.get("disabled") == "true"]
    if dynamic_only:
        filtered = [r for r in filtered if r.get("dynamic") == "true"]
    if static_only:
        filtered = [r for r in filtered if r.get("static") == "true"]
    return filtered


def _convert_create_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = {}
    if "dst_address" in payload:
        result["dst-address"] = payload.pop("dst_address")
    if "target_scope" in payload:
        result["target-scope"] = payload.pop("target_scope")
    if "routing_mark" in payload:
        result["routing-mark"] = payload.pop("routing_mark")
    if "vrf_interface" in payload:
        result["vrf-interface"] = payload.pop("vrf_interface")
    if "pref_src" in payload:
        result["pref-src"] = payload.pop("pref_src")
    if "check_gateway" in payload:
        result["check-gateway"] = payload.pop("check_gateway")
    result.update(payload)
    if "disabled" in result:
        result["disabled"] = "true" if result["disabled"] else "false"
    return result


def _convert_update_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = {}
    if "dst_address" in payload:
        result["dst-address"] = payload.pop("dst_address")
    if "target_scope" in payload:
        result["target-scope"] = payload.pop("target_scope")
    if "routing_mark" in payload:
        result["routing-mark"] = payload.pop("routing_mark")
    if "vrf_interface" in payload:
        result["vrf-interface"] = payload.pop("vrf_interface")
    if "pref_src" in payload:
        result["pref-src"] = payload.pop("pref_src")
    if "check_gateway" in payload:
        result["check-gateway"] = payload.pop("check_gateway")
    result.update(payload)
    if "disabled" in result:
        result["disabled"] = "true" if result["disabled"] else "false"
    return result


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_routes", annotations=READ)
    async def list_routes(
        dst_filter: str | None = None,
        gateway_filter: str | None = None,
        routing_mark_filter: str | None = None,
        distance_filter: int | None = None,
        active_only: bool = False,
        disabled_only: bool = False,
        dynamic_only: bool = False,
        static_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists routes from the routing table."""
        manager = get_manager(ctx)
        routes = await manager.get("ip/route")
        if not routes:
            return []
        return _filter_routes(
            rows=routes,
            dst_filter=dst_filter,
            gateway_filter=gateway_filter,
            routing_mark_filter=routing_mark_filter,
            distance_filter=distance_filter,
            active_only=active_only,
            disabled_only=disabled_only,
            dynamic_only=dynamic_only,
            static_only=static_only,
        )

    @mcp.tool(name="mikrotik_get_route", annotations=READ)
    async def get_route(
        route_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific route."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/route/{route_id}")
        if not isinstance(result, dict):
            raise ValueError(f"Route not found: {route_id}")
        return result

    @mcp.tool(name="mikrotik_add_route", annotations=WRITE)
    async def add_route(
        dst_address: Annotated[str, Field(min_length=3)],
        gateway: Annotated[str, Field(min_length=1)],
        distance: int | None = None,
        scope: int | None = None,
        target_scope: int | None = None,
        routing_mark: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        vrf_interface: str | None = None,
        pref_src: str | None = None,
        check_gateway: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds a route to the routing table."""
        manager = get_manager(ctx)
        payload = IpRouteCreate(
            dst_address=dst_address,
            gateway=gateway,
            distance=distance,
            scope=scope,
            target_scope=target_scope,
            routing_mark=routing_mark,
            comment=comment,
            disabled=disabled,
            vrf_interface=vrf_interface,
            pref_src=pref_src,
            check_gateway=check_gateway,
        ).model_dump(exclude_none=True)
        payload = _convert_create_payload(payload)
        result = await manager.put("ip/route", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_update_route", annotations=WRITE)
    async def update_route(
        route_id: Annotated[str, Field(min_length=1)],
        dst_address: str | None = None,
        gateway: str | None = None,
        distance: int | None = None,
        scope: int | None = None,
        target_scope: int | None = None,
        routing_mark: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        vrf_interface: str | None = None,
        pref_src: str | None = None,
        check_gateway: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing route."""
        manager = get_manager(ctx)
        payload = IpRouteUpdate(
            dst_address=dst_address,
            gateway=gateway,
            distance=distance,
            scope=scope,
            target_scope=target_scope,
            routing_mark=routing_mark,
            comment=comment,
            disabled=disabled,
            vrf_interface=vrf_interface,
            pref_src=pref_src,
            check_gateway=check_gateway,
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        payload = _convert_update_payload(payload)
        await manager.patch(f"ip/route/{route_id}", json=payload)
        return {"updated": True, "id": route_id}

    @mcp.tool(name="mikrotik_remove_route", annotations=DESTRUCTIVE)
    async def remove_route(
        route_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a route."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/route/{route_id}")
        return {"removed": True, "id": route_id}

    @mcp.tool(name="mikrotik_enable_route", annotations=WRITE)
    async def enable_route(
        route_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Enables a route."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/route/{route_id}", json={"disabled": "false"})
        return {"enabled": True, "id": route_id}

    @mcp.tool(name="mikrotik_disable_route", annotations=WRITE)
    async def disable_route(
        route_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables a route."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/route/{route_id}", json={"disabled": "true"})
        return {"disabled": True, "id": route_id}

    @mcp.tool(name="mikrotik_get_routing_table", annotations=READ)
    async def get_routing_table(
        table_name: str | None = "main",
        protocol_filter: str | None = None,
        active_only: bool = True,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Gets a specific routing table."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("ip/route")
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
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
        """Checks the route path to a destination."""
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
        """Gets the route cache."""
        manager = get_manager(ctx)
        return await manager.get("ip/route/cache") or []

    @mcp.tool(name="mikrotik_flush_route_cache", annotations=WRITE)
    async def flush_route_cache(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Flushes the route cache."""
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
        """Adds a default route."""
        manager = get_manager(ctx)
        payload = {
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
        """Adds a blackhole route."""
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
        """Gets routing table statistics."""
        manager = get_manager(ctx)
        routes = await manager.get("ip/route") or []
        return {
            "total": len(routes),
            "active": len([r for r in routes if r.get("active") == "true"]),
            "disabled": len([r for r in routes if r.get("disabled") == "true"]),
            "dynamic": len([r for r in routes if r.get("dynamic") == "true"]),
            "static": len([r for r in routes if r.get("static") == "true"]),
        }
