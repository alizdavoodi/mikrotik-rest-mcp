import sys

from pydantic import ValidationError

from .app import mcp
from .config import get_settings


def main() -> None:
    try:
        settings = get_settings()
    except ValidationError as exc:
        missing_fields = sorted(
            {
                str(err["loc"][0])
                for err in exc.errors()
                if err.get("type") == "missing" and err.get("loc")
            }
        )
        env_map = {
            "host": "MIKROTIK_HOST",
            "password": "MIKROTIK_PASSWORD",
        }
        missing_env_vars = [
            env_map[field] for field in missing_fields if field in env_map
        ]

        message = "MikroTik MCP configuration error."
        if missing_env_vars:
            required = ", ".join(missing_env_vars)
            message = f"{message} Missing required environment variables: {required}."
        message = (
            f"{message} Set them in your shell environment or MCP server env config."
        )
        print(message, file=sys.stderr)
        raise SystemExit(1) from None

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
