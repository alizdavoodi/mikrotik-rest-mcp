from __future__ import annotations

import pytest

from mikrotik_rest_mcp.tools.dhcp_pool import DhcpPoolCreate, register


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


class TestDhcpPoolCreate:
    def test_model_dump_excludes_optional_none(self) -> None:
        model = DhcpPoolCreate(name="pool1", ranges="192.168.88.10-192.168.88.200")
        data = model.model_dump(exclude_none=True)

        assert data == {"name": "pool1", "ranges": "192.168.88.10-192.168.88.200"}

    def test_model_dump_includes_optional_fields_when_set(self) -> None:
        model = DhcpPoolCreate(
            name="pool2",
            ranges="10.0.0.10-10.0.0.100",
            next_pool="pool3",
            comment="fallback",
        )
        data = model.model_dump(exclude_none=True)

        assert data["next_pool"] == "pool3"
        assert data["comment"] == "fallback"


class TestDhcpPoolTools:
    @pytest.mark.asyncio
    async def test_list_dhcp_pools_filters_and_include_used(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        list_dhcp_pools = tools["mikrotik_list_dhcp_pools"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.side_effect = [
            [
                {"name": "pool-main", "ranges": "192.168.88.10-192.168.88.200"},
                {"name": "pool-guest", "ranges": "10.10.10.10-10.10.10.200"},
            ],
            [
                {"pool": "pool-main", "address": "192.168.88.50"},
                {"pool": "pool-main", "address": "192.168.88.51"},
            ],
        ]

        result = await list_dhcp_pools(
            name_filter="main",
            ranges_filter="192.168.88",
            include_used=True,
            ctx=mock_context,
        )

        assert result == [
            {
                "name": "pool-main",
                "ranges": "192.168.88.10-192.168.88.200",
                "used_entries": [
                    {"pool": "pool-main", "address": "192.168.88.50"},
                    {"pool": "pool-main", "address": "192.168.88.51"},
                ],
            }
        ]
        assert manager.get.await_count == 2

    @pytest.mark.asyncio
    async def test_get_dhcp_pool_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_pool = tools["mikrotik_get_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*4", "name": "pool-main"}, "junk"]

        result = await get_dhcp_pool("pool-main", ctx=mock_context)

        assert result == {".id": "*4", "name": "pool-main"}
        manager.get.assert_awaited_once_with("ip/pool", params={"name": "pool-main"})

    @pytest.mark.asyncio
    async def test_get_dhcp_pool_not_found_raises(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dhcp_pool = tools["mikrotik_get_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="DHCP pool not found: missing"):
            await get_dhcp_pool("missing", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_create_dhcp_pool_maps_next_pool(self, mock_context: object) -> None:
        tools = _registered_tools()
        create_dhcp_pool = tools["mikrotik_create_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*8"}

        result = await create_dhcp_pool(
            name="pool-new",
            ranges="192.168.90.10-192.168.90.200",
            next_pool="pool-fallback",
            comment="new",
            ctx=mock_context,
        )

        assert result == {"created": True, "id": "*8"}
        manager.put.assert_awaited_once_with(
            "ip/pool",
            json={
                "name": "pool-new",
                "ranges": "192.168.90.10-192.168.90.200",
                "comment": "new",
                "next-pool": "pool-fallback",
            },
        )

    @pytest.mark.asyncio
    async def test_remove_dhcp_pool_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        remove_dhcp_pool = tools["mikrotik_remove_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*11", "name": "pool-old"}]

        result = await remove_dhcp_pool("pool-old", ctx=mock_context)

        assert result == {"removed": True, "id": "*11"}
        manager.get.assert_awaited_once_with("ip/pool", params={"name": "pool-old"})
        manager.delete.assert_awaited_once_with("ip/pool/*11")

    @pytest.mark.asyncio
    async def test_remove_dhcp_pool_not_found_raises(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        remove_dhcp_pool = tools["mikrotik_remove_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="DHCP pool not found: pool404"):
            await remove_dhcp_pool("pool404", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_update_dhcp_pool_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        update_dhcp_pool = tools["mikrotik_update_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*15", "name": "pool-main"}]

        result = await update_dhcp_pool(
            "pool-main",
            new_name="pool-main-new",
            ranges="192.168.99.10-192.168.99.200",
            next_pool="pool-next",
            comment="updated",
            ctx=mock_context,
        )

        assert result == {"updated": True, "id": "*15"}
        manager.patch.assert_awaited_once_with(
            "ip/pool/*15",
            json={
                "name": "pool-main-new",
                "ranges": "192.168.99.10-192.168.99.200",
                "next-pool": "pool-next",
                "comment": "updated",
            },
        )

    @pytest.mark.asyncio
    async def test_update_dhcp_pool_not_found_raises(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        update_dhcp_pool = tools["mikrotik_update_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="DHCP pool not found: pool404"):
            await update_dhcp_pool("pool404", new_name="x", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_update_dhcp_pool_requires_at_least_one_field(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        update_dhcp_pool = tools["mikrotik_update_dhcp_pool"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{".id": "*16", "name": "pool-main"}]

        with pytest.raises(
            ValueError, match="At least one update field must be provided"
        ):
            await update_dhcp_pool("pool-main", ctx=mock_context)
