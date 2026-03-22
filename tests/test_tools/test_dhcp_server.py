from __future__ import annotations

import pytest

from mikrotik_rest_mcp.tools.dhcp_server import DhcpServerCreate, register


class _MockMCP:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str, annotations: dict[str, object]) -> object:
        del annotations

        def decorator(func: object) -> object:
            self.tools[name] = func
            return func

        return decorator


def _registered_tools() -> dict[str, object]:
    mcp = _MockMCP()
    register(mcp)  # type: ignore[arg-type]
    return mcp.tools


class TestDhcpServerCreate:
    def test_minimal_payload_defaults(self) -> None:
        model = DhcpServerCreate(name="srv1", interface="bridge")
        data = model.model_dump(exclude_none=True)

        assert data["name"] == "srv1"
        assert data["interface"] == "bridge"
        assert data["lease_time"] == "1d"
        assert data["disabled"] is False
        assert data["authoritative"] == "yes"
        assert "address_pool" not in data
        assert "delay_threshold" not in data
        assert "comment" not in data

    def test_full_payload_includes_optional_fields(self) -> None:
        model = DhcpServerCreate(
            name="srv2",
            interface="ether1",
            lease_time="2h",
            address_pool="pool1",
            disabled=True,
            authoritative="after-2sec-delay",
            delay_threshold="2s",
            comment="test",
        )
        data = model.model_dump(exclude_none=True)

        assert data["lease_time"] == "2h"
        assert data["address_pool"] == "pool1"
        assert data["disabled"] is True
        assert data["authoritative"] == "after-2sec-delay"
        assert data["delay_threshold"] == "2s"
        assert data["comment"] == "test"


class TestDhcpServerTools:
    @pytest.mark.asyncio
    async def test_list_dhcp_servers_applies_filters(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        list_dhcp_servers = tools["mikrotik_list_dhcp_servers"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {
                "name": "srv1",
                "interface": "bridge",
                "disabled": "false",
                "invalid": "false",
            },
            {
                "name": "srv2",
                "interface": "ether1",
                "disabled": "true",
                "invalid": "true",
            },
        ]

        result = await list_dhcp_servers(
            name_filter="srv",
            interface_filter="ether1",
            disabled_only=True,
            invalid_only=True,
            ctx=mock_context,
        )

        assert result == [
            {
                "name": "srv2",
                "interface": "ether1",
                "disabled": "true",
                "invalid": "true",
            }
        ]
        manager.get.assert_awaited_once_with("ip/dhcp-server")

    @pytest.mark.asyncio
    async def test_get_dhcp_server_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_server = tools["mikrotik_get_dhcp_server"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*1", "name": "srv1"}, "junk"]

        result = await get_dhcp_server("srv1", ctx=mock_context)

        assert result == {".id": "*1", "name": "srv1"}
        manager.get.assert_awaited_once_with("ip/dhcp-server", params={"name": "srv1"})

    @pytest.mark.asyncio
    async def test_get_dhcp_server_not_found_raises(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_server = tools["mikrotik_get_dhcp_server"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="DHCP server not found: missing"):
            await get_dhcp_server("missing", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_create_dhcp_server_maps_payload_fields(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        create_dhcp_server = tools["mikrotik_create_dhcp_server"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*9"}

        result = await create_dhcp_server(
            name="srv3",
            interface="bridge",
            lease_time="12h",
            address_pool="pool-main",
            disabled=True,
            authoritative="yes",
            delay_threshold="1s",
            comment="created",
            ctx=mock_context,
        )

        assert result == {"created": True, "id": "*9"}
        manager.put.assert_awaited_once_with(
            "ip/dhcp-server",
            json={
                "name": "srv3",
                "interface": "bridge",
                "disabled": True,
                "authoritative": "yes",
                "comment": "created",
                "lease-time": "12h",
                "address-pool": "pool-main",
                "delay-threshold": "1s",
            },
        )

    @pytest.mark.asyncio
    async def test_remove_dhcp_server_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        remove_dhcp_server = tools["mikrotik_remove_dhcp_server"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*3", "name": "srv3"}]

        result = await remove_dhcp_server("srv3", ctx=mock_context)

        assert result == {"removed": True, "id": "*3"}
        manager.get.assert_awaited_once_with("ip/dhcp-server", params={"name": "srv3"})
        manager.delete.assert_awaited_once_with("ip/dhcp-server/*3")

    @pytest.mark.asyncio
    async def test_remove_dhcp_server_not_found_raises(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        remove_dhcp_server = tools["mikrotik_remove_dhcp_server"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="DHCP server not found: srv404"):
            await remove_dhcp_server("srv404", ctx=mock_context)
