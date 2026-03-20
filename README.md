<!-- prettier-ignore -->
<div align="center">

# MikroTik MCP Server

_FastMCP server that exposes MikroTik RouterOS REST API as MCP tools_

[![Python](https://img.shields.io/badge/Python->=3.11-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![RouterOS](https://img.shields.io/badge/RouterOS-v7.1+-e4182c?style=flat-square)](https://mikrotik.com)
[![FastMCP](https://img.shields.io/badge/FastMCP->=3.1-6f42c1?style=flat-square)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[Overview](#overview) • [Get Started](#get-started) • [Configuration](#configuration) • [MCP Client Setup](#mcp-client-setup) • [Troubleshooting](#troubleshooting)

</div>

Manage MikroTik devices from any MCP-compatible client (Claude Code, Claude Desktop, OpenCode, or custom MCP clients) using a single server package.

> [!NOTE]
> This server exposes **100+ tools** across IP, firewall, DNS, DHCP, interfaces, and system domains. This large tool surface can consume significant context window space. See [Context Window Considerations](#context-window-considerations) for recommendations.

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

## MCP Client Setup

### Context Window Considerations

This server registers **100+ tools**. When an MCP client loads all tool definitions into context at startup, this can consume a substantial portion of the available context window — leaving less room for conversation and reasoning.

**Recommendations:**

- **Use lazy-loading / tool search if your client supports it.** This defers tool definition loading until a tool is actually needed, keeping context lean.
- **Claude Code** supports this via [MCP tool search](https://docs.anthropic.com/en/docs/claude-code/settings#tool-search). Enable it by setting `CLAUDE_MCP_TOOL_SEARCH=true` in your environment before launching Claude Code. This is the **recommended** approach when using Claude Code with this server.
- If your client does not support lazy loading, consider whether you need all domains active. You can still use the server — just be aware of the context cost.

### Claude Code

Add to your project-level `.mcp.json` (recommended) or global `~/.claude/settings.json`:

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

> [!TIP]
> Enable tool search to avoid loading 100+ tool definitions into context:
>
> ```bash
> export CLAUDE_MCP_TOOL_SEARCH=true
> claude
> ```

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

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

Add to your OpenCode config (`opencode.json`):

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

Ensure `MIKROTIK_*` variables are set in your client's env/environment config block, or exported before launching the client.

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
