<!-- prettier-ignore -->
<div align="center">

# MikroTik MCP Server

_FastMCP server that exposes MikroTik RouterOS REST API as MCP tools_

[![Python](https://img.shields.io/badge/Python->=3.11-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![RouterOS](https://img.shields.io/badge/RouterOS-v7.1+-e4182c?style=flat-square)](https://mikrotik.com)
[![FastMCP](https://img.shields.io/badge/FastMCP->=3.1-6f42c1?style=flat-square)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[Overview](#overview) • [Get Started](#get-started) • [Configuration](#configuration) • [OpenCode Skill](#opencode-skill-recommended) • [Troubleshooting](#troubleshooting)

</div>

Manage MikroTik devices from any MCP-compatible client (Claude Desktop, OpenCode, or custom MCP clients) using a single server package.

> [!NOTE]
> This project exposes **100+ tools** across IP, firewall, DNS, DHCP, interfaces, and system domains. For OpenCode, skill-first usage is recommended to avoid loading a very large tool surface into context by default.

## Overview

This server wraps RouterOS REST endpoints (`/rest/...`) and exposes them as typed MCP tools.

- Built with `FastMCP` + async `httpx`
- Pydantic validation for inputs and settings
- `stdio`, `sse`, and `streamable-http` transport modes
- Single connection manager shared through MCP lifespan

## Get Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or any PEP 517 installer
- MikroTik RouterOS v7.1+ with REST API reachable

### OpenCode Skill (recommended)

This repo ships a project-local OpenCode skill:

- `.opencode/skills/mikrotik/SKILL.md`

Why this is the best default in OpenCode:

- `mikrotik-rest-mcp` has a large tool set, which can inflate context if always loaded globally.
- Skill-first workflow activates the MCP tool surface only when needed.
- Skill config explicitly passes `MIKROTIK_*` into the spawned MCP process.

Usage:

```text
skill(name="mikrotik")
skill_mcp(mcp_name="mikrotik", tool_name="mikrotik_list_ip_addresses")
skill_mcp(mcp_name="mikrotik", tool_name="mikrotik_get_dns_settings")
```

### Install

Run without installing (recommended):

```bash
uvx mikrotik-rest-mcp
```

Install into current environment:

```bash
uv pip install mikrotik-rest-mcp
```

From source (contributors):

```bash
uv sync --dev
```

If you prefer Nix for development:

```bash
nix develop
```

### Run

```bash
export MIKROTIK_HOST=192.168.88.1
export MIKROTIK_USERNAME=admin
export MIKROTIK_PASSWORD=yourpassword
export MIKROTIK_PORT=80

uvx mikrotik-rest-mcp
```

Test with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uvx mikrotik-rest-mcp
```

## Configuration

All settings are read from process environment variables.

| Variable                   | Description                                      | Default      |
| -------------------------- | ------------------------------------------------ | ------------ |
| `MIKROTIK_HOST`            | Router IP or hostname                            | _(required)_ |
| `MIKROTIK_USERNAME`        | Router username                                  | `admin`      |
| `MIKROTIK_PASSWORD`        | Router password                                  | _(required)_ |
| `MIKROTIK_PORT`            | RouterOS REST API port                           | `80`         |
| `MIKROTIK_USE_SSL`         | Use HTTPS                                        | `false`      |
| `MIKROTIK_SSL_VERIFY`      | Verify TLS certificate                           | `false`      |
| `MIKROTIK__MCP__TRANSPORT` | MCP transport: `stdio`, `sse`, `streamable-http` | `stdio`      |
| `MIKROTIK__MCP__HOST`      | Bind host for non-stdio transports               | `0.0.0.0`    |
| `MIKROTIK__MCP__PORT`      | Bind port for non-stdio transports               | `8000`       |

> [!IMPORTANT]
> `mikrotik-rest-mcp` reads **process env**. It does not auto-load `.env`. In MCP clients, prefer setting variables in the client's `env` / `environment` block.

SSE example:

```bash
MIKROTIK__MCP__TRANSPORT=sse uvx mikrotik-rest-mcp
```

## Tool Coverage

Registered domains include:

- **IP**: addresses, routes, pools
- **DNS**: resolver config, cache, static entries
- **Firewall**: filter rules, NAT, address lists
- **Interfaces**: VLAN, wireless, WireGuard
- **DHCP**: servers, leases, pools
- **System**: users, backups, logs, logging rules/actions

Tool naming convention follows `mikrotik_<verb>_<resource>`.

## Global Skill Setup (all sessions)

If you want this skill available in every session (not just this repo), install it globally.

### OpenCode global paths

- `~/.config/opencode/skills/<skill-name>/SKILL.md` (OpenCode native)
- `~/.claude/skills/<skill-name>/SKILL.md` (Claude-compatible path often used with OpenCode setups)
- `~/.agents/skills/<skill-name>/SKILL.md` (Agent Skills compatibility path)

### Claude Code global path

- `~/.claude/skills/<skill-name>/SKILL.md`

### Recommended cross-compatible path

Use `~/.claude/skills/mikrotik/SKILL.md` so both OpenCode and Claude sessions can discover it.

Install globally from a repo checkout:

```bash
mkdir -p ~/.claude/skills/mikrotik
cp .opencode/skills/mikrotik/SKILL.md ~/.claude/skills/mikrotik/SKILL.md
```

> [!TIP]
> Export `MIKROTIK_*` before launching OpenCode/Claude, then restart the app/session after changing env values.

## MCP Client Examples

### Claude Desktop

```json
{
  "mcpServers": {
    "mikrotik": {
      "command": "uvx",
      "args": ["mikrotik-rest-mcp"],
      "env": {
        "MIKROTIK_HOST": "192.168.88.1",
        "MIKROTIK_USERNAME": "admin",
        "MIKROTIK_PASSWORD": "yourpassword",
        "MIKROTIK_PORT": "80"
      }
    }
  }
}
```

### OpenCode

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "mikrotik": {
      "type": "local",
      "command": ["uvx", "mikrotik-rest-mcp"],
      "environment": {
        "MIKROTIK_HOST": "192.168.88.1",
        "MIKROTIK_USERNAME": "admin",
        "MIKROTIK_PASSWORD": "yourpassword",
        "MIKROTIK_PORT": "80"
      }
    }
  }
}
```

## Architecture

```text
server.py -> app.py -> FastMCP(lifespan)
                    -> tools.register_tools()
                    -> MikrotikConnectionManager
                    -> RouterOS REST API (/rest/...)
```

- `src/mikrotik_rest_mcp/server.py`: entrypoint + transport selection
- `src/mikrotik_rest_mcp/app.py`: FastMCP app + lifecycle wiring
- `src/mikrotik_rest_mcp/connection.py`: async HTTP client and request handling
- `src/mikrotik_rest_mcp/tools/`: domain tool modules

## Troubleshooting

### `MCP error -32000: Connection closed`

This usually means server startup failed early or env vars were missing in the spawned process.

Check raw startup error:

```bash
uvx mikrotik-rest-mcp 2>&1
```

If you use OpenCode `skill_mcp`, ensure `MIKROTIK_*` are set in skill/client config or exported before app startup.

### Validate connectivity quickly

```bash
export MIKROTIK_HOST=192.168.88.1
export MIKROTIK_USERNAME=admin
export MIKROTIK_PASSWORD=yourpassword
curl -u "$MIKROTIK_USERNAME:$MIKROTIK_PASSWORD" "http://$MIKROTIK_HOST/rest/system/resource"
```

If you use HTTPS, switch the URL to `https://` and apply your TLS verification settings.

## Security Notes

> [!IMPORTANT]
> This server can modify live network configuration.

- Use a dedicated RouterOS user with minimum required permissions.
- Prefer HTTPS (`MIKROTIK_USE_SSL=true`, `MIKROTIK_PORT=443`) in production.
- Restrict RouterOS REST access by source IP/firewall rules.
- Never commit secrets.
