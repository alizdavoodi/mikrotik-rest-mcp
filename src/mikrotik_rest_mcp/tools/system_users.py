from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    password: str = Field(min_length=1)
    group: str = "read"
    address: str | None = None
    comment: str | None = None
    disabled: bool = False


class UserUpdate(BaseModel):
    new_name: str | None = None
    password: str | None = None
    group: str | None = None
    address: str | None = None
    comment: str | None = None
    disabled: bool | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_users", annotations=READ)
    async def list_users(
        name_filter: str | None = None,
        group_filter: str | None = None,
        disabled_only: bool = False,
        active_only: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists users on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("user") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if group_filter:
            filtered = [r for r in filtered if r.get("group") == group_filter]
        if disabled_only:
            filtered = [r for r in filtered if r.get("disabled") == "true"]
        if active_only:
            filtered = [r for r in filtered if r.get("active") == "true"]
        return filtered

    @mcp.tool(name="mikrotik_get_user", annotations=READ)
    async def get_user(name: str, ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Gets detailed information about a specific user."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("user")
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        for user in rows:
            if user.get("name") == name:
                return user
        raise ValueError(f"User not found: {name}")

    @mcp.tool(name="mikrotik_create_user", annotations=WRITE)
    async def create_user(
        name: str,
        password: str,
        group: str = "read",
        address: str | None = None,
        comment: str | None = None,
        disabled: bool = False,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds a user to MikroTik device."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "name": name,
            "password": password,
            "group": group,
            "disabled": "true" if disabled else "false",
        }
        if address:
            payload["address"] = address
        if comment:
            payload["comment"] = comment
        await manager.put("user", json=payload)
        return {"created": True, "name": name}

    @mcp.tool(name="mikrotik_update_user", annotations=WRITE)
    async def update_user(
        name: str,
        new_name: str | None = None,
        password: str | None = None,
        group: str | None = None,
        address: str | None = None,
        comment: str | None = None,
        disabled: bool | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Updates a user."""
        manager = get_manager(ctx)
        rows = await manager.get("user") or []
        user_id = None
        for user in rows:
            if user.get("name") == name:
                user_id = user.get(".id")
                break
        if not user_id:
            raise ValueError(f"User not found: {name}")
        payload: dict[str, Any] = {}
        if new_name:
            payload["name"] = new_name
        if password:
            payload["password"] = password
        if group:
            payload["group"] = group
        if address is not None:
            payload["address"] = address
        if comment is not None:
            payload["comment"] = comment
        if disabled is not None:
            payload["disabled"] = "true" if disabled else "false"
        if not payload:
            raise ValueError("At least one update field must be provided")
        await manager.patch(f"user/{user_id}", json=payload)
        return {"updated": True, "name": name}

    @mcp.tool(name="mikrotik_remove_user", annotations=DESTRUCTIVE)
    async def remove_user(name: str, ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Removes a user."""
        manager = get_manager(ctx)
        rows = await manager.get("user") or []
        user_id = None
        for user in rows:
            if user.get("name") == name:
                user_id = user.get(".id")
                break
        if not user_id:
            raise ValueError(f"User not found: {name}")
        await manager.delete(f"user/{user_id}")
        return {"removed": True, "name": name}

    @mcp.tool(name="mikrotik_disable_user", annotations=WRITE)
    async def disable_user(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Disables a user."""
        manager = get_manager(ctx)
        rows = await manager.get("user") or []
        user_id = None
        for user in rows:
            if user.get("name") == name:
                user_id = user.get(".id")
                break
        if not user_id:
            raise ValueError(f"User not found: {name}")
        await manager.patch(f"user/{user_id}", json={"disabled": "true"})
        return {"disabled": True, "name": name}

    @mcp.tool(name="mikrotik_enable_user", annotations=WRITE)
    async def enable_user(name: str, ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Enables a user."""
        manager = get_manager(ctx)
        rows = await manager.get("user") or []
        user_id = None
        for user in rows:
            if user.get("name") == name:
                user_id = user.get(".id")
                break
        if not user_id:
            raise ValueError(f"User not found: {name}")
        await manager.patch(f"user/{user_id}", json={"disabled": "false"})
        return {"enabled": True, "name": name}

    @mcp.tool(name="mikrotik_list_user_groups", annotations=READ)
    async def list_user_groups(
        name_filter: str | None = None,
        policy_filter: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Lists user groups on MikroTik device."""
        manager = get_manager(ctx)
        rows = await manager.get("user/group") or []
        filtered = rows
        if name_filter:
            filtered = [r for r in filtered if name_filter in str(r.get("name", ""))]
        if policy_filter:
            filtered = [
                r for r in filtered if policy_filter in str(r.get("policy", ""))
            ]
        return filtered

    @mcp.tool(name="mikrotik_get_user_group", annotations=READ)
    async def get_user_group(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Gets detailed information about a specific user group."""
        manager = get_manager(ctx)
        rows_raw = await manager.get("user/group")
        rows = (
            [row for row in rows_raw if isinstance(row, dict)]
            if isinstance(rows_raw, list)
            else []
        )
        for group in rows:
            if group.get("name") == name:
                return group
        raise ValueError(f"User group not found: {name}")

    @mcp.tool(name="mikrotik_create_user_group", annotations=WRITE)
    async def create_user_group(
        name: str,
        policy: list[str],
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Adds a user group."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {"name": name, "policy": ",".join(policy)}
        if comment:
            payload["comment"] = comment
        await manager.put("user/group", json=payload)
        return {"created": True, "name": name}

    @mcp.tool(name="mikrotik_remove_user_group", annotations=DESTRUCTIVE)
    async def remove_user_group(
        name: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Removes a user group."""
        manager = get_manager(ctx)
        rows = await manager.get("user/group") or []
        group_id = None
        for group in rows:
            if group.get("name") == name:
                group_id = group.get(".id")
                break
        if not group_id:
            raise ValueError(f"User group not found: {name}")
        await manager.delete(f"user/group/{group_id}")
        return {"removed": True, "name": name}

    @mcp.tool(name="mikrotik_get_active_users", annotations=READ)
    async def get_active_users(ctx: Context = CurrentContext()) -> list[dict[str, Any]]:
        """Gets currently active/logged-in users."""
        manager = get_manager(ctx)
        return await manager.get("user/active") or []
