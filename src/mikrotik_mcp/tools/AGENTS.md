# TOOLS — DOMAIN MODULES

17 self-contained tool modules. Each wraps a RouterOS REST API section as MCP tools.

## ADDING A NEW MODULE

1. Create `tools/<domain>.py` with a `register(mcp: FastMCP)` function
2. Import + call in `tools/__init__.py::register_tools()`

### Template (copy-paste starter)

```python
from __future__ import annotations
from typing import Annotated, Any
from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel, Field
from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager

class EntityCreate(BaseModel):
    name: str = Field(min_length=1)
    value: str | None = None
    comment: str | None = None
    disabled: bool = False

class EntityUpdate(BaseModel):
    name: str | None = None
    value: str | None = None
    comment: str | None = None
    disabled: bool | None = None

def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_list_entities", annotations=READ)
    async def list_entities(ctx: Context = CurrentContext()) -> list[dict[str, Any]]:
        """List entities."""
        manager = get_manager(ctx)
        return await manager.get("path/to/entity") or []

    @mcp.tool(name="mikrotik_get_entity", annotations=READ)
    async def get_entity(
        entity_id: Annotated[str, Field(min_length=1)],
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Get one entity."""
        manager = get_manager(ctx)
        result = await manager.get(f"path/to/entity/{entity_id}")
        if not result:
            raise ValueError(f"Entity not found: {entity_id}")
        return result

    @mcp.tool(name="mikrotik_create_entity", annotations=WRITE)
    async def create_entity(
        name: str, value: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create entity."""
        manager = get_manager(ctx)
        payload = EntityCreate(name=name, value=value).model_dump(exclude_none=True)
        result = await manager.put("path/to/entity", json=payload)
        return {"created": True, "id": result.get(".id")} if result else {"created": True}

    @mcp.tool(name="mikrotik_remove_entity", annotations=DESTRUCTIVE)
    async def remove_entity(
        entity_id: Annotated[str, Field(min_length=1)],
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Remove entity."""
        manager = get_manager(ctx)
        await manager.delete(f"path/to/entity/{entity_id}")
        return {"removed": True, "id": entity_id}
```

## CONVENTIONS (tools-specific)

- **Tool name**: `mikrotik_<verb>_<noun>` — verbs: list, get, create/add, update, remove, enable, disable, move
- **Annotations**: `READ` for queries, `WRITE` for creates/updates/enable/disable, `DESTRUCTIVE` for deletes
- **`ctx` always last param**: `ctx: Context = CurrentContext()`
- **Pydantic Create/Update models**: Defined at module top. Create has defaults; Update has all `| None`
- **`model_dump(exclude_none=True)`**: Strips unset fields before sending to API
- **Not found → `ValueError`**: NOT `NotFoundError` from exceptions.py
- **Return shape**: `{"<verb>ed": True, "id": ...}` for mutations; raw dict/list for reads

## DOMAIN MAP

| Module | REST Path | Tools | Notes |
|--------|-----------|-------|-------|
| `ip_address.py` | `ip/address` | 7 | `_filter_rows()` helper |
| `ip_route.py` | `ip/route` | 11 | Routing table, cache, stats, blackhole/default route helpers |
| `ip_pool.py` | `ip/pool` | 7 | `pool/used` sub-resource for used addresses |
| `dns.py` | `ip/dns` | 5 | Settings, cache, cache stats |
| `dns_static.py` | `ip/dns/static` | 7 | A, AAAA, CNAME, regexp entries |
| `firewall_filter.py` | `ip/firewall/filter` | 9 | `_translate()` snake→kebab, `create_basic_firewall_setup` |
| `firewall_nat.py` | `ip/firewall/nat` | 8 | `_translate()` same pattern as filter |
| `firewall_address_list.py` | `ip/firewall/address-list` | 4 | Timeout support |
| `interface_vlan.py` | `interface/vlan` | 5 | |
| `interface_wireless.py` | `interface/wireless` | 7 | `scan`, `registration-table` sub-resources |
| `interface_wireguard.py` | `interface/wireguard` | 8 | Two sub-domains: interfaces + peers |
| `system_users.py` | `user` | 8 | Users + groups + active sessions |
| `system_backup.py` | `system/backup` | 5 | File upload/download via `file` path |
| `system_logs.py` | `log` | 6 | Client-side severity/topic/search filtering |
| `dhcp_server.py` | `ip/dhcp-server` | 4 | |
| `dhcp_lease.py` | `ip/dhcp-server/lease` | 4 | |
| `dhcp_pool.py` | `ip/pool` | 5 | Shares REST path with `ip_pool.py` (DHCP context) |

## PATTERNS BY COMPLEXITY

**Simple** (ip_address, interface_vlan, dhcp_lease): Straight CRUD, no translation needed.

**With translation** (firewall_filter, firewall_nat): Have `_translate()` to convert `src_address` → `src-address`. Also convert `bool` → `"true"/"false"` string. Copy the `_translate()` function if adding firewall-adjacent modules.

**With sub-resources** (interface_wireguard, system_backup, ip_route): Multiple REST paths in one module. WireGuard manages both `interface/wireguard` and `interface/wireguard/peers`.

**With special operations** (ip_route, system_logs): Non-CRUD operations like cache flush (`DELETE ip/route/cache`), route path check (`POST`), log search (client-side filtering).

## ANTI-PATTERNS

- **No cross-module imports** — modules never import from each other
- **No shared base class for tools** — each module is fully standalone
- **No query-param filtering** — RouterOS REST API doesn't support it; all filtering is client-side via `_filter_rows()`
- **Never send Python `True`/`False` to RouterOS** — must be string `"true"`/`"false"`
