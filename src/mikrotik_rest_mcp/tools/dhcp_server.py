from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class DhcpServerCreate(BaseModel):
    name: str
    interface: str
    lease_time: str = "1d"
    address_pool: str | None = None
    disabled: bool = False
    authoritative: str = "yes"
    delay_threshold: str | None = None
    comment: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_dhcp_servers", annotations=READ)
    async def list_dhcp_servers(
        name_filter: str | None = None,
        interface_filter: str | None = None,
        disabled_only: bool = False,
        invalid_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List DHCP servers."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/dhcp-server") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if interface_filter:
            filtered = [r for r in filtered if r.get("interface") == interface_filter]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if invalid_only:
            filtered = [r for r in filtered if r.get("invalid") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_dhcp_server", annotations=READ)
    async def get_dhcp_server(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get one DHCP server by name."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("ip/dhcp-server", params={"name": name})
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        if not rows:
            raise ValueError(f"DHCP server not found: {name}")
        return rows[0]

    @mcp.tool(name="mikrotik_create_dhcp_server", annotations=WRITE)
    async def create_dhcp_server(
        name: str,
        interface: str,
        lease_time: str = "1d",
        address_pool: str | None = None,
        disabled: bool = False,
        authoritative: str = "yes",
        delay_threshold: str | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a DHCP server."""
        manager = get_manager(ctx)
        payload = DhcpServerCreate(
            name=name,
            interface=interface,
            lease_time=lease_time,
            address_pool=address_pool,
            disabled=disabled,
            authoritative=authoritative,
            delay_threshold=delay_threshold,
            comment=comment,
        ).model_dump(exclude_none=True)
        payload["lease-time"] = payload.pop("lease_time")
        if "address_pool" in payload:
            payload["address-pool"] = payload.pop("address_pool")
        if "delay_threshold" in payload:
            payload["delay-threshold"] = payload.pop("delay_threshold")
        result = await manager.put("ip/dhcp-server", json=payload)
        return {"created": True, "id": result.get(".id") if result else name}

    @mcp.tool(name="mikrotik_remove_dhcp_server", annotations=DESTRUCTIVE)
    async def remove_dhcp_server(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove DHCP server by name."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/dhcp-server", params={"name": name}) or []
        if not rows:
            raise ValueError(f"DHCP server not found: {name}")
        entry_id = str(rows[0].get(".id"))
        await manager.delete(f"ip/dhcp-server/{entry_id}")
        return {"removed": True, "id": entry_id}
