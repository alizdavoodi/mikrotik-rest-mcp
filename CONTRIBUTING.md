# Contributing to MikroTik MCP Server

Thanks for your interest in contributing.

## Development Setup

### Using uv (recommended)

```bash
uv sync --dev
```

### Using Nix

```bash
nix develop
```

## Running Tests

```bash
# With uv
pytest

# With Nix
nix develop -c pytest
```

## Code Quality

Before submitting a PR, ensure all checks pass:

```bash
# Linting
nix develop -c ruff check src/ tests/

# Type checking
nix develop -c mypy src/
```

Auto-fix lint issues:

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Adding a New Tool Module

To add support for a new RouterOS domain:

1. Create `src/mikrotik_rest_mcp/tools/<domain>.py` with a `register(mcp: FastMCP)` function
2. Import and register it in `src/mikrotik_rest_mcp/tools/__init__.py`
3. Add tests in `tests/test_tools/test_<domain>.py`

See existing modules like `ip_address.py` or `firewall_filter.py` for patterns. Key conventions:

- Use `READ` annotation for list/get operations, `WRITE` for creates/updates, `DESTRUCTIVE` for deletes
- Define Pydantic models for Create/Update payloads
- Always use `model_dump(exclude_none=True)` when sending to the API
- Raise `ValueError` for "not found" errors
- Place `ctx: Context = CurrentContext()` as the last parameter

## Pull Request Guidelines

- All tests must pass
- Code must be lint-clean (`ruff check`)
- Type checking must pass (`mypy src/`)
- Add tests for new functionality
- Update documentation if user-facing behavior changes

## Questions?

Open an issue on GitHub for discussion before large changes.
