from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpServerSettings(BaseModel):
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)


class MikrotikConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MIKROTIK_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    host: str
    username: str = "admin"
    password: str
    port: int = Field(default=80, ge=1, le=65535)
    use_ssl: bool = False
    ssl_verify: bool = False
    mcp: McpServerSettings = McpServerSettings()

    @property
    def base_url(self) -> str:
        """Build base URL from config."""
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}"


@lru_cache(maxsize=1)
def get_settings() -> MikrotikConfig:
    return MikrotikConfig()
