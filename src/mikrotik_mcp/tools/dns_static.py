from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class DnsStaticCreate(BaseModel):
    name: str = Field(min_length=1)
    address: str | None = None
    cname: str | None = None
    ttl: str | None = None
    comment: str | None = None
    disabled: bool = False
    regexp: str | None = None


class DnsStaticUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    cname: str | None = None
    ttl: str | None = None
    comment: str | None = None
    disabled: bool | None = None
    regexp: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_dns_static", annotations=READ)
    async def list_dns_static(
        name_filter: str | None = None,
        address_filter: str | None = None,
        type_filter: str | None = None,
        disabled_only: bool = False,
        regexp_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists static DNS entries."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/dns/static") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if address_filter:
            filtered = [
                r for r in filtered if address_filter in str(r.get("address", ""))
            ]
        if type_filter:
            filtered = [r for r in filtered if r.get("type") == type_filter]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if regexp_only:
            filtered = [r for r in filtered if bool(r.get("regexp"))]
        return filtered

    @mcp.tool(name="mikrotik_get_dns_static", annotations=READ)
    async def get_dns_static(
        entry_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets details of a specific static DNS entry."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/dns/static/{entry_id}")
        if not result:
            raise ValueError(f"DNS static entry not found: {entry_id}")
        return result

    @mcp.tool(name="mikrotik_add_dns_static", annotations=WRITE)
    async def add_dns_static(
        name: Annotated[str, Field(min_length=1)],
        address: str | None = None,
        cname: str | None = None,
        ttl: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        regexp: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds a static DNS entry."""
        manager = get_manager(ctx)
        payload = DnsStaticCreate(
            name=name,
            address=address,
            cname=cname,
            ttl=ttl,
            comment=comment,
            disabled=disabled,
            regexp=regexp,
        ).model_dump(exclude_none=True)
        if "disabled" in payload:
            payload["disabled"] = "true" if payload["disabled"] else "false"
        result = await manager.put("ip/dns/static", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_update_dns_static", annotations=WRITE)
    async def update_dns_static(
        entry_id: Annotated[str, Field(min_length=1)],
        name: str | None = None,
        address: str | None = None,
        cname: str | None = None,
        ttl: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        regexp: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing static DNS entry."""
        manager = get_manager(ctx)
        payload = DnsStaticUpdate(
            name=name,
            address=address,
            cname=cname,
            ttl=ttl,
            comment=comment,
            disabled=disabled,
            regexp=regexp,
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        if "disabled" in payload:
            payload["disabled"] = "true" if payload["disabled"] else "false"
        await manager.patch(f"ip/dns/static/{entry_id}", json=payload)
        return {"updated": True, "id": entry_id}

    @mcp.tool(name="mikrotik_remove_dns_static", annotations=DESTRUCTIVE)
    async def remove_dns_static(
        entry_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a static DNS entry."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/dns/static/{entry_id}")
        return {"removed": True, "id": entry_id}

    @mcp.tool(name="mikrotik_enable_dns_static", annotations=WRITE)
    async def enable_dns_static(
        entry_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Enables a static DNS entry."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/dns/static/{entry_id}", json={"disabled": "false"})
        return {"enabled": True, "id": entry_id}

    @mcp.tool(name="mikrotik_disable_dns_static", annotations=WRITE)
    async def disable_dns_static(
        entry_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables a static DNS entry."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/dns/static/{entry_id}", json={"disabled": "true"})
        return {"disabled": True, "id": entry_id}
