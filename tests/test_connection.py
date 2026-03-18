"""Tests for MikrotikConnectionManager HTTP operations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from mikrotik_rest_mcp.config import MikrotikConfig
from mikrotik_rest_mcp.connection import MikrotikConnectionManager
from mikrotik_rest_mcp.exceptions import ConnectionError


class TestMikrotikConnectionManager:
    """Tests for MikrotikConnectionManager."""

    def test_init(self, mock_settings: MikrotikConfig) -> None:
        manager = MikrotikConnectionManager(mock_settings)
        assert manager._config == mock_settings
        assert manager._client is None

    @pytest.mark.asyncio
    async def test_connect_creates_client(self, mock_settings: MikrotikConfig) -> None:
        manager = MikrotikConnectionManager(mock_settings)
        assert manager._client is None

        await manager.connect()

        assert manager._client is not None
        assert isinstance(manager._client, httpx.AsyncClient)

        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, mock_settings: MikrotikConfig) -> None:
        manager = MikrotikConnectionManager(mock_settings)

        await manager.connect()
        first_client = manager._client

        await manager.connect()

        assert manager._client is first_client

        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_closes_client(
        self, mock_settings: MikrotikConfig
    ) -> None:
        manager = MikrotikConnectionManager(mock_settings)

        await manager.connect()
        assert manager._client is not None

        await manager.disconnect()

        assert manager._client is None

    @pytest.mark.asyncio
    async def test_disconnect_idempotent(self, mock_settings: MikrotikConfig) -> None:
        manager = MikrotikConnectionManager(mock_settings)

        await manager.connect()
        await manager.disconnect()

        await manager.disconnect()

        assert manager._client is None

    @pytest.mark.asyncio
    async def test_get_returns_json(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b'[{"id": "1", "name": "test"}]'
        mock_response.json.return_value = [{"id": "1", "name": "test"}]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request.return_value = mock_response

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.get("ip/address")

        assert result == [{"id": "1", "name": "test"}]
        mock_httpx_client.request.assert_called_once_with("GET", "/rest/ip/address")

    @pytest.mark.asyncio
    async def test_get_returns_none_on_404(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = httpx.Response(404)
        mock_response._content = b'{"error": "not found"}'
        mock_httpx_client.request.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("GET", "http://test"),
            response=mock_response,
        )

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.get("ip/address/999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_empty_on_204(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request.return_value = mock_response

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.get("ip/address")

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_raises_connection_error_on_500(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = httpx.Response(500, text="Internal Server Error")
        mock_httpx_client.request.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "http://test"),
            response=mock_response,
        )

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        with pytest.raises(ConnectionError) as exc_info:
            await manager.get("ip/address")

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_put_returns_created(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.content = b'{".id": "*1", "name": "created"}'
        mock_response.json.return_value = {".id": "*1", "name": "created"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request.return_value = mock_response

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.put("ip/address", json={"address": "192.168.1.1/24"})

        assert result == {".id": "*1", "name": "created"}
        mock_httpx_client.request.assert_called_once_with(
            "PUT", "/rest/ip/address", json={"address": "192.168.1.1/24"}
        )

    @pytest.mark.asyncio
    async def test_patch_returns_empty(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"{}"
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request.return_value = mock_response

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.patch("ip/address/*1", json={"disabled": "true"})

        assert result == {}
        mock_httpx_client.request.assert_called_once_with(
            "PATCH", "/rest/ip/address/*1", json={"disabled": "true"}
        )

    @pytest.mark.asyncio
    async def test_delete_returns_empty(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.request.return_value = mock_response

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        result = await manager.delete("ip/address/*1")

        assert result == {}
        mock_httpx_client.request.assert_called_once_with(
            "DELETE", "/rest/ip/address/*1"
        )

    @pytest.mark.asyncio
    async def test_request_raises_on_network_error(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        mock_httpx_client.request.side_effect = httpx.RequestError("Network error")

        manager = MikrotikConnectionManager(mock_settings)
        manager._client = mock_httpx_client

        with pytest.raises(ConnectionError) as exc_info:
            await manager.request("GET", "ip/address")

        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ensure_connects_if_needed(
        self, mock_settings: MikrotikConfig, mock_httpx_client: AsyncMock
    ) -> None:
        manager = MikrotikConnectionManager(mock_settings)

        manager2 = MikrotikConnectionManager(mock_settings)
        await manager2.connect()
        manager2._client = mock_httpx_client

        await manager2.get("ip/address")

        mock_httpx_client.request.assert_called_once()


class TestConnectionManagerAuth:
    """Tests for authentication in connection manager."""

    @pytest.mark.asyncio
    async def test_client_has_auth(self, mock_settings: MikrotikConfig) -> None:
        manager = MikrotikConnectionManager(mock_settings)

        await manager.connect()

        assert manager._client is not None
        assert manager._client._auth is not None

        await manager.disconnect()
