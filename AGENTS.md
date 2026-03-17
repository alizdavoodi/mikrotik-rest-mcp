# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-16
**Branch:** main (no commits yet)

## OVERVIEW

FastMCP server exposing MikroTik RouterOS REST API (v7.1+) as MCP tools. Python 3.11+, async httpx, Pydantic validation. 17 tool modules across 6 domains.

## STRUCTURE

```
mikrotik-api-mcp/
├── src/mikrotik_mcp/
│   ├── server.py        # Entry point — transport selection (stdio/sse/streamable-http)
│   ├── app.py           # FastMCP instance + lifespan (connection lifecycle)
│   ├── config.py        # Pydantic BaseSettings — env vars MIKROTIK_* prefix
│   ├── connection.py    # httpx AsyncClient wrapper — all REST calls go through here
│   ├── exceptions.py    # MikrotikMcpError → ConnectionError | NotFoundError | ValidationError
│   ├── __init__.py      # Exports: main, mcp
│   └── tools/           # 17 domain tool modules (see tools/AGENTS.md)
├── pyproject.toml       # setuptools, src-layout, 4 deps
├── shell.nix            # Nix dev env — Python 3.12 + auto-venv
└── .env.example         # Required: MIKROTIK_HOST, USERNAME, PASSWORD
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new tool domain | `tools/<domain>.py` + `tools/__init__.py` | See `tools/AGENTS.md` for pattern |
| Change connection behavior | `connection.py` | All HTTP goes through `MikrotikConnectionManager.request()` |
| Add config option | `config.py` | Pydantic BaseSettings, env prefix `MIKROTIK_` |
| Add transport mode | `server.py` | Currently: stdio, sse, streamable-http |
| Change tool annotations | `app.py` | READ / WRITE / DESTRUCTIVE hint dicts |
| Add custom exception | `exceptions.py` | Inherit from `MikrotikMcpError` |

## ARCHITECTURE

```
server.py → app.py → FastMCP(lifespan=...) → tools/__init__.py::register_tools()
                ↓
         lifespan context manager
                ↓
         MikrotikConnectionManager (connect/disconnect lifecycle)
                ↓
         Injected into tools via ctx.lifespan_context["connection_manager"]
```

**Request flow**: Tool function → `get_manager(ctx)` → `manager.get/put/patch/delete("path")` → httpx → `/rest/<path>` on RouterOS

**REST API mapping**:
- GET = read, PUT = create, PATCH = update, DELETE = remove
- Path pattern: `ip/address`, `ip/route`, `ip/firewall/filter`, etc.
- 404 → returns `None`, 204 → returns `{}`

## CONVENTIONS

- **Tool naming**: `mikrotik_<verb>_<domain>` (e.g., `mikrotik_list_ip_addresses`)
- **Tool annotations**: Always one of `READ`, `WRITE`, or `DESTRUCTIVE` from `app.py`
- **Context param**: Always last: `ctx: Context = CurrentContext()`
- **Validation**: Pydantic BaseModel per Create/Update operation, `model_dump(exclude_none=True)`
- **Not found**: Raise `ValueError(f"... not found: {id}")` — NOT custom exceptions
- **Enable/disable**: PATCH with `{"disabled": "true"/"false"}` (string, not bool)
- **Filtering**: Client-side `_filter_rows()` helpers, not query params
- **Payload translation**: Snake_case Python → kebab-case RouterOS in firewall modules via `_translate()`

## ANTI-PATTERNS (THIS PROJECT)

- **No `as any` / type suppression** — Pydantic handles validation
- **No direct httpx usage in tools** — Always go through `MikrotikConnectionManager`
- **No cross-domain imports between tool modules** — Each module is self-contained
- **No global state** — Connection manager lives in lifespan context only
- **Booleans to RouterOS**: Must be string `"true"`/`"false"`, never Python `True`/`False`

## COMMANDS

```bash
# Dev environment
nix-shell                              # Enter dev env (auto-creates venv, installs deps)

# Run server
python -m mikrotik_mcp.server          # stdio transport (default)
MIKROTIK__MCP__TRANSPORT=sse python -m mikrotik_mcp.server  # SSE transport

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m mikrotik_mcp.server

# Required env vars
export MIKROTIK_HOST=192.168.88.1
export MIKROTIK_USERNAME=admin
export MIKROTIK_PASSWORD=yourpassword
```

## NOTES

- **No tests yet** — README mentions pytest/mypy but no test infrastructure exists
- **No CI/CD** — No GitHub Actions, no Makefile
- **No dev deps defined** — pyproject.toml lacks `[project.optional-dependencies]`
- **No `[project.scripts]`** — `mikrotik-mcp` CLI command not wired in pyproject.toml
- **Port mismatch**: `.env.example` shows port 8728 (old API) but code defaults to 80 (REST API)
- **Config caching**: `get_settings()` uses `@lru_cache(maxsize=1)` — singleton per process
