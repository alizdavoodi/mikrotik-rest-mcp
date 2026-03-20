from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .config import get_settings
from .connection import MikrotikConnectionManager
from .tools import register_tools

READ: dict[str, Any] = {"readOnlyHint": True, "destructiveHint": False}
WRITE: dict[str, Any] = {"readOnlyHint": False, "destructiveHint": False}
DESTRUCTIVE: dict[str, Any] = {"readOnlyHint": False, "destructiveHint": True}


@asynccontextmanager
async def lifespan(_: FastMCP) -> AsyncIterator[dict[str, Any]]:
    settings = get_settings()
    manager = MikrotikConnectionManager(settings)
    await manager.connect()
    try:
        yield {"connection_manager": manager}
    finally:
        await manager.disconnect()


mcp = FastMCP("mikrotik-rest-mcp", lifespan=lifespan)

register_tools(mcp)
