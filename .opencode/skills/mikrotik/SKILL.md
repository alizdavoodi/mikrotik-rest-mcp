---
name: mikrotik
description: Manage MikroTik RouterOS devices via the mikrotik-rest-mcp server using skill_mcp to keep tool context lean.
mcp:
  mikrotik:
    command: uvx mikrotik-rest-mcp
    env:
      MIKROTIK_HOST: ${MIKROTIK_HOST}
      MIKROTIK_USERNAME: ${MIKROTIK_USERNAME}
      MIKROTIK_PASSWORD: ${MIKROTIK_PASSWORD}
      MIKROTIK_PORT: ${MIKROTIK_PORT:-80}
      MIKROTIK_USE_SSL: ${MIKROTIK_USE_SSL:-false}
      MIKROTIK_SSL_VERIFY: ${MIKROTIK_SSL_VERIFY:-false}
---

# MikroTik RouterOS Skill (Project Local)

Use this skill when you need RouterOS operations (IP, DNS, firewall, DHCP, interfaces, WireGuard, users, backups, logs).

## Why this skill is recommended

- This server exposes 100+ tools.
- Loading it through `skill_mcp` keeps the default tool list smaller until actually needed.
- A smaller active tool surface usually improves planning quality and reduces context pressure.

## Required environment variables

- `MIKROTIK_HOST` (required)
- `MIKROTIK_PASSWORD` (required)
- `MIKROTIK_USERNAME` (default: `admin`)
- `MIKROTIK_PORT` (default: `80`)
- `MIKROTIK_USE_SSL` (default: `false`)
- `MIKROTIK_SSL_VERIFY` (default: `false`)

Export these before launching OpenCode, then restart OpenCode if values change.

## Usage pattern

1. Load the skill: `skill(name="mikrotik")`
2. Call tools via `skill_mcp`:

```text
skill_mcp(mcp_name="mikrotik", tool_name="mikrotik_list_ip_addresses")
skill_mcp(mcp_name="mikrotik", tool_name="mikrotik_list_filter_rules", arguments={"chain_filter": "forward"})
skill_mcp(mcp_name="mikrotik", tool_name="mikrotik_get_dns_settings")
```

For high-impact changes (firewall/routing/restore/remove), explain impact first and request confirmation.
