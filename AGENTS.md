# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-18
**Commit:** `2f98e6e` (main)

## OVERVIEW

FastMCP server exposing MikroTik RouterOS REST API (v7.1+) as MCP tools. Python 3.11+, async httpx, Pydantic validation. 122 tools across 17 modules in 6 domains (IP, DNS, Firewall, Interfaces, DHCP, System).

## STRUCTURE

```
mikrotik-rest-mcp/
├── src/mikrotik_rest_mcp/
│   ├── server.py        # Entry point — transport selection (stdio/sse/streamable-http)
│   ├── app.py           # FastMCP instance + lifespan + READ/WRITE/DESTRUCTIVE annotations
│   ├── config.py        # Pydantic BaseSettings — env vars MIKROTIK_* prefix, lru_cache singleton
│   ├── connection.py    # httpx AsyncClient wrapper — all REST calls go through here
│   ├── exceptions.py    # MikrotikMcpError → ConnectionError | NotFoundError | ValidationError
│   ├── __init__.py      # Exports: main, mcp
│   └── tools/           # 17 domain tool modules (see tools/AGENTS.md)
│       └── __init__.py  # register_tools() + get_manager() helper
├── tests/
│   ├── conftest.py      # Shared fixtures: mock_context, mock_connection_manager, sample data
│   ├── test_config.py   # 11 tests — config validation, base URL, port bounds
│   ├── test_connection.py  # 16 tests — HTTP ops, error handling, auth
│   ├── test_exceptions.py  # 7 tests — exception hierarchy
│   └── test_tools/      # Tool-specific tests (mirror src/tools/)
│       ├── test_ip_address.py       # 13 tests
│       └── test_firewall_filter.py  # 17 tests
├── pyproject.toml       # setuptools src-layout, 4 core + 5 dev deps, ruff/mypy/pytest config
├── flake.nix            # Nix flake — uv2nix, Python 3.12, editable dev shell
├── shell.nix            # Compat shim → flake.nix
├── .env.example         # Required: MIKROTIK_HOST, PASSWORD. Optional: PORT, SSL, MCP transport
└── README.md            # Setup, configuration, MCP client examples, troubleshooting
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new tool domain | `tools/<domain>.py` + `tools/__init__.py` | See `tools/AGENTS.md` for template |
| Change connection behavior | `connection.py` | All HTTP goes through `MikrotikConnectionManager.request()` |
| Add config option | `config.py` | Pydantic BaseSettings, env prefix `MIKROTIK_`, nested delimiter `__` |
| Add transport mode | `server.py` | Currently: stdio, sse, streamable-http |
| Change tool annotations | `app.py` | `READ` / `WRITE` / `DESTRUCTIVE` hint dicts |
| Add custom exception | `exceptions.py` | Inherit from `MikrotikMcpError` |
| Add/modify tests | `tests/` | Mirrors `src/` structure. Use `conftest.py` fixtures |
| Modify dev environment | `flake.nix` | uv2nix + pyproject-nix, editable overlay |
| Change linting rules | `pyproject.toml` | `[tool.ruff]`, `[tool.mypy]` sections |

## ARCHITECTURE

```
server.py::main()
    ↓ get_settings() → MikrotikConfig (validates env vars)
    ↓ mcp.run(transport=...)
app.py
    ↓ FastMCP("mikrotik-rest-mcp", lifespan=lifespan)
    ↓ lifespan context manager:
    │   create MikrotikConnectionManager(settings)
    │   → manager.connect() → httpx.AsyncClient(base_url, auth, verify, timeout=30s)
    │   → yield {"connection_manager": manager}
    │   → finally: manager.disconnect()
    ↓ register_tools(mcp) → imports + calls register() on all 17 tool modules
