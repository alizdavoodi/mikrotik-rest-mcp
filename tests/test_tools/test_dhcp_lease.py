from __future__ import annotations

import pytest

from mikrotik_rest_mcp.tools.dhcp_lease import DhcpLeaseCreate, register


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


class TestDhcpLeaseCreate:
    def test_model_dump_excludes_none_and_keeps_defaults(self) -> None:
        model = DhcpLeaseCreate(
            address="192.168.88.10", mac_address="AA:BB:CC:DD:EE:FF"
        )
        data = model.model_dump(exclude_none=True)

        assert data == {
            "address": "192.168.88.10",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "disabled": False,
        }

    def test_model_dump_includes_optional_fields_when_set(self) -> None:
        model = DhcpLeaseCreate(
            address="192.168.88.11",
            mac_address="11:22:33:44:55:66",
            server="dhcp1",
            comment="printer",
            disabled=True,
        )
        data = model.model_dump(exclude_none=True)

        assert data["server"] == "dhcp1"
        assert data["comment"] == "printer"
        assert data["disabled"] is True


class TestDhcpLeaseTools:
    @pytest.mark.asyncio
    async def test_list_dhcp_leases_applies_all_filters(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        list_dhcp_leases = tools["mikrotik_list_dhcp_leases"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {
                ".id": "*1",
                "server": "dhcp1",
                "mac-address": "AA:AA:AA:AA:AA:AA",
                "address": "192.168.88.2",
                "status": "bound",
            },
            {
                ".id": "*2",
                "server": "dhcp2",
                "mac-address": "BB:BB:BB:BB:BB:BB",
                "address": "192.168.88.3",
                "status": "offered",
            },
        ]

        result = await list_dhcp_leases(
            server="dhcp1",
            mac_address="AA:AA:AA:AA:AA:AA",
            address="192.168.88.2",
            status="bound",
            ctx=mock_context,
        )

        assert result == [
            {
                ".id": "*1",
                "server": "dhcp1",
                "mac-address": "AA:AA:AA:AA:AA:AA",
                "address": "192.168.88.2",
                "status": "bound",
            }
        ]
        manager.get.assert_awaited_once_with("ip/dhcp-server/lease")

    @pytest.mark.asyncio
    async def test_get_dhcp_lease_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_lease = tools["mikrotik_get_dhcp_lease"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = {".id": "*7", "address": "192.168.88.7"}

        result = await get_dhcp_lease("*7", ctx=mock_context)

        assert result == {".id": "*7", "address": "192.168.88.7"}
        manager.get.assert_awaited_once_with("ip/dhcp-server/lease/*7")

    @pytest.mark.asyncio
    async def test_get_dhcp_lease_not_found_raises(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_lease = tools["mikrotik_get_dhcp_lease"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = None

        with pytest.raises(ValueError, match="DHCP lease not found: \*404"):
            await get_dhcp_lease("*404", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_create_dhcp_lease_maps_mac_address_field(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        create_dhcp_lease = tools["mikrotik_create_dhcp_lease"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*12"}

        result = await create_dhcp_lease(
            address="192.168.88.12",
            mac_address="12:12:12:12:12:12",
            server="dhcp1",
            comment="iot",
            disabled=True,
            ctx=mock_context,
        )

        assert result == {"created": True, "id": "*12"}
        manager.put.assert_awaited_once_with(
            "ip/dhcp-server/lease",
            json={
                "address": "192.168.88.12",
                "server": "dhcp1",
                "comment": "iot",
                "disabled": True,
                "mac-address": "12:12:12:12:12:12",
            },
        )

    @pytest.mark.asyncio
    async def test_remove_dhcp_lease_calls_delete(self, mock_context: object) -> None:
        tools = _registered_tools()
        remove_dhcp_lease = tools["mikrotik_remove_dhcp_lease"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await remove_dhcp_lease("*9", ctx=mock_context)

        assert result == {"removed": True, "id": "*9"}
        manager.delete.assert_awaited_once_with("ip/dhcp-server/lease/*9")
