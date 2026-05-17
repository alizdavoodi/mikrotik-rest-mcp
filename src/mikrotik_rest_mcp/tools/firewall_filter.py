"""Bespoke firewall_filter tools.

CRUD for ``ip/firewall/filter`` is registered from submenus. This module only
holds the convenience workflow ``mikrotik_create_basic_firewall_setup``.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext

from ..app import WRITE
from ..submenu import get_manager


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_create_basic_firewall_setup", annotations=WRITE)
    async def create_basic_firewall_setup(
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a basic firewall setup with common security rules."""
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
