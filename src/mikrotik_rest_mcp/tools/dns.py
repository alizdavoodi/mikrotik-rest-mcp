"""Bespoke DNS tools.

DNS configuration is a RouterOS singleton (``/ip/dns`` is one record, not a
collection), so it doesn't fit the Submenu CRUD pattern.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from ..app import READ, WRITE
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_get_dns_settings", annotations=READ)
    async def get_dns_settings(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Get current DNS configuration."""
        manager = get_manager(ctx)
        result = await manager.get("ip/dns")
        return result or {}

    @mcp.tool(name="mikrotik_set_dns_servers", annotations=WRITE)
    async def set_dns_servers(
        servers: Annotated[list[str], Field(min_length=1)],
        allow_remote_requests: bool = False,
        max_udp_packet_size: int | None = None,
        max_concurrent_queries: int | None = None,
        cache_size: int | None = None,
        cache_max_ttl: str | None = None,
        use_doh: bool = False,
        doh_server: str | None = None,
        verify_doh_cert: bool = True,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Set DNS server configuration."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {
            "servers": ",".join(servers),
            "allow-remote-requests": "true" if allow_remote_requests else "false",
            "use-doh-server": "true" if use_doh else "false",
            "verify-doh-cert": "true" if verify_doh_cert else "false",
        }
        if max_udp_packet_size is not None:
            payload["max-udp-packet-size"] = max_udp_packet_size
        if max_concurrent_queries is not None:
            payload["max-concurrent-queries"] = max_concurrent_queries
        if cache_size is not None:
            payload["cache-size"] = cache_size
        if cache_max_ttl:
            payload["cache-max-ttl"] = cache_max_ttl
        if doh_server:
            payload["doh-server"] = doh_server
        await manager.patch("ip/dns", json=payload)
        return {"updated": True}

    @mcp.tool(name="mikrotik_get_dns_cache", annotations=READ)
    async def get_dns_cache(ctx: Context = CurrentContext()) -> list[dict[str, Any]]:
        """Get the current DNS cache."""
        manager = get_manager(ctx)
        return await manager.get("ip/dns/cache") or []

    @mcp.tool(name="mikrotik_flush_dns_cache", annotations=WRITE)
    async def flush_dns_cache(ctx: Context = CurrentContext()) -> dict[str, Any]:
        """Flush the DNS cache."""
        manager = get_manager(ctx)
        await manager.delete("ip/dns/cache")
        return {"flushed": True}

    @mcp.tool(name="mikrotik_get_dns_cache_statistics", annotations=READ)
    async def get_dns_cache_statistics(
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Get DNS cache statistics."""
        manager = get_manager(ctx)
        return await manager.get("ip/dns/cache/all") or {}
