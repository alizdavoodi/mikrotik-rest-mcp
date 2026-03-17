from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext

from ..app import DESTRUCTIVE, READ
from . import get_manager


def _filter_logs(
    rows: list[dict[str, Any]],
    topics: str | None,
    action: str | None,
    message_filter: str | None,
    prefix_filter: str | None,
) -> list[dict[str, Any]]:
    filtered = rows
    if topics:
        topic_set = {value.strip() for value in topics.split(",") if value.strip()}
        filtered = [
            row
            for row in filtered
            if topic_set.intersection(set(str(row.get("topics", "")).split(",")))
        ]
    if action:
        filtered = [
            row
            for row in filtered
            if action.lower() in str(row.get("message", "")).lower()
        ]
    if message_filter:
        filtered = [
            row
            for row in filtered
            if message_filter.lower() in str(row.get("message", "")).lower()
        ]
    if prefix_filter:
        prefixes = [p.strip() for p in prefix_filter.split(",") if p.strip()]
        if prefixes:
            filtered = [
                row
                for row in filtered
                if any(
                    str(row.get("message", "")).startswith(p)
                    or str(row.get("prefix", "")) == p
                    for p in prefixes
                )
            ]
    return filtered


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_get_logs", annotations=READ)
    async def get_logs(
        topics: str | None = None,
        action: str | None = None,
        time_filter: str | None = None,
        message_filter: str | None = None,
        prefix_filter: str | None = None,
        limit: int | None = None,
        follow: bool = False,
        print_as: str = "value",
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Return log entries with optional filters."""
        _ = (time_filter, follow, print_as)
        manager = get_manager(ctx)
        rows = await manager.get("log") or []
        filtered = _filter_logs(rows, topics, action, message_filter, prefix_filter)
        if limit is not None:
            filtered = filtered[:limit]
        return filtered

    @mcp.tool(name="mikrotik_search_logs", annotations=READ)
    async def search_logs(
        search_term: str,
        time_filter: str | None = None,
        case_sensitive: bool = False,
        limit: int | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Search log messages for a term."""
        _ = time_filter
        manager = get_manager(ctx)
        rows = await manager.get("log") or []
        if case_sensitive:
            filtered = [r for r in rows if search_term in str(r.get("message", ""))]
        else:
            lower = search_term.lower()
            filtered = [r for r in rows if lower in str(r.get("message", "")).lower()]
        if limit is not None:
            filtered = filtered[:limit]
        return filtered

    @mcp.tool(name="mikrotik_get_logs_by_severity", annotations=READ)
    async def get_logs_by_severity(
        severity: str,
        time_filter: str | None = None,
        limit: int | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Return logs filtered by severity topic."""
        _ = time_filter
        manager = get_manager(ctx)
        rows = await manager.get("log") or []
        filtered = [r for r in rows if severity in str(r.get("topics", "")).split(",")]
        if limit is not None:
            filtered = filtered[:limit]
        return filtered

    @mcp.tool(name="mikrotik_get_logs_by_topic", annotations=READ)
    async def get_logs_by_topic(
        topic: str,
        time_filter: str | None = None,
        limit: int | None = None,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """Return logs filtered by topic."""
        _ = time_filter
        manager = get_manager(ctx)
        rows = await manager.get("log") or []
        filtered = [r for r in rows if topic in str(r.get("topics", "")).split(",")]
        if limit is not None:
            filtered = filtered[:limit]
        return filtered

    @mcp.tool(name="mikrotik_clear_logs", annotations=DESTRUCTIVE)
    async def clear_logs(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Clear RouterOS logs."""
        manager = get_manager(ctx)
        await manager.post("log/clear")
        return {"cleared": True}
