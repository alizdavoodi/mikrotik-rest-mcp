from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class IpAddressCreate(BaseModel):
    address: str = Field(min_length=3)
    interface: str = Field(min_length=1)
    network: str | None = None
    broadcast: str | None = None
    comment: str | None = None
    disabled: bool = False


class IpAddressUpdate(BaseModel):
    address: str | None = None
    interface: str | None = None
    network: str | None = None
    broadcast: str | None = None
    comment: str | None = None
    disabled: bool | None = None


def _filter_rows(
    rows: list[dict[str, Any]],
    interface_filter: str | None,
    address_filter: str | None,
    network_filter: str | None,
    disabled_only: bool,
    dynamic_only: bool,
) -> list[dict[str, Any]]:
    filtered = rows
    if interface_filter:
        filtered = [row for row in filtered if row.get("interface") == interface_filter]
    if address_filter:
        filtered = [
            row for row in filtered if address_filter in str(row.get("address", ""))
        ]
    if network_filter:
        filtered = [row for row in filtered if row.get("network") == network_filter]
    if disabled_only:
        filtered = [row for row in filtered if row.get("disabled") == "true"]
    if dynamic_only:
        filtered = [row for row in filtered if row.get("dynamic") == "true"]
    return filtered


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_ip_addresses", annotations=READ)
    async def list_ip_addresses(
        interface_filter: str | None = None,
        address_filter: str | None = None,
        network_filter: str | None = None,
        disabled_only: bool = False,
        dynamic_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List IP addresses on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/address")
        if not rows:
            return []
        return _filter_rows(
            rows=rows,
            interface_filter=interface_filter,
            address_filter=address_filter,
            network_filter=network_filter,
            disabled_only=disabled_only,
            dynamic_only=dynamic_only,
        )

    @mcp.tool(name="mikrotik_get_ip_address", annotations=READ)
    async def get_ip_address(
        address_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific IP address."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/address/{address_id}")
        if not isinstance(result, dict):
            raise ValueError(f"IP address entry not found: {address_id}")
        return result

    @mcp.tool(name="mikrotik_add_ip_address", annotations=WRITE)
    async def add_ip_address(
        address: Annotated[str, Field(min_length=3)],
        interface: Annotated[str, Field(min_length=1)],
        network: str | None = None,
        broadcast: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds an IP address to an interface on MikroTik device."""
        manager = get_manager(ctx)
        payload = IpAddressCreate(
            address=address,
            interface=interface,
            network=network,
            broadcast=broadcast,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        result = await manager.put("ip/address", json=payload)
        return {"added": True, "id": result.get(".id")} if result else {"added": True}

    @mcp.tool(name="mikrotik_update_ip_address", annotations=WRITE)
    async def update_ip_address(
        address_id: Annotated[str, Field(min_length=1)],
        address: str | None = None,
        interface: str | None = None,
        network: str | None = None,
        broadcast: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing IP address on MikroTik device."""
        manager = get_manager(ctx)
        model = IpAddressUpdate(
            address=address,
            interface=interface,
            network=network,
            broadcast=broadcast,
            comment=comment,
            disabled=disabled,
        )
        payload = model.model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"ip/address/{address_id}", json=payload)
        return {"updated": True, "id": address_id}

    @mcp.tool(name="mikrotik_remove_ip_address", annotations=DESTRUCTIVE)
    async def remove_ip_address(
        address_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes an IP address from MikroTik device."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/address/{address_id}")
        return {"removed": True, "id": address_id}

    @mcp.tool(name="mikrotik_enable_ip_address", annotations=WRITE)
    async def enable_ip_address(
        address_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Enables a disabled IP address entry."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/address/{address_id}", json={"disabled": "false"})
        return {"enabled": True, "id": address_id}

    @mcp.tool(name="mikrotik_disable_ip_address", annotations=WRITE)
    async def disable_ip_address(
        address_id: Annotated[str, Field(min_length=1)], ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables an IP address entry."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/address/{address_id}", json={"disabled": "true"})
        return {"disabled": True, "id": address_id}
