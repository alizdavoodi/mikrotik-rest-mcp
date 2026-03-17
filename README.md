<!-- prettier-ignore -->
<div align="center">

# MikroTik MCP Server

*Manage MikroTik RouterOS devices through the Model Context Protocol*

[![Python](https://img.shields.io/badge/Python->=3.11-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![MikroTik](https://img.shields.io/badge/RouterOS-v7.1+-e22a27?style=flat-square)](https://mikrotik.com)
[![FastMCP](https://img.shields.io/badge/FastMCP->=3.1-6f42c1?style=flat-square)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[Overview](#overview) • [Getting Started](#getting-started) • [Configuration](#configuration) • [Features](#features) • [Architecture](#architecture) • [Security](#security)

</div>

## Overview

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes MikroTik RouterOS management capabilities as tools for AI assistants. Built with [FastMCP](https://github.com/jlowin/fastmcp), it connects to your router's REST API and provides **100+ tools** across 6 domains — IP management, firewall, DNS, DHCP, interfaces, and system administration.

Use it with Claude Desktop, or any MCP-compatible client to manage your MikroTik devices through natural language.

## Getting Started

### Prerequisites

- **Python 3.11+**
- **MikroTik RouterOS v7.1+** with the REST API enabled (available on port 80/443 by default)

### Installation

```bash
git clone https://github.com/yourusername/mikrotik-api-mcp.git
cd mikrotik-api-mcp
pip install -e .
```

<details>
<summary><strong>Using Nix</strong></summary>

If you have [Nix](https://nixos.org) installed, enter the development shell which sets up Python and a virtual environment automatically:

```bash
nix-shell
```

</details>

### Quick Start

1. Set your router credentials:

    ```bash
    export MIKROTIK_HOST=192.168.88.1
    export MIKROTIK_USERNAME=admin
    export MIKROTIK_PASSWORD=yourpassword
    ```

2. Run the server:

    ```bash
    python -m mikrotik_mcp.server
    ```

3. Or test interactively with MCP Inspector:

    ```bash
    npx @modelcontextprotocol/inspector python -m mikrotik_mcp.server
    ```

### Usage with Claude Desktop

Add the following to your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mikrotik": {
      "command": "python",
      "args": ["-m", "mikrotik_mcp.server"],
      "env": {
        "MIKROTIK_HOST": "192.168.88.1",
        "MIKROTIK_USERNAME": "admin",
        "MIKROTIK_PASSWORD": "yourpassword"
      }
    }
  }
}
```

## Configuration

All settings are configured through environment variables (or a `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `MIKROTIK_HOST` | Router IP or hostname | *(required)* |
| `MIKROTIK_USERNAME` | API username | `admin` |
| `MIKROTIK_PASSWORD` | API password | *(required)* |
| `MIKROTIK_PORT` | REST API port | `80` |
| `MIKROTIK_USE_SSL` | Enable HTTPS | `false` |
| `MIKROTIK_SSL_VERIFY` | Verify SSL certificate | `false` |
| `MIKROTIK__MCP__TRANSPORT` | MCP transport: `stdio`, `sse`, `streamable-http` | `stdio` |
| `MIKROTIK__MCP__HOST` | Server bind address (non-stdio) | `0.0.0.0` |
| `MIKROTIK__MCP__PORT` | Server port (non-stdio) | `8000` |

> [!TIP]
> Copy `.env.example` to `.env` and edit it to get started quickly. Note that the REST API uses port **80** (HTTP) or **443** (HTTPS) — not the legacy API port 8728.

### Running with SSE transport

```bash
MIKROTIK__MCP__TRANSPORT=sse python -m mikrotik_mcp.server
```

## Features

### IP Management
- **IP Addresses** — List, get, add, update, remove, enable/disable addresses on interfaces
- **Routing** — Full route table management, path checking, blackhole routes, cache control, statistics
- **IP Pools** — Create and manage address pools, view used addresses

### DNS
- **Server Config** — Get/set DNS servers, DoH configuration, cache management
- **Static Entries** — Full CRUD for A, AAAA, CNAME, and regexp DNS records

### Firewall
- **Filter Rules** — Complete rule management with ordering, enable/disable, and a basic setup wizard
- **NAT Rules** — Source and destination NAT with full CRUD and rule ordering
- **Address Lists** — Manage address lists with optional timeout entries

### Interfaces
- **VLAN** — Create and manage VLAN interfaces on any parent interface
- **Wireless** — Manage wireless interfaces, scan for networks, view connected clients
- **WireGuard** — Full VPN management for both interfaces and peers

### DHCP
- **Servers** — Create and manage DHCP server instances
- **Leases** — View and manage dynamic/static lease reservations
- **Pools** — Configure address pools for DHCP distribution

### System
- **Users** — User and group management with policy control, view active sessions
- **Backups** — Create, list, download, upload, and restore system backups
- **Logs** — Query logs by severity, topic, or free-text search

## Architecture

```
src/mikrotik_mcp/
├── server.py         # Entry point — transport selection
├── app.py            # FastMCP instance + connection lifespan
├── config.py         # Pydantic settings (env vars)
├── connection.py     # Async HTTP client (httpx)
├── exceptions.py     # Error hierarchy
└── tools/            # 17 domain modules
    ├── ip_address.py
    ├── ip_route.py
    ├── ip_pool.py
    ├── dns.py
    ├── dns_static.py
    ├── firewall_filter.py
    ├── firewall_nat.py
    ├── firewall_address_list.py
    ├── interface_vlan.py
    ├── interface_wireless.py
    ├── interface_wireguard.py
    ├── system_users.py
    ├── system_backup.py
    ├── system_logs.py
    ├── dhcp_server.py
    ├── dhcp_lease.py
    └── dhcp_pool.py
```

The server communicates with RouterOS through its REST API (`/rest/...`) using async HTTP via [httpx](https://www.python-httpx.org/). Each tool module is self-contained and registers its tools with the FastMCP instance on startup. Connection lifecycle is managed through FastMCP's lifespan context — a single authenticated `httpx.AsyncClient` is shared across all tool invocations.

## Security

> [!IMPORTANT]
> The MCP server has full access to your MikroTik device through the REST API. Follow these practices to minimize risk.

- **Use HTTPS in production** — Set `MIKROTIK_USE_SSL=true` and `MIKROTIK_PORT=443`
- **Create a dedicated API user** with only the permissions your use case requires
- **Restrict API access by IP** using MikroTik firewall rules
- **Never commit credentials** — Use environment variables or `.env` files (already in `.gitignore`)
- **Self-signed certificates** — Set `MIKROTIK_SSL_VERIFY=false` if your router uses a self-signed cert

## Development

```bash
# Enter dev environment (Nix)
nix-shell

# Or manually
pip install -e .

# Run the server
python -m mikrotik_mcp.server

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m mikrotik_mcp.server
```
