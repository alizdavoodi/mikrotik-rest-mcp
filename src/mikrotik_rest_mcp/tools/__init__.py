"""MCP tool registration.

Most tools are synthesized from :data:`mikrotik_rest_mcp.submenus.SUBMENUS`.
Bespoke (non-CRUD) tools live in this package and register themselves.
"""

from __future__ import annotations

from fastmcp import Context, FastMCP

from ..connection import MikrotikConnectionManager
from ..submenu import get_manager
from ..submenus import register_all

__all__ = ["MikrotikConnectionManager", "get_manager", "register_tools"]


def register_tools(mcp: FastMCP) -> None:
    """Register every MikroTik MCP tool on ``mcp``."""
    register_all(mcp)

    # Bespoke (non-CRUD) tools — registered per module.
    from . import (
        dns,
        firewall_filter,
        interface_wireless,
        ip_pool,
        ip_route,
        system_backup,
        system_logs,
        system_users,
    )

    for module in (
        dns,
        ip_pool,
        ip_route,
        firewall_filter,
        interface_wireless,
        system_backup,
        system_logs,
        system_users,
    ):
        module.register(mcp)


# Re-export Context for any callers that still import it from here.
_ = Context  # noqa: F401
