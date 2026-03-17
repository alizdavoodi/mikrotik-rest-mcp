from .app import mcp
from .config import get_settings


def main() -> None:
    settings = get_settings()
    transport = settings.mcp.transport
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    mcp.run(
        transport=transport,
        host=settings.mcp.host,
        port=settings.mcp.port,
    )


if __name__ == "__main__":
    main()
