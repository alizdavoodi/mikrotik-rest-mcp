from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class DhcpLeaseCreate(BaseModel):
    address: str
    mac_address: str
    server: str | None = None
    comment: str | None = None
    disabled: bool = False


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_dhcp_leases", annotations=READ)
    async def list_dhcp_leases(
        server: str | None = None,
        mac_address: str | None = None,
        address: str | None = None,
        status: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List DHCP leases."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/dhcp-server/lease") or []
        filtered = rows
        if server:
            filtered = [r for r in filtered if r.get("server") == server]
        if mac_address:
            filtered = [r for r in filtered if r.get("mac-address") == mac_address]
        if address:
            filtered = [r for r in filtered if r.get("address") == address]
        if status:
            filtered = [r for r in filtered if r.get("status") == status]
        return filtered

    @mcp.tool(name="mikrotik_get_dhcp_lease", annotations=READ)
    async def get_dhcp_lease(
        lease_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get a DHCP lease by id."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/dhcp-server/lease/{lease_id}")
        if not isinstance(result, dict):
            raise ValueError(f"DHCP lease not found: {lease_id}")
        return result

    @mcp.tool(name="mikrotik_create_dhcp_lease", annotations=WRITE)
    async def create_dhcp_lease(
        address: str,
        mac_address: str,
        server: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create static DHCP lease."""
        manager = get_manager(ctx)
        payload = DhcpLeaseCreate(
            address=address,
            mac_address=mac_address,
            server=server,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        payload["mac-address"] = payload.pop("mac_address")
        result = await manager.put("ip/dhcp-server/lease", json=payload)
        return {"created": True, "id": result.get(".id") if result else address}

    @mcp.tool(name="mikrotik_remove_dhcp_lease", annotations=DESTRUCTIVE)
    async def remove_dhcp_lease(
        lease_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove DHCP lease by id."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/dhcp-server/lease/{lease_id}")
        return {"removed": True, "id": lease_id}
