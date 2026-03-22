from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.dns_static import (
    DnsStaticCreate,
    DnsStaticUpdate,
    register,
)


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


class TestDnsStaticCreate:
    def test_model_dump_excludes_optional_none(self) -> None:
        model = DnsStaticCreate(name="router.local")
        data = model.model_dump(exclude_none=True)

        assert data == {"name": "router.local", "disabled": False}

    def test_model_dump_includes_optional_when_set(self) -> None:
        model = DnsStaticCreate(
            name="printer.local",
            address="192.168.88.20",
            ttl="1h",
            comment="office printer",
            disabled=True,
            regexp="",
        )
        data = model.model_dump(exclude_none=True)

        assert data["address"] == "192.168.88.20"
        assert data["ttl"] == "1h"
        assert data["comment"] == "office printer"
        assert data["disabled"] is True
        assert data["regexp"] == ""

    def test_name_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            DnsStaticCreate(name="")


class TestDnsStaticUpdate:
    def test_all_fields_optional(self) -> None:
        model = DnsStaticUpdate()
        data = model.model_dump(exclude_none=True)
        assert data == {}

    def test_partial_update_dump(self) -> None:
        model = DnsStaticUpdate(address="10.0.0.10", disabled=False)
        data = model.model_dump(exclude_none=True)

        assert data == {"address": "10.0.0.10", "disabled": False}


class TestDnsStaticTools:
    @pytest.mark.asyncio
    async def test_list_dns_static_applies_filters(self, mock_context: object) -> None:
        tools = _registered_tools()
        list_dns_static = tools["mikrotik_list_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {
                ".id": "*1",
                "name": "host1.local",
                "address": "192.168.88.11",
                "type": "A",
                "disabled": "false",
                "regexp": "",
            },
            {
                ".id": "*2",
                "name": "host2.local",
                "address": "192.168.88.12",
                "type": "A",
                "disabled": "true",
                "regexp": "^api.*",
            },
        ]

        result = await list_dns_static(
            name_filter="host2",
            address_filter="192.168.88.12",
            type_filter="A",
            disabled_only=True,
            regexp_only=True,
            ctx=mock_context,
        )

        assert result == [
            {
                ".id": "*2",
                "name": "host2.local",
                "address": "192.168.88.12",
                "type": "A",
                "disabled": "true",
                "regexp": "^api.*",
            }
        ]
        manager.get.assert_awaited_once_with("ip/dns/static")

    @pytest.mark.asyncio
    async def test_get_dns_static_success(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dns_static = tools["mikrotik_get_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = {".id": "*4", "name": "router.local"}

        result = await get_dns_static("*4", ctx=mock_context)

        assert result == {".id": "*4", "name": "router.local"}
        manager.get.assert_awaited_once_with("ip/dns/static/*4")

    @pytest.mark.asyncio
    async def test_get_dns_static_not_found_raises(self, mock_context: object) -> None:
        tools = _registered_tools()
        get_dns_static = tools["mikrotik_get_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = None

        with pytest.raises(ValueError, match="DNS static entry not found: \*404"):
            await get_dns_static("*404", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_create_dns_static_converts_disabled_to_string(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        create_dns_static = tools["mikrotik_create_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*20"}

        result = await create_dns_static(
            name="camera.local",
            address="192.168.88.30",
            disabled=True,
            ctx=mock_context,
        )

        assert result == {"created": True, "id": "*20"}
        manager.put.assert_awaited_once_with(
            "ip/dns/static",
            json={
                "name": "camera.local",
                "address": "192.168.88.30",
                "disabled": "true",
            },
        )

    @pytest.mark.asyncio
    async def test_update_dns_static_requires_fields(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        update_dns_static = tools["mikrotik_update_dns_static"]

        with pytest.raises(
            ValueError, match="At least one update field must be provided"
        ):
            await update_dns_static("*1", ctx=mock_context)

    @pytest.mark.asyncio
    async def test_update_dns_static_converts_disabled_to_string(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        update_dns_static = tools["mikrotik_update_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await update_dns_static(
            "*5", address="10.0.0.5", disabled=False, ctx=mock_context
        )

        assert result == {"updated": True, "id": "*5"}
        manager.patch.assert_awaited_once_with(
            "ip/dns/static/*5",
            json={"address": "10.0.0.5", "disabled": "false"},
        )

    @pytest.mark.asyncio
    async def test_remove_dns_static_calls_delete(self, mock_context: object) -> None:
        tools = _registered_tools()
        remove_dns_static = tools["mikrotik_remove_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await remove_dns_static("*6", ctx=mock_context)

        assert result == {"removed": True, "id": "*6"}
        manager.delete.assert_awaited_once_with("ip/dns/static/*6")

    @pytest.mark.asyncio
    async def test_enable_dns_static_calls_patch(self, mock_context: object) -> None:
        tools = _registered_tools()
        enable_dns_static = tools["mikrotik_enable_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await enable_dns_static("*7", ctx=mock_context)

        assert result == {"enabled": True, "id": "*7"}
        manager.patch.assert_awaited_once_with(
            "ip/dns/static/*7", json={"disabled": "false"}
        )

    @pytest.mark.asyncio
    async def test_disable_dns_static_calls_patch(self, mock_context: object) -> None:
        tools = _registered_tools()
        disable_dns_static = tools["mikrotik_disable_dns_static"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await disable_dns_static("*8", ctx=mock_context)

        assert result == {"disabled": True, "id": "*8"}
        manager.patch.assert_awaited_once_with(
            "ip/dns/static/*8", json={"disabled": "true"}
        )
