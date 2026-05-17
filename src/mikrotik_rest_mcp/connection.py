from __future__ import annotations

from typing import Any

import httpx

from .config import MikrotikConfig
from .exceptions import MikrotikConnectionError, MikrotikNotFound


class MikrotikConnectionManager:
    """Manages HTTP connection to MikroTik REST API."""

    def __init__(self, config: MikrotikConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            auth=(self._config.username, self._config.password),
            verify=self._config.ssl_verify,
            timeout=30.0,
        )

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        await self._ensure_connected()

        client = self._client
        assert client is not None

        url = f"/rest/{path}"

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise MikrotikConnectionError(
                f"HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise MikrotikConnectionError(f"Request failed: {exc}") from exc

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def get_list(self, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        """GET a RouterOS submenu collection. Always returns a list."""
        result = await self.request("GET", path, **kwargs)
        if result is None:
            return []
        if not isinstance(result, list):
            raise MikrotikConnectionError(
                f"Expected list from {path}, got {type(result).__name__}"
            )
        return [row for row in result if isinstance(row, dict)]

    async def get_one(
        self, path: str, identifier: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """GET a single RouterOS record. Raises MikrotikNotFound on 404."""
        full = path if identifier is None else f"{path}/{identifier}"
        result = await self.request("GET", full, **kwargs)
        if not isinstance(result, dict):
            raise MikrotikNotFound(path, identifier)
        return result

    async def put(self, path: str, **kwargs: Any) -> Any:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> Any:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    async def _ensure_connected(self) -> None:
        if self._client is None:
            await self.connect()
