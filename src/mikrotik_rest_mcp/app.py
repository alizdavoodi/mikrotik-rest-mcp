from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .annotations import DESTRUCTIVE, READ, WRITE
from .config import get_settings
from .connection import MikrotikConnectionManager
from .tools import register_tools

__all__ = ["DESTRUCTIVE", "READ", "WRITE", "mcp"]


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
