from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class FirewallFilterCreate(BaseModel):
    chain: str
    action: str
    src_address: str | None = None
    dst_address: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    protocol: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    connection_state: str | None = None
    src_address_list: str | None = None
    dst_address_list: str | None = None
    limit: str | None = None
    tcp_flags: str | None = None
    connection_limit: str | None = None
    address_list_timeout: str | None = None
    comment: str | None = None
    disabled: bool = False
    log: bool = False
    log_prefix: str | None = None


class FirewallFilterUpdate(BaseModel):
    chain: str | None = None
    action: str | None = None
    src_address: str | None = None
    dst_address: str | None = None
    src_port: str | None = None
    dst_port: str | None = None
    protocol: str | None = None
    in_interface: str | None = None
    out_interface: str | None = None
    connection_state: str | None = None
    src_address_list: str | None = None
    dst_address_list: str | None = None
    limit: str | None = None
    tcp_flags: str | None = None
    connection_limit: str | None = None
    address_list_timeout: str | None = None
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
        "connection_state": "connection-state",
        "src_address_list": "src-address-list",
        "dst_address_list": "dst-address-list",
        "tcp_flags": "tcp-flags",
        "connection_limit": "connection-limit",
        "address_list_timeout": "address-list-timeout",
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
    @mcp.tool(name="mikrotik_list_filter_rules", annotations=READ)
    async def list_filter_rules(
        chain_filter: str | None = None,
        action_filter: str | None = None,
        src_address_filter: str | None = None,
        dst_address_filter: str | None = None,
        protocol_filter: str | None = None,
        interface_filter: str | None = None,
        disabled_only: bool = False,
        invalid_only: bool = False,
        dynamic_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists firewall filter rules from MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("ip/firewall/filter") or []
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
        if dynamic_only:
            filtered = [r for r in filtered if r.get("dynamic") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_filter_rule", annotations=READ)
    async def get_filter_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific firewall filter rule."""
        manager = get_manager(ctx)
        result = await manager.get(f"ip/firewall/filter/{rule_id}")
        if not isinstance(result, dict):
            raise ValueError(f"Filter rule not found: {rule_id}")
        return result

    @mcp.tool(name="mikrotik_create_filter_rule", annotations=WRITE)
    async def create_filter_rule(
        chain: str,
        action: str,
        src_address: str | None = None,
        dst_address: str | None = None,
        src_port: str | None = None,
        dst_port: str | None = None,
        protocol: str | None = None,
        in_interface: str | None = None,
        out_interface: str | None = None,
        connection_state: str | None = None,
        src_address_list: str | None = None,
        dst_address_list: str | None = None,
        limit: str | None = None,
        tcp_flags: str | None = None,
        connection_limit: str | None = None,
        address_list_timeout: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        log: bool = False,
        log_prefix: str | None = None,
        place_before: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Creates a firewall filter rule on MikroTik device."""
        manager = get_manager(ctx)
        model = FirewallFilterCreate(
            chain=chain,
            action=action,
            src_address=src_address,
            dst_address=dst_address,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            in_interface=in_interface,
            out_interface=out_interface,
            connection_state=connection_state,
            src_address_list=src_address_list,
            dst_address_list=dst_address_list,
            limit=limit,
            tcp_flags=tcp_flags,
            connection_limit=connection_limit,
            address_list_timeout=address_list_timeout,
            comment=comment,
            disabled=disabled,
            log=log,
            log_prefix=log_prefix,
        )
        payload = _translate(model.model_dump(exclude_none=True))
        if place_before is not None:
            payload["place-before"] = place_before
        result = await manager.put("ip/firewall/filter", json=payload)
        return (
            {"created": True, "id": result.get(".id")} if result else {"created": True}
        )

    @mcp.tool(name="mikrotik_update_filter_rule", annotations=WRITE)
    async def update_filter_rule(
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
        connection_state: str | None = None,
        src_address_list: str | None = None,
        dst_address_list: str | None = None,
        limit: str | None = None,
        tcp_flags: str | None = None,
        connection_limit: str | None = None,
        address_list_timeout: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        log: bool | None = None,
        log_prefix: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates an existing firewall filter rule on MikroTik device."""
        manager = get_manager(ctx)
        payload = FirewallFilterUpdate(
            chain=chain,
            action=action,
            src_address=src_address,
            dst_address=dst_address,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            in_interface=in_interface,
            out_interface=out_interface,
            connection_state=connection_state,
            src_address_list=src_address_list,
            dst_address_list=dst_address_list,
            limit=limit,
            tcp_flags=tcp_flags,
            connection_limit=connection_limit,
            address_list_timeout=address_list_timeout,
            comment=comment,
            disabled=disabled,
            log=log,
            log_prefix=log_prefix,
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        payload = _translate(payload)
        await manager.patch(f"ip/firewall/filter/{rule_id}", json=payload)
        return {"updated": True, "id": rule_id}

    @mcp.tool(name="mikrotik_remove_filter_rule", annotations=DESTRUCTIVE)
    async def remove_filter_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a firewall filter rule from MikroTik device."""
        manager = get_manager(ctx)
        await manager.delete(f"ip/firewall/filter/{rule_id}")
        return {"removed": True, "id": rule_id}

    @mcp.tool(name="mikrotik_move_filter_rule", annotations=WRITE)
    async def move_filter_rule(
        rule_id: str, destination: int, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Moves a firewall filter rule to a different position in the chain."""
        manager = get_manager(ctx)
        await manager.patch(
            f"ip/firewall/filter/{rule_id}", json={"move": str(destination)}
        )
        return {"moved": True, "id": rule_id, "destination": destination}

    @mcp.tool(name="mikrotik_enable_filter_rule", annotations=WRITE)
    async def enable_filter_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Enables a firewall filter rule."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/firewall/filter/{rule_id}", json={"disabled": "false"})
        return {"enabled": True, "id": rule_id}

    @mcp.tool(name="mikrotik_disable_filter_rule", annotations=WRITE)
    async def disable_filter_rule(
        rule_id: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables a firewall filter rule."""
        manager = get_manager(ctx)
        await manager.patch(f"ip/firewall/filter/{rule_id}", json={"disabled": "true"})
        return {"disabled": True, "id": rule_id}

    @mcp.tool(name="mikrotik_create_basic_firewall_setup", annotations=WRITE)
    async def create_basic_firewall_setup(
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Creates a basic firewall setup with common security rules."""
        manager = get_manager(ctx)
        rules = [
            {
                "chain": "input",
                "action": "accept",
                "connection-state": "established,related",
                "comment": "Accept established connections",
            },
            {
                "chain": "input",
                "action": "accept",
                "protocol": "icmp",
                "comment": "Allow ICMP",
            },
            {
                "chain": "input",
                "action": "drop",
                "in-interface": "ether1",
                "comment": "Drop from WAN",
            },
            {
                "chain": "forward",
                "action": "accept",
                "connection-state": "established,related",
                "comment": "Accept forwarded established",
            },
            {
                "chain": "forward",
                "action": "drop",
                "connection-state": "invalid",
                "comment": "Drop invalid",
            },
        ]
        created = []
        for rule in rules:
            result = await manager.put("ip/firewall/filter", json=rule)
            if result:
                created.append(result.get(".id"))
        return {"created": len(created), "rules_created": created}
