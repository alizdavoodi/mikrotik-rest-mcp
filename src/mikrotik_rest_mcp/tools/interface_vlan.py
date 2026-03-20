from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class VlanCreate(BaseModel):
    name: str = Field(min_length=1)
    vlan_id: int = Field(ge=1, le=4094)
    interface: str = Field(min_length=1)
    comment: str | None = None
    disabled: bool = False
    mtu: int | None = None


class VlanUpdate(BaseModel):
    new_name: str | None = None
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    interface: str | None = None
    comment: str | None = None
    disabled: bool | None = None
    mtu: int | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_vlan_interfaces", annotations=READ)
    async def list_vlan_interfaces(
        name_filter: str | None = None,
        vlan_id_filter: int | None = None,
        interface_filter: str | None = None,
        disabled_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists VLAN interfaces on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/vlan") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if vlan_id_filter is not None:
            filtered = [
                r for r in filtered if str(vlan_id_filter) == str(r.get("vlan-id"))
            ]
        if interface_filter:
            filtered = [r for r in filtered if r.get("interface") == interface_filter]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_vlan_interface", annotations=READ)
    async def get_vlan_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific VLAN interface."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("interface/vlan")
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        for vlan in rows:
            if vlan.get("name") == name:
                return vlan
        raise ValueError(f"VLAN interface not found: {name}")

    @mcp.tool(name="mikrotik_create_vlan_interface", annotations=WRITE)
    async def create_vlan_interface(
        name: str,
        vlan_id: int,
        interface: str,
        comment: str | None = None,
        disabled: bool = False,
        mtu: int | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Creates a VLAN interface on MikroTik device."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "name": name,
            "vlan-id": vlan_id,
            "interface": interface,
            "disabled": "true" if disabled else "false",
        }
        if comment:
            payload["comment"] = comment
        if mtu:
            payload["mtu"] = mtu
        result = await manager.put("interface/vlan", json=payload)
        return (
            {"created": True, "id": result.get(".id")} if result else {"created": True}
        )

    @mcp.tool(name="mikrotik_update_vlan_interface", annotations=WRITE)
    async def update_vlan_interface(
        name: str,
        new_name: str | None = None,
        vlan_id: int | None = None,
        interface: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        mtu: int | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing VLAN interface on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/vlan") or []
        vlan_id_val = None
        for vlan in rows:
            if vlan.get("name") == name:
                vlan_id_val = vlan.get(".id")
                break
        if not vlan_id_val:
            raise ValueError(f"VLAN interface not found: {name}")
        payload: dict[str, Any] = {}
        if new_name:
            payload["name"] = new_name
        if vlan_id is not None:
            payload["vlan-id"] = vlan_id
        if interface:
            payload["interface"] = interface
        if comment:
            payload["comment"] = comment
        if disabled is not None:
            payload["disabled"] = "true" if disabled else "false"
        if mtu:
            payload["mtu"] = mtu
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"interface/vlan/{vlan_id_val}", json=payload)
        return {"updated": True, "name": name}

    @mcp.tool(name="mikrotik_remove_vlan_interface", annotations=DESTRUCTIVE)
    async def remove_vlan_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a VLAN interface from MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/vlan") or []
        vlan_id = None
        for vlan in rows:
            if vlan.get("name") == name:
                vlan_id = vlan.get(".id")
                break
        if not vlan_id:
            raise ValueError(f"VLAN interface not found: {name}")
        await manager.delete(f"interface/vlan/{vlan_id}")
        return {"removed": True, "name": name}
