from __future__ import annotations

from typing import Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class LoggingRuleCreate(BaseModel):
    topics: str = Field(min_length=1)
    action: str = "memory"
    prefix: str | None = None
    disabled: bool = False


class LoggingRuleUpdate(BaseModel):
    topics: str | None = None
    action: str | None = None
    prefix: str | None = None
    disabled: bool | None = None


class LoggingActionCreate(BaseModel):
    name: str = Field(min_length=1)
    target: Literal["memory", "disk", "echo", "remote"] = "remote"
    remote: str | None = None
    remote_port: int | None = Field(default=None, ge=1, le=65535)
    src_address: str | None = None
    remote_protocol: Literal["udp", "tcp", "tls"] | None = None
    remote_log_format: Literal["default", "cef", "syslog"] | None = None
    syslog_facility: str | None = None
    syslog_severity: str | None = None
    syslog_time_format: Literal["bsd-syslog", "iso8601"] | None = None
    bsd_syslog: bool | None = None
    vrf: str | None = None
    comment: str | None = None
    disabled: bool = False


class LoggingActionUpdate(BaseModel):
    name: str | None = None
    target: Literal["memory", "disk", "echo", "remote"] | None = None
    remote: str | None = None
    remote_port: int | None = Field(default=None, ge=1, le=65535)
    src_address: str | None = None
    remote_protocol: Literal["udp", "tcp", "tls"] | None = None
    remote_log_format: Literal["default", "cef", "syslog"] | None = None
    syslog_facility: str | None = None
    syslog_severity: str | None = None
    syslog_time_format: Literal["bsd-syslog", "iso8601"] | None = None
    bsd_syslog: bool | None = None
    vrf: str | None = None
    comment: str | None = None
    disabled: bool | None = None


_ACTION_FIELD_MAP = {
    "remote_port": "remote-port",
    "src_address": "src-address",
    "remote_protocol": "remote-protocol",
    "remote_log_format": "remote-log-format",
    "syslog_facility": "syslog-facility",
    "syslog_severity": "syslog-severity",
    "syslog_time_format": "syslog-time-format",
    "bsd_syslog": "bsd-syslog",
}


