from __future__ import annotations

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from ..connection import MikrotikConnectionManager


def get_manager(ctx: Context) -> MikrotikConnectionManager:
    manager = ctx.lifespan_context.get("connection_manager")
    if not isinstance(manager, MikrotikConnectionManager):
        raise ToolError("MikroTik connection manager is not available")
    return manager


def register_tools(mcp: FastMCP) -> None:
    from . import (
        dhcp_lease,
        dhcp_pool,
        dhcp_server,
        dns,
        dns_static,
        firewall_address_list,
        firewall_filter,
        firewall_nat,
        interface_vlan,
        interface_wireguard,
        interface_wireless,
        ip_address,
        ip_pool,
        ip_route,
        system_backup,
        system_logging,
        system_logs,
        system_users,
    )

    ip_address.register(mcp)
    ip_route.register(mcp)
    ip_pool.register(mcp)
    dns.register(mcp)
    dns_static.register(mcp)
    firewall_filter.register(mcp)
    firewall_nat.register(mcp)
    firewall_address_list.register(mcp)
    interface_vlan.register(mcp)
    interface_wireless.register(mcp)
    interface_wireguard.register(mcp)
    system_users.register(mcp)
    system_backup.register(mcp)
    system_logs.register(mcp)
    system_logging.register(mcp)
    dhcp_server.register(mcp)
    dhcp_lease.register(mcp)
    dhcp_pool.register(mcp)
