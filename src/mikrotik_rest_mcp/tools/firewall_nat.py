from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class NatCreate(BaseModel):
    chain: str
    action: str
    src_address: str | None = None
    dst_address: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    protocol: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    to_addresses: str | None = None
    to_ports: str | None = None
    limit: str | None = None
    comment: str | None = None
    disabled: bool = False
    log: bool = False
    log_prefix: str | None = None


class NatUpdate(BaseModel):
    chain: str | None = None
    action: str | None = None
    src_address: str | None = None
    dst_address: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    protocol: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    to_addresses: str | None = None
    to_ports: str | None = None
    limit: str | None = None
    comment: str | None = None
    disabled: bool | None = None
    log: bool | None = None
    log_prefix: str | None = None


def _translate(payload: dict[str, Any]) -> dict[str, Any]:
    mappings = {
        "src_address": "src-address",
        "dst_address": "dst-address",
        "src_port": "src-port",
        "dst_port": "dst-port",
        "in_interface": "in-interface",
        "out_interface": "out-interface",
        "to_addresses": "to-addresses",
        "to_ports": "to-ports",
        "log_prefix": "log-prefix",
    }
    result = dict(payload)
    for src, dst in mappings.items():
        if src in result:
            result[dst] = result.pop(src)
    if "disabled" in result:
        result["disabled"] = "true" if result["disabled"] else "false"
    if "log" in result:
        result["log"] = "true" if result["log"] else "false"
    return result


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_nat_rules", annotations=READ)
    async def list_nat_rules(
        chain_filter: str | None = None,
        action_filter: str | None = None,
        src_address_filter: str | None = None,
        dst_address_filter: str | None = None,
        protocol_filter: str | None = None,
        interface_filter: str | None = None,
        disabled_only: bool = False,
        invalid_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists NAT rules on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/firewall/nat") or []
        filtered = rows
        if chain_filter:
            filtered = [r for r in filtered if r.get("chain") == chain_filter]
        if action_filter:
            filtered = [r for r in filtered if r.get("action") == action_filter]
        if src_address_filter:
            filtered = [
                r
                for r in filtered
                if src_address_filter in str(r.get("src-address", ""))
            ]
        if dst_address_filter:
            filtered = [
                r
                for r in filtered
                if dst_address_filter in str(r.get("dst-address", ""))
            ]
        if protocol_filter:
            filtered = [r for r in filtered if r.get("protocol") == protocol_filter]
        if interface_filter:
            filtered = [
                r
                for r in filtered
                if interface_filter in str(r.get("in-interface", ""))
                or interface_filter in str(r.get("out-interface", ""))
            ]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if invalid_only:
            filtered = [r for r in filtered if r.get("invalid") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_nat_rule", annotations=READ)
    async def get_nat_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific NAT rule."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/firewall/nat/{rule_id}")
        if not isinstance(result, dict):
            raise ValueError(f"NAT rule not found: {rule_id}")
        return result

    @mcp.tool(name="mikrotik_create_nat_rule", annotations=WRITE)
    async def create_nat_rule(
        chain: str,
        action: str,
        src_address: str | None = None,
        dst_address: str | None = None,
        src_port: str | None = None,
        dst_port: str | None = None,
        protocol: str | None = None,
        in_interface: str | None = None,
        out_interface: str | None = None,
        to_addresses: str | None = None,
        to_ports: str | None = None,
        limit: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        log: bool = False,
        log_prefix: str | None = None,
        place_before: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Creates a NAT rule on MikroTik device."""
        manager = get_manager(ctx)
        model = NatCreate(
            chain=chain,
            action=action,
            src_address=src_address,
            dst_address=dst_address,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            in_interface=in_interface,
            out_interface=out_interface,
            to_addresses=to_addresses,
            to_ports=to_ports,
            limit=limit,
            comment=comment,
            disabled=disabled,
            log=log,
            log_prefix=log_prefix,
        )
        payload = _translate(model.model_dump(exclude_none=True))
        if place_before is not None:
            payload["place-before"] = place_before
        result = await manager.put("ip/firewall/nat", json=payload)
        return (
            {"created": True, "id": result.get(".id")} if result else {"created": True}
        )

    @mcp.tool(name="mikrotik_update_nat_rule", annotations=WRITE)
    async def update_nat_rule(
        rule_id: str,
        chain: str | None = None,
        action: str | None = None,
        src_address: str | None = None,
        dst_address: str | None = None,
        src_port: str | None = None,
        dst_port: str | None = None,
        protocol: str | None = None,
        in_interface: str | None = None,
        out_interface: str | None = None,
        to_addresses: str | None = None,
        to_ports: str | None = None,
        limit: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        log: bool | None = None,
        log_prefix: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing NAT rule on MikroTik device."""
        manager = get_manager(ctx)
        payload = NatUpdate(
            chain=chain,
            action=action,
            src_address=src_address,
            dst_address=dst_address,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            in_interface=in_interface,
            out_interface=out_interface,
            to_addresses=to_addresses,
            to_ports=to_ports,
            limit=limit,
            comment=comment,
            disabled=disabled,
            log=log,
            log_prefix=log_prefix,
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        payload = _translate(payload)
        await manager.patch(f"ip/firewall/nat/{rule_id}", json=payload)
        return {"updated": True, "id": rule_id}

    @mcp.tool(name="mikrotik_remove_nat_rule", annotations=DESTRUCTIVE)
    async def remove_nat_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a NAT rule from MikroTik device."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/firewall/nat/{rule_id}")
        return {"removed": True, "id": rule_id}

    @mcp.tool(name="mikrotik_move_nat_rule", annotations=WRITE)
    async def move_nat_rule(
        rule_id: str, destination: int, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Moves a NAT rule to a different position in the chain."""
        manager = get_manager(ctx)
        await manager.patch(
            f"ip/firewall/nat/{rule_id}", json={"move": str(destination)}
        )
        return {"moved": True, "id": rule_id, "destination": destination}

    @mcp.tool(name="mikrotik_enable_nat_rule", annotations=WRITE)
    async def enable_nat_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Enables a NAT rule."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/firewall/nat/{rule_id}", json={"disabled": "false"})
        return {"enabled": True, "id": rule_id}

    @mcp.tool(name="mikrotik_disable_nat_rule", annotations=WRITE)
    async def disable_nat_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables a NAT rule."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/firewall/nat/{rule_id}", json={"disabled": "true"})
        return {"disabled": True, "id": rule_id}
