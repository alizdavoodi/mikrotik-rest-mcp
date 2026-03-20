from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class AddressListAdd(BaseModel):
    list_name: str = Field(min_length=1)
    address: str = Field(min_length=3)
    timeout: str | None = None
    comment: str | None = None
    disabled: bool = False


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_firewall_address_list", annotations=READ)
    async def list_firewall_address_list(
        list_filter: str | None = None,
        address_filter: str | None = None,
        disabled_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists firewall address-list entries."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/firewall/address-list") or []
        filtered = rows
        if list_filter:
            filtered = [r for r in filtered if r.get("list") == list_filter]
        if address_filter:
            filtered = [
                r for r in filtered if address_filter in str(r.get("address", ""))
            ]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_firewall_address_list", annotations=READ)
    async def get_firewall_address_list(
        entry_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets one firewall address-list entry."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/firewall/address-list/{entry_id}")
        if not isinstance(result, dict):
            raise ValueError(f"Address-list entry not found: {entry_id}")
        return result

    @mcp.tool(name="mikrotik_add_firewall_address_list", annotations=WRITE)
    async def add_firewall_address_list(
        list_name: str,
        address: str,
        timeout: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds entry to firewall address-list."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "list": list_name,
            "address": address,
            "disabled": "true" if disabled else "false",
        }
        if timeout:
            payload["timeout"] = timeout
        if comment:
            payload["comment"] = comment
        result = await manager.put("ip/firewall/address-list", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_remove_firewall_address_list", annotations=DESTRUCTIVE)
    async def remove_firewall_address_list(
        entry_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes firewall address-list entry."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/firewall/address-list/{entry_id}")
        return {"removed": True, "id": entry_id}
