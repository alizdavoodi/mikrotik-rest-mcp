from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class WireguardInterfaceCreate(BaseModel):
    name: str = Field(min_length=1)
    listen_port: int | None = Field(default=None, ge=1, le=65535)
    private_key: str | None = None
    mtu: int | None = None
    comment: str | None = None
    disabled: bool = False


class WireguardPeerCreate(BaseModel):
    interface: str = Field(min_length=1)
    public_key: str = Field(min_length=30)
    allowed_address: str = Field(min_length=3)
    endpoint_address: str | None = None
    endpoint_port: int | None = Field(default=None, ge=1, le=65535)
    preshared_key: str | None = None
    persistent_keepalive: str | None = None
    comment: str | None = None
    disabled: bool = False


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_wireguard_interfaces", annotations=READ)
    async def list_wireguard_interfaces(
        name_filter: str | None = None,
        disabled_only: bool = False,
        running_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List WireGuard interfaces."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireguard") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if running_only:
            filtered = [r for r in filtered if r.get("running") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_wireguard_interface", annotations=READ)
    async def get_wireguard_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get one WireGuard interface by name."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("interface/wireguard", params={"name": name})
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        if not rows:
            raise ValueError(f"WireGuard interface not found: {name}")
        return rows[0]

    @mcp.tool(name="mikrotik_create_wireguard_interface", annotations=WRITE)
    async def create_wireguard_interface(
        name: str,
        listen_port: int | None = None,
        private_key: str | None = None,
        mtu: int | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a WireGuard interface."""
        manager = get_manager(ctx)
        payload = WireguardInterfaceCreate(
            name=name,
            listen_port=listen_port,
            private_key=private_key,
            mtu=mtu,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        if "listen_port" in payload:
            payload["listen-port"] = payload.pop("listen_port")
        if "private_key" in payload:
            payload["private-key"] = payload.pop("private_key")
        result = await manager.put("interface/wireguard", json=payload)
        return {"created": True, "id": result.get(".id") if result else name}

    @mcp.tool(name="mikrotik_update_wireguard_interface", annotations=WRITE)
    async def update_wireguard_interface(
        name: str,
        new_name: str | None = None,
        listen_port: int | None = None,
        private_key: str | None = None,
        mtu: int | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update a WireGuard interface."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireguard", params={"name": name}) or []
        if not rows:
            raise ValueError(f"WireGuard interface not found: {name}")
        entry_id = str(rows[0].get(".id"))
        payload: dict[str, Any] = {}
        if new_name is not None:
            payload["name"] = new_name
        if listen_port is not None:
            payload["listen-port"] = listen_port
        if private_key is not None:
            payload["private-key"] = private_key
        if mtu is not None:
            payload["mtu"] = mtu
        if comment is not None:
            payload["comment"] = comment
        if disabled is not None:
            payload["disabled"] = "true" if disabled else "false"
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"interface/wireguard/{entry_id}", json=payload)
        return {"updated": True, "id": entry_id}

    @mcp.tool(name="mikrotik_remove_wireguard_interface", annotations=DESTRUCTIVE)
    async def remove_wireguard_interface(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove a WireGuard interface by name."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireguard", params={"name": name}) or []
        if not rows:
            raise ValueError(f"WireGuard interface not found: {name}")
        entry_id = str(rows[0].get(".id"))
        await manager.delete(f"interface/wireguard/{entry_id}")
        return {"removed": True, "id": entry_id}

    @mcp.tool(name="mikrotik_list_wireguard_peers", annotations=READ)
    async def list_wireguard_peers(
        interface_filter: str | None = None,
        disabled_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List WireGuard peers."""
        manager = get_manager(ctx)
        rows = await manager.get("interface/wireguard/peers") or []
        filtered = rows
        if interface_filter:
            filtered = [r for r in filtered if r.get("interface") == interface_filter]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_wireguard_peer", annotations=READ)
    async def get_wireguard_peer(
        peer_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Get a WireGuard peer by ID."""
        manager = get_manager(ctx)
        result = await manager.get(f"interface/wireguard/peers/{peer_id}")
        if not isinstance(result, dict):
            raise ValueError(f"WireGuard peer not found: {peer_id}")
        return result

    @mcp.tool(name="mikrotik_create_wireguard_peer", annotations=WRITE)
    async def create_wireguard_peer(
        interface: str,
        public_key: str,
        allowed_address: str,
        endpoint_address: str | None = None,
        endpoint_port: int | None = None,
        preshared_key: str | None = None,
        persistent_keepalive: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Add a WireGuard peer."""
        manager = get_manager(ctx)
        payload = WireguardPeerCreate(
            interface=interface,
            public_key=public_key,
            allowed_address=allowed_address,
            endpoint_address=endpoint_address,
            endpoint_port=endpoint_port,
            preshared_key=preshared_key,
            persistent_keepalive=persistent_keepalive,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        payload["public-key"] = payload.pop("public_key")
        payload["allowed-address"] = payload.pop("allowed_address")
        if "endpoint_address" in payload:
            payload["endpoint-address"] = payload.pop("endpoint_address")
        if "endpoint_port" in payload:
            payload["endpoint-port"] = payload.pop("endpoint_port")
        if "preshared_key" in payload:
            payload["preshared-key"] = payload.pop("preshared_key")
        if "persistent_keepalive" in payload:
            payload["persistent-keepalive"] = payload.pop("persistent_keepalive")
        result = await manager.put("interface/wireguard/peers", json=payload)
        return {"created": True, "id": result.get(".id") if result else interface}

    @mcp.tool(name="mikrotik_update_wireguard_peer", annotations=WRITE)
    async def update_wireguard_peer(
        peer_id: str,
        allowed_address: str | None = None,
        endpoint_address: str | None = None,
        endpoint_port: int | None = None,
        preshared_key: str | None = None,
        persistent_keepalive: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update an existing WireGuard peer."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {}
        if allowed_address is not None:
            payload["allowed-address"] = allowed_address
        if endpoint_address is not None:
            payload["endpoint-address"] = endpoint_address
        if endpoint_port is not None:
            payload["endpoint-port"] = endpoint_port
        if preshared_key is not None:
            payload["preshared-key"] = preshared_key
        if persistent_keepalive is not None:
            payload["persistent-keepalive"] = persistent_keepalive
        if comment is not None:
            payload["comment"] = comment
        if disabled is not None:
            payload["disabled"] = "true" if disabled else "false"
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"interface/wireguard/peers/{peer_id}", json=payload)
        return {"updated": True, "id": peer_id}

    @mcp.tool(name="mikrotik_remove_wireguard_peer", annotations=DESTRUCTIVE)
    async def remove_wireguard_peer(
        peer_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Remove a WireGuard peer."""
        manager = get_manager(ctx)
        await manager.delete(f"interface/wireguard/peers/{peer_id}")
        return {"removed": True, "id": peer_id}