def _translate(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        new_key = _ACTION_FIELD_MAP.get(key, key)
        if isinstance(value, bool):
            result[new_key] = "true" if value else "false"
        else:
            result[new_key] = value
    return result


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_logging_rules", annotations=READ)
    async def list_logging_rules(
        topics_filter: str | None = None,
        action_filter: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List all logging rules; optionally filter by topics or action."""
        manager = get_manager(ctx)
        rows = await manager.get("system/logging") or []
        if topics_filter:
            rows = [r for r in rows if topics_filter in str(r.get("topics", ""))]
        if action_filter:
            rows = [r for r in rows if r.get("action") == action_filter]
        return rows

    @mcp.tool(name="mikrotik_get_logging_rule", annotations=READ)
    async def get_logging_rule(
        rule_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Get a single logging rule by ID (e.g., '*1')."""
        manager = get_manager(ctx)
        result = await manager.get(f"system/logging/{rule_id}")
        if not result:
            raise ValueError(f"Logging rule not found: {rule_id}")
        return result

    @mcp.tool(name="mikrotik_create_logging_rule", annotations=WRITE)
    async def create_logging_rule(
        topics: str,
        action: str = "memory",
        prefix: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a logging rule.

        topics: comma-separated topic list (e.g., 'firewall', 'dhcp,info').
        action: name of logging action (e.g., 'memory', 'remote-syslog')."""
        manager = get_manager(ctx)
        payload = LoggingRuleCreate(
            topics=topics, action=action, prefix=prefix, disabled=disabled
        ).model_dump(exclude_none=True)
        if "disabled" in payload:
            payload["disabled"] = "true" if payload["disabled"] else "false"
        result = await manager.put("system/logging", json=payload)
        return {"created": True, "id": result.get(".id") if result else None}

    @mcp.tool(name="mikrotik_update_logging_rule", annotations=WRITE)
    async def update_logging_rule(
        rule_id: str,
        topics: str | None = None,
        action: str | None = None,
        prefix: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update an existing logging rule by ID."""
        manager = get_manager(ctx)
        data = LoggingRuleUpdate(
            topics=topics, action=action, prefix=prefix, disabled=disabled
        )
        payload = data.model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        if "disabled" in payload:
            payload["disabled"] = "true" if payload["disabled"] else "false"
        await manager.patch(f"system/logging/{rule_id}", json=payload)
        return {"updated": True, "id": rule_id}

    @mcp.tool(name="mikrotik_remove_logging_rule", annotations=DESTRUCTIVE)
    async def remove_logging_rule(
        rule_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Remove a logging rule by ID.

        Note: Default rules (*0-*3) are protected by RouterOS.
        """
        manager = get_manager(ctx)
        await manager.delete(f"system/logging/{rule_id}")
        return {"removed": True, "id": rule_id}

    @mcp.tool(name="mikrotik_enable_logging_rule", annotations=WRITE)
    async def enable_logging_rule(
        rule_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Enable a disabled logging rule."""
        manager = get_manager(ctx)
        await manager.patch(f"system/logging/{rule_id}", json={"disabled": "false"})
        return {"enabled": True, "id": rule_id}

    @mcp.tool(name="mikrotik_disable_logging_rule", annotations=WRITE)
    async def disable_logging_rule(
        rule_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Disable a logging rule."""
        manager = get_manager(ctx)
        await manager.patch(f"system/logging/{rule_id}", json={"disabled": "true"})
        return {"disabled": True, "id": rule_id}

    @mcp.tool(name="mikrotik_list_logging_actions", annotations=READ)
    async def list_logging_actions(
        target_filter: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List logging actions; optionally filter by target type."""
        manager = get_manager(ctx)
        rows = await manager.get("system/logging/action") or []
        if target_filter:
            rows = [r for r in rows if r.get("target") == target_filter]
        return rows

    @mcp.tool(name="mikrotik_get_logging_action", annotations=READ)
    async def get_logging_action(
        action_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Get a single logging action by ID (e.g., '*1') or name (e.g., 'memory')."""
        manager = get_manager(ctx)
        result = await manager.get(f"system/logging/action/{action_id}")
        if not result:
            raise ValueError(f"Logging action not found: {action_id}")
        return result

    @mcp.tool(name="mikrotik_create_logging_action", annotations=WRITE)
    async def create_logging_action(
        name: str,
        target: Literal["memory", "disk", "echo", "remote"] = "remote",
        remote: str | None = None,
        remote_port: int | None = None,
        src_address: str | None = None,
        remote_protocol: Literal["udp", "tcp", "tls"] | None = None,
        remote_log_format: Literal["default", "cef", "syslog"] | None = None,
        syslog_facility: str | None = None,
        syslog_severity: str | None = None,
        syslog_time_format: Literal["bsd-syslog", "iso8601"] | None = None,
        bsd_syslog: bool | None = None,
        vrf: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a logging action.

        For remote syslog: target='remote', remote='10.0.0.1', remote_port=514.
        Note: Default actions (memory, disk, echo, remote) may be recreated
        by RouterOS on reboot.
        """
        manager = get_manager(ctx)
        payload = LoggingActionCreate(
            name=name,
            target=target,
            remote=remote,
            remote_port=remote_port,
            src_address=src_address,
            remote_protocol=remote_protocol,
            remote_log_format=remote_log_format,
            syslog_facility=syslog_facility,
            syslog_severity=syslog_severity,
            syslog_time_format=syslog_time_format,
            bsd_syslog=bsd_syslog,
            vrf=vrf,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        payload = _translate(payload)
        result = await manager.put("system/logging/action", json=payload)
        return {"created": True, "id": result.get(".id") if result else name}

    @mcp.tool(name="mikrotik_update_logging_action", annotations=WRITE)
    async def update_logging_action(
        action_id: str,
        name: str | None = None,
        target: Literal["memory", "disk", "echo", "remote"] | None = None,
        remote: str | None = None,
        remote_port: int | None = None,
        src_address: str | None = None,
        remote_protocol: Literal["udp", "tcp", "tls"] | None = None,
        remote_log_format: Literal["default", "cef", "syslog"] | None = None,
        syslog_facility: str | None = None,
        syslog_severity: str | None = None,
        syslog_time_format: Literal["bsd-syslog", "iso8601"] | None = None,
        bsd_syslog: bool | None = None,
        vrf: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Update an existing logging action by ID.

        Note: Default actions (memory, disk, echo, remote) may be recreated by
        RouterOS on reboot if deleted.
        """
        manager = get_manager(ctx)
        payload = LoggingActionUpdate(
            name=name,
            target=target,
            remote=remote,
            remote_port=remote_port,
            src_address=src_address,
            remote_protocol=remote_protocol,
            remote_log_format=remote_log_format,
            syslog_facility=syslog_facility,
            syslog_severity=syslog_severity,
            syslog_time_format=syslog_time_format,
            bsd_syslog=bsd_syslog,
            vrf=vrf,
            comment=comment,
            disabled=disabled,
        ).model_dump(exclude_none=True)
        if not payload:
            raise ValueError("At least one update field must be provided")
        payload = _translate(payload)
        await manager.patch(f"system/logging/action/{action_id}", json=payload)
        return {"updated": True, "id": action_id}

    @mcp.tool(name="mikrotik_remove_logging_action", annotations=DESTRUCTIVE)
    async def remove_logging_action(
        action_id: str,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Remove a logging action by ID or name.

        Note: Default actions (memory, disk, echo, remote) may be recreated by
        RouterOS on reboot.
        """
        manager = get_manager(ctx)
        await manager.delete(f"system/logging/action/{action_id}")
        return {"removed": True, "id": action_id}