```

**Request flow**: Tool function → `get_manager(ctx)` → `manager.get/put/patch/delete("path")` → httpx → `/rest/<path>` on RouterOS

**REST API mapping**:
- GET = read, PUT = create, PATCH = update, DELETE = remove, POST = special ops
- Path pattern: `ip/address`, `ip/route`, `ip/firewall/filter`, etc.
- 404 → returns `None`, 204 → returns `{}`

## CONVENTIONS

- **Tool naming**: `mikrotik_<verb>_<domain>` — verbs: list, get, create/add, update, remove, enable, disable, move
- **Tool annotations**: Always one of `READ`, `WRITE`, or `DESTRUCTIVE` from `app.py`
- **Context param**: Always last: `ctx: Context = CurrentContext()`
- **Validation**: Pydantic BaseModel per Create/Update operation, `model_dump(exclude_none=True)`
- **Not found**: Raise `ValueError(f"... not found: {id}")` — NOT custom exceptions
- **Enable/disable**: PATCH with `{"disabled": "true"/"false"}` (string, not bool)
- **Filtering**: Client-side `_filter_rows()` helpers, not query params (RouterOS REST doesn't support them)
- **Payload translation**: Snake_case Python → kebab-case RouterOS in firewall/logging modules via `_translate()`
- **Return shapes**: Reads return raw dict/list. Mutations return `{"<verb>ed": True, "id": ...}`
- **Imports**: `from ..app import DESTRUCTIVE, READ, WRITE` + `from . import get_manager`

## ANTI-PATTERNS (THIS PROJECT)

- **No `as any` / type suppression** — Pydantic handles validation
- **No direct httpx usage in tools** — Always go through `MikrotikConnectionManager`
- **No cross-domain imports between tool modules** — Each module is self-contained
- **No global state** — Connection manager lives in lifespan context only
- **Booleans to RouterOS**: Must be string `"true"`/`"false"`, never Python `True`/`False`
- **Never use custom exceptions in tools** — `ValueError` for not-found, `ConnectionError` for HTTP failures (handled in connection.py)
- **Never send `model_dump()` without `exclude_none=True`** — Sends None values to RouterOS

## COMMANDS

```bash
# Dev environment
nix develop                                 # Enter flake dev env (Python 3.12 + uv + ruff)
nix-shell                                   # Compat shim for non-flake users

# Run server
mikrotik-rest-mcp                                          # stdio (default, after install)
python -m mikrotik_rest_mcp.server                         # stdio (from source)
MIKROTIK__MCP__TRANSPORT=sse mikrotik-rest-mcp             # SSE transport
MIKROTIK__MCP__TRANSPORT=streamable-http mikrotik-rest-mcp # HTTP streaming

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uvx mikrotik-rest-mcp

# Testing
pytest                                      # Run all 64 tests
pytest tests/test_config.py                 # Run specific module
pytest -x                                   # Stop on first failure
pytest --cov=mikrotik_rest_mcp              # With coverage

# Linting & Type Checking
ruff check src/ tests/                      # Lint (E, F, I, UP, B, SIM rules)
ruff format src/ tests/                     # Auto-format
mypy src/                                   # Type check (strict mode)

# Required env vars
export MIKROTIK_HOST=192.168.88.1
export MIKROTIK_USERNAME=admin
export MIKROTIK_PASSWORD=yourpassword
```

## TESTING PATTERNS

- **Framework**: pytest + pytest-asyncio (auto mode)
- **Fixtures** (`conftest.py`): `mock_settings`, `mock_httpx_client`, `mock_connection_manager`, `mock_context`, `sample_ip_address(es)`, `sample_firewall_rule(s)`
- **Mock pattern**: `mock_context.lifespan_context["connection_manager"]` → AsyncMock with pre-configured `.get`, `.put`, `.patch`, `.delete`
- **Test structure mirrors source**: `tests/test_<module>.py` for core, `tests/test_tools/test_<domain>.py` for tools
- **Coverage**: 64 tests. Core modules (config, connection, exceptions) have tests. Only 2 of 17 tool modules have tests (ip_address, firewall_filter)

## NOTES

- **Test coverage gap**: 15 of 17 tool modules lack tests (dhcp_*, dns*, interface_*, ip_pool, ip_route, system_*, firewall_nat, firewall_address_list)
- **No CI/CD**: No GitHub Actions, Makefile, or pre-commit hooks
- **Port mismatch**: `.env.example` shows port 8728 (old API) but code defaults to 80 (REST API)
- **Unused env var**: `.env.example` has `MIKROTIK_SSL_VERIFY_HOSTNAME` but config.py doesn't define it
- **Config caching**: `get_settings()` uses `@lru_cache(maxsize=1)` — singleton per process
- **Nix Python version**: `flake.nix` uses Python 3.12, `pyproject.toml` targets >=3.11
