from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class WirelessCreate(BaseModel):
    name: str
    ssid: str | None = None
    disabled: bool = False
    comment: str | None = None


class WirelessUpdate(BaseModel):
    new_name: str | None = None
    ssid: str | None = None
    disabled: bool | None = None
    comment: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_wireless_interfaces", annotations=READ)
    async def list_wireless_interfaces(
        name_filter: str | None = None,
        disabled_only: bool = False,
        running_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List wireless interfaces."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireless") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if running_only:
            filtered = [r for r in filtered if r.get("running") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_wireless_interface", annotations=READ)
    async def get_wireless_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get details for one wireless interface."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("interface/wireless", params={"name": name})
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        if not rows:
            raise ValueError(f"Wireless interface not found: {name}")
        return rows[0]

    @mcp.tool(name="mikrotik_create_wireless_interface", annotations=WRITE)
    async def create_wireless_interface(
        name: str,
        ssid: str | None = None,
        disabled: bool = False,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create wireless interface (legacy /interface/wireless path)."""
        manager = get_manager(ctx)
        payload = WirelessCreate(
            name=name, ssid=ssid, disabled=disabled, comment=comment
        ).model_dump(exclude_none=True)
        result = await manager.put("interface/wireless", json=payload)
        return {"created": True, "id": result.get(".id") if result else name}

    @mcp.tool(name="mikrotik_update_wireless_interface", annotations=WRITE)
    async def update_wireless_interface(
        name: str,
        new_name: str | None = None,
        ssid: str | None = None,
        disabled: bool | None = None,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update wireless interface values."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireless", params={"name": name}) or []
        if not rows:
            raise ValueError(f"Wireless interface not found: {name}")
        entry_id = str(rows[0].get(".id"))
        payload = WirelessUpdate(
            new_name=new_name, ssid=ssid, disabled=disabled, comment=comment
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        if "new_name" in payload:
            payload["name"] = payload.pop("new_name")
        await manager.patch(f"interface/wireless/{entry_id}", json=payload)
        return {"updated": True, "id": entry_id}

    @mcp.tool(name="mikrotik_remove_wireless_interface", annotations=DESTRUCTIVE)
    async def remove_wireless_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove wireless interface by name."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireless", params={"name": name}) or []
        if not rows:
            raise ValueError(f"Wireless interface not found: {name}")
        entry_id = str(rows[0].get(".id"))
        await manager.delete(f"interface/wireless/{entry_id}")
        return {"removed": True, "id": entry_id}

    @mcp.tool(name="mikrotik_scan_wireless_networks", annotations=READ)
    async def scan_wireless_networks(
        interface: str, duration: int = 5, ctx: Context = CurrentContext()
    ) -> list[dict[str, Any]]:
        """Scan for nearby wireless networks on an interface."""
        manager = get_manager(ctx)
        _ = duration
        await manager.post(f"interface/wireless/{interface}/scan", json={})
        rows = await manager.get("interface/wireless/scan") or []
        return rows

    @mcp.tool(name="mikrotik_get_wireless_registration_table", annotations=READ)
    async def get_wireless_registration_table(
        interface: str | None = None, ctx: Context = CurrentContext()
    ) -> list[dict[str, Any]]:
        """Return wireless registration table (associated clients)."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireless/registration-table") or []
        if interface:
            rows = [row for row in rows if row.get("interface") == interface]
        return rows
