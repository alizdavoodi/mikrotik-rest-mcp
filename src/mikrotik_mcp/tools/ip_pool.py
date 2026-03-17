from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class PoolCreate(BaseModel):
    name: str = Field(min_length=1)
    ranges: str = Field(min_length=3)
    next_pool: str | None = None
    comment: str | None = None


class PoolUpdate(BaseModel):
    new_name: str | None = None
    ranges: str | None = None
    next_pool: str | None = None
    comment: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_ip_pools", annotations=READ)
    async def list_ip_pools(
        name_filter: str | None = None,
        ranges_filter: str | None = None,
        include_used: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists IP pools on MikroTik device."""
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
            for item in used:
                used_map.setdefault(str(item.get("pool", "")), []).append(item)
            for item in filtered:
                item["used_entries"] = used_map.get(str(item.get("name", "")), [])
        return filtered

    @mcp.tool(name="mikrotik_get_ip_pool", annotations=READ)
    async def get_ip_pool(
        name: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific IP pool."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool") or []
        for pool in rows:
            if pool.get("name") == name:
                return pool
        raise ValueError(f"IP pool not found: {name}")

    @mcp.tool(name="mikrotik_create_ip_pool", annotations=WRITE)
    async def create_ip_pool(
        name: Annotated[str, Field(min_length=1)],
        ranges: Annotated[str, Field(min_length=3)],
        next_pool: str | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Creates an IP pool on MikroTik device."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {"name": name, "ranges": ranges}
        if next_pool:
            payload["next-pool"] = next_pool
        if comment:
            payload["comment"] = comment
        result = await manager.put("ip/pool", json=payload)
        return (
            {"created": True, "id": result.get(".id")} if result else {"created": True}
        )

    @mcp.tool(name="mikrotik_update_ip_pool", annotations=WRITE)
    async def update_ip_pool(
        name: Annotated[str, Field(min_length=1)],
        new_name: str | None = None,
        ranges: str | None = None,
        next_pool: str | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing IP pool on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool") or []
        pool_id = None
        for pool in rows:
            if pool.get("name") == name:
                pool_id = pool.get(".id")
                break
        if not pool_id:
            raise ValueError(f"IP pool not found: {name}")
        payload: dict[str, Any] = {}
        if new_name:
            payload["name"] = new_name
        if ranges:
            payload["ranges"] = ranges
        if next_pool:
            payload["next-pool"] = next_pool
        if comment:
            payload["comment"] = comment
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"ip/pool/{pool_id}", json=payload)
        return {"updated": True, "id": pool_id}

    @mcp.tool(name="mikrotik_remove_ip_pool", annotations=DESTRUCTIVE)
    async def remove_ip_pool(
        name: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes an IP pool from MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool") or []
        pool_id = None
        for pool in rows:
            if pool.get("name") == name:
                pool_id = pool.get(".id")
                break
        if not pool_id:
            raise ValueError(f"IP pool not found: {name}")
        await manager.delete(f"ip/pool/{pool_id}")
        return {"removed": True, "id": pool_id}

    @mcp.tool(name="mikrotik_list_ip_pool_used", annotations=READ)
    async def list_ip_pool_used(
        pool_name: str | None = None,
        address_filter: str | None = None,
        mac_filter: str | None = None,
        info_filter: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists used addresses from IP pools."""
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
        """Expands an existing IP pool by adding more ranges."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/pool") or []
        pool = None
        pool_id = None
        for p in rows:
            if p.get("name") == name:
                pool = p
                pool_id = p.get(".id")
                break
        if not pool_id:
            raise ValueError(f"IP pool not found: {name}")
        current_ranges = pool.get("ranges", "")
        new_ranges = (
            f"{current_ranges},{additional_ranges}"
            if current_ranges
            else additional_ranges
        )
        await manager.patch(f"ip/pool/{pool_id}", json={"ranges": new_ranges})
        return {"expanded": True, "id": pool_id, "new_ranges": new_ranges}
