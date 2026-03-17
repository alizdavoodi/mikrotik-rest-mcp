from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.exceptions import ToolError

from ..connection import MikrotikConnectionManager


def get_manager(ctx) -> MikrotikConnectionManager:
    manager = ctx.lifespan_context.get("connection_manager")
    if not isinstance(manager, MikrotikConnectionManager):
        raise ToolError("MikroTik connection manager is not available")
    return manager


def register_tools(mcp: FastMCP) -> None:
    from . import dhcp_lease
    from . import dhcp_pool
    from . import dhcp_server
    from . import dns
    from . import dns_static
    from . import firewall_address_list
    from . import firewall_filter
    from . import firewall_nat
    from . import interface_vlan
    from . import interface_wireguard
    from . import interface_wireless
    from . import ip_address
    from . import ip_pool
    from . import ip_route
    from . import system_backup
    from . import system_logs
    from . import system_logging
    from . import system_users

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
