"""Tests for the RouterOS submenu deep module.

These tests cover the synthesis layer — predicates, schemas, lookup-key
resolution, and the synthesized list/get/create/update/remove/enable/disable
/move tools — using one representative schema each.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import Field, ValidationError

from mikrotik_rest_mcp.connection import MikrotikConnectionManager
from mikrotik_rest_mcp.exceptions import MikrotikNotFound
from mikrotik_rest_mcp.submenu import (
    Equals,
    RouterOSSchema,
    Submenu,
    Substring,
    SubstringAny,
    TrueFlag,
    Truthy,
    build_submenu_tools,
)

# ---- Fixtures -------------------------------------------------------------


def _ctx_with_manager() -> tuple[MagicMock, AsyncMock]:
    """Build a (ctx, manager) pair with manager honoring isinstance check."""
    manager = AsyncMock(spec=MikrotikConnectionManager)
    manager.get_list = AsyncMock(return_value=[])
    manager.get_one = AsyncMock()
    manager.put = AsyncMock(return_value={".id": "*1"})
    manager.patch = AsyncMock(return_value={})
    manager.delete = AsyncMock(return_value={})
    ctx = MagicMock()
    ctx.lifespan_context = {"connection_manager": manager}
    return ctx, manager


# ---- Schemas + submenus used across these tests --------------------------


class _Filter(RouterOSSchema):
    chain: str
    action: str
    src_address: str | None = Field(default=None, alias="src-address")
    in_interface: str | None = Field(default=None, alias="in-interface")
    comment: str | None = None
    disabled: bool = False
    log: bool = False
    place_before: str | None = Field(default=None, alias="place-before")


class _Named(RouterOSSchema):
    name: str = Field(min_length=1)
    ranges: str = Field(min_length=3)
    next_pool: str | None = Field(default=None, alias="next-pool")
    comment: str | None = None


FILTER_SUBMENU = Submenu(
    path="ip/firewall/filter",
    schema=_Filter,
    id_param="rule_id",
    singular="filter rule",
    plural="filter rules",
    create_only_fields=("place_before",),
    tool_names={
        "list": "list_filters",
        "get": "get_filter",
        "create": "create_filter",
        "update": "update_filter",
        "remove": "remove_filter",
        "enable": "enable_filter",
        "disable": "disable_filter",
        "move": "move_filter",
    },
    list_filters=(
        Equals("chain_filter", "chain"),
        Substring("src_address_filter", "src-address"),
        SubstringAny("interface_filter", ("in-interface", "out-interface")),
        TrueFlag("disabled_only", "disabled"),
    ),
)


NAMED_SUBMENU = Submenu(
    path="ip/pool",
    schema=_Named,
    id_param="name",
    singular="IP pool",
    plural="IP pools",
    lookup_key="name",
    update_name_field="name",
    tool_names={
        "list": "list_pools",
        "get": "get_pool",
        "create": "create_pool",
        "update": "update_pool",
        "remove": "remove_pool",
    },
    list_filters=(Substring("name_filter", "name"),),
)


# ---- Predicate unit tests -------------------------------------------------


class TestPredicates:
    def test_substring_matches(self) -> None:
        p = Substring("addr", "address")
        assert p.matches({"address": "10.0.0.1/24"}, "10.0")
        assert not p.matches({"address": "192.168.1.1"}, "10.0")
        assert not p.matches({}, "10.0")

    def test_substring_any_matches_any_field(self) -> None:
        p = SubstringAny("iface", ("in-interface", "out-interface"))
        assert p.matches({"in-interface": "ether1"}, "ether1")
        assert p.matches({"out-interface": "ether1"}, "ether1")
        assert not p.matches({"in-interface": "ether2", "out-interface": "ether3"}, "x")

    def test_equals_str(self) -> None:
        p = Equals("chain", "chain")
        assert p.matches({"chain": "input"}, "input")
        assert not p.matches({"chain": "forward"}, "input")

    def test_equals_int_via_string_coercion(self) -> None:
        p = Equals("vlan", "vlan-id")
        assert p.matches({"vlan-id": "100"}, 100)
        assert not p.matches({"vlan-id": "200"}, 100)

    def test_true_flag_only_matches_string_true(self) -> None:
        p = TrueFlag("only", "disabled")
        assert p.matches({"disabled": "true"}, True)
        assert not p.matches({"disabled": "false"}, True)
        assert not p.matches({}, True)

    def test_truthy_matches_any_nonempty(self) -> None:
        p = Truthy("has", "regexp")
        assert p.matches({"regexp": "abc"}, True)
        assert not p.matches({"regexp": ""}, True)
        assert not p.matches({}, True)


# ---- Schema serialization -------------------------------------------------


class TestSchemaSerialization:
    def test_aliases_applied_on_dump(self) -> None:
        m = _Filter(
            chain="input",
            action="accept",
            src_address="10.0.0.0/24",
            in_interface="ether1",
        )
        wire = m.to_router_os()
        assert wire["src-address"] == "10.0.0.0/24"
        assert wire["in-interface"] == "ether1"
        assert "src_address" not in wire

    def test_bools_serialized_as_strings(self) -> None:
        m = _Filter(chain="input", action="accept", disabled=True, log=False)
        wire = m.to_router_os()
        assert wire["disabled"] == "true"
        assert wire["log"] == "false"

    def test_none_fields_excluded(self) -> None:
        m = _Filter(chain="input", action="accept")
        wire = m.to_router_os()
        assert "src-address" not in wire
        assert "comment" not in wire

    def test_required_field_missing_raises(self) -> None:
        with pytest.raises(ValidationError):
            _Filter(action="accept")  # missing chain


# ---- List tool ------------------------------------------------------------


class TestListTool:
    @pytest.mark.asyncio
    async def test_returns_all_rows_when_no_filters_set(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [{"chain": "input"}, {"chain": "forward"}]

        result = await list_fn(ctx=ctx)

        assert len(result) == 2
        manager.get_list.assert_awaited_once_with("ip/firewall/filter")

    @pytest.mark.asyncio
    async def test_equals_filter_applied(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {"chain": "input"},
            {"chain": "forward"},
            {"chain": "output"},
        ]

        result = await list_fn(chain_filter="input", ctx=ctx)

        assert result == [{"chain": "input"}]

    @pytest.mark.asyncio
    async def test_substring_filter_applied(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {"chain": "input", "src-address": "10.0.0.1"},
            {"chain": "input", "src-address": "192.168.1.1"},
        ]

        result = await list_fn(src_address_filter="10.0", ctx=ctx)

        assert len(result) == 1
        assert result[0]["src-address"] == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_substring_any_filter_applied(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {"in-interface": "ether1"},
            {"out-interface": "ether1"},
            {"in-interface": "ether2", "out-interface": "ether3"},
        ]

        result = await list_fn(interface_filter="ether1", ctx=ctx)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_true_flag_filter_applied(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {"disabled": "true"},
            {"disabled": "false"},
        ]

        result = await list_fn(disabled_only=True, ctx=ctx)

        assert result == [{"disabled": "true"}]

    @pytest.mark.asyncio
    async def test_multiple_filters_combine(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        list_fn, _ = tools["list_filters"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {"chain": "input", "src-address": "10.0.0.1", "disabled": "true"},
            {"chain": "input", "src-address": "10.0.0.1", "disabled": "false"},
            {"chain": "forward", "src-address": "10.0.0.1", "disabled": "true"},
        ]

        result = await list_fn(
            chain_filter="input", src_address_filter="10.0", disabled_only=True, ctx=ctx
        )

        assert len(result) == 1
        assert result[0]["chain"] == "input"
        assert result[0]["disabled"] == "true"


# ---- Get tool -------------------------------------------------------------


class TestGetTool:
    @pytest.mark.asyncio
    async def test_get_by_id_uses_get_one(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        get_fn, _ = tools["get_filter"]
        ctx, manager = _ctx_with_manager()
        manager.get_one.return_value = {".id": "*7", "chain": "input"}

        result = await get_fn(rule_id="*7", ctx=ctx)

        assert result == {".id": "*7", "chain": "input"}
        manager.get_one.assert_awaited_once_with("ip/firewall/filter", "*7")

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        get_fn, _ = tools["get_filter"]
        ctx, manager = _ctx_with_manager()
        manager.get_one.side_effect = MikrotikNotFound("ip/firewall/filter", "*404")

        with pytest.raises(MikrotikNotFound):
            await get_fn(rule_id="*404", ctx=ctx)

    @pytest.mark.asyncio
    async def test_get_by_lookup_key_scans_list(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        get_fn, _ = tools["get_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {".id": "*1", "name": "pool-a"},
            {".id": "*2", "name": "pool-b"},
        ]

        result = await get_fn(name="pool-b", ctx=ctx)

        assert result == {".id": "*2", "name": "pool-b"}

    @pytest.mark.asyncio
    async def test_get_by_lookup_key_raises_when_absent(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        get_fn, _ = tools["get_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [{".id": "*1", "name": "pool-a"}]

        with pytest.raises(MikrotikNotFound):
            await get_fn(name="missing", ctx=ctx)


# ---- Create tool ----------------------------------------------------------


class TestCreateTool:
    @pytest.mark.asyncio
    async def test_create_dumps_payload_with_aliases_and_bool_strings(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        create_fn, _ = tools["create_filter"]
        ctx, manager = _ctx_with_manager()
        manager.put.return_value = {".id": "*5"}

        result = await create_fn(
            chain="input",
            action="accept",
            src_address="10.0.0.0/24",
            in_interface="ether1",
            disabled=True,
            log=False,
            ctx=ctx,
        )

        assert result == {"created": True, "id": "*5"}
        manager.put.assert_awaited_once_with(
            "ip/firewall/filter",
            json={
                "chain": "input",
                "action": "accept",
                "src-address": "10.0.0.0/24",
                "in-interface": "ether1",
                "disabled": "true",
                "log": "false",
            },
        )

    @pytest.mark.asyncio
    async def test_create_includes_create_only_field(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        create_fn, _ = tools["create_filter"]
        ctx, manager = _ctx_with_manager()
        manager.put.return_value = {".id": "*1"}

        await create_fn(
            chain="input", action="accept", place_before="*9", ctx=ctx
        )

        sent = manager.put.call_args.kwargs["json"]
        assert sent["place-before"] == "*9"

    @pytest.mark.asyncio
    async def test_create_returns_none_id_on_empty_put_response(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        create_fn, _ = tools["create_filter"]
        ctx, manager = _ctx_with_manager()
        manager.put.return_value = {}

        result = await create_fn(chain="input", action="accept", ctx=ctx)

        assert result == {"created": True, "id": None}

    @pytest.mark.asyncio
    async def test_create_rejects_missing_required_field(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        create_fn, _ = tools["create_filter"]
        ctx, _ = _ctx_with_manager()

        with pytest.raises(ValidationError):
            await create_fn(chain="input", ctx=ctx)  # missing action


# ---- Update tool ----------------------------------------------------------


class TestUpdateTool:
    @pytest.mark.asyncio
    async def test_update_by_id_patches_only_provided_fields(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        update_fn, _ = tools["update_filter"]
        ctx, manager = _ctx_with_manager()

        result = await update_fn(
            rule_id="*3", src_address="10.1.0.0/24", disabled=False, ctx=ctx
        )

        assert result == {"updated": True, "id": "*3"}
        manager.patch.assert_awaited_once_with(
            "ip/firewall/filter/*3",
            json={"src-address": "10.1.0.0/24", "disabled": "false"},
        )

    @pytest.mark.asyncio
    async def test_update_with_no_fields_raises(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        update_fn, _ = tools["update_filter"]
        ctx, _ = _ctx_with_manager()

        with pytest.raises(ValueError, match="At least one update field"):
            await update_fn(rule_id="*3", ctx=ctx)

    @pytest.mark.asyncio
    async def test_update_excludes_create_only_field(self) -> None:
        """place_before is create-only and must not appear on update sig."""
        import inspect

        tools = build_submenu_tools(FILTER_SUBMENU)
        update_fn, _ = tools["update_filter"]
        sig = inspect.signature(update_fn)
        assert "place_before" not in sig.parameters

    @pytest.mark.asyncio
    async def test_update_via_lookup_key_resolves_id_then_patches(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        update_fn, _ = tools["update_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [
            {".id": "*1", "name": "pool-a"},
            {".id": "*2", "name": "pool-b"},
        ]

        result = await update_fn(
            name="pool-b", ranges="10.0.0.1-10.0.0.99", ctx=ctx
        )

        assert result == {"updated": True, "id": "*2"}
        manager.patch.assert_awaited_once_with(
            "ip/pool/*2", json={"ranges": "10.0.0.1-10.0.0.99"}
        )

    @pytest.mark.asyncio
    async def test_update_rename_via_new_name(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        update_fn, _ = tools["update_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [{".id": "*1", "name": "pool-a"}]

        await update_fn(name="pool-a", new_name="pool-renamed", ctx=ctx)

        manager.patch.assert_awaited_once_with(
            "ip/pool/*1", json={"name": "pool-renamed"}
        )

    @pytest.mark.asyncio
    async def test_update_via_lookup_raises_when_name_missing(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        update_fn, _ = tools["update_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = []

        with pytest.raises(MikrotikNotFound):
            await update_fn(name="ghost", ranges="x", ctx=ctx)


# ---- Remove / enable / disable / move ------------------------------------


class TestSideEffectTools:
    @pytest.mark.asyncio
    async def test_remove_by_id(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        remove_fn, _ = tools["remove_filter"]
        ctx, manager = _ctx_with_manager()

        result = await remove_fn(rule_id="*9", ctx=ctx)

        assert result == {"removed": True, "id": "*9"}
        manager.delete.assert_awaited_once_with("ip/firewall/filter/*9")

    @pytest.mark.asyncio
    async def test_remove_via_lookup_key(self) -> None:
        tools = build_submenu_tools(NAMED_SUBMENU)
        remove_fn, _ = tools["remove_pool"]
        ctx, manager = _ctx_with_manager()
        manager.get_list.return_value = [{".id": "*5", "name": "pool-a"}]

        result = await remove_fn(name="pool-a", ctx=ctx)

        assert result == {"removed": True, "id": "*5"}
        manager.delete.assert_awaited_once_with("ip/pool/*5")

    @pytest.mark.asyncio
    async def test_enable_patches_disabled_false(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        enable_fn, _ = tools["enable_filter"]
        ctx, manager = _ctx_with_manager()

        result = await enable_fn(rule_id="*3", ctx=ctx)

        assert result == {"enabled": True, "id": "*3"}
        manager.patch.assert_awaited_once_with(
            "ip/firewall/filter/*3", json={"disabled": "false"}
        )

    @pytest.mark.asyncio
    async def test_disable_patches_disabled_true(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        disable_fn, _ = tools["disable_filter"]
        ctx, manager = _ctx_with_manager()

        result = await disable_fn(rule_id="*3", ctx=ctx)

        assert result == {"disabled": True, "id": "*3"}
        manager.patch.assert_awaited_once_with(
            "ip/firewall/filter/*3", json={"disabled": "true"}
        )

    @pytest.mark.asyncio
    async def test_move_patches_with_destination(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        move_fn, _ = tools["move_filter"]
        ctx, manager = _ctx_with_manager()

        result = await move_fn(rule_id="*7", destination=2, ctx=ctx)

        assert result == {"moved": True, "id": "*7", "destination": 2}
        manager.patch.assert_awaited_once_with(
            "ip/firewall/filter/*7", json={"move": "2"}
        )


# ---- Operation-set selection ---------------------------------------------


class TestOperationSelection:
    def test_only_declared_operations_produce_tools(self) -> None:
        small = Submenu(
            path="x",
            schema=_Named,
            id_param="name",
            singular="x",
            plural="xs",
            lookup_key="name",
            tool_names={"list": "xlist", "remove": "xremove"},
        )
        tools = build_submenu_tools(small)
        assert set(tools.keys()) == {"xlist", "xremove"}

    def test_all_synthesized_tools_have_correct_names(self) -> None:
        tools = build_submenu_tools(FILTER_SUBMENU)
        for tool_name, (fn, _) in tools.items():
            assert fn.__name__ == tool_name


# ---- All-submenus registration smoke test --------------------------------


class TestAllSubmenusRegister:
    def test_all_descriptors_produce_unique_tools(self) -> None:
        """Every descriptor in SUBMENUS produces a unique set of tool names."""
        from mikrotik_rest_mcp.submenus import SUBMENUS

        seen: set[str] = set()
        for submenu in SUBMENUS:
            for name in submenu.tool_names.values():
                assert name not in seen, f"duplicate tool name: {name}"
                seen.add(name)

    @pytest.mark.asyncio
    async def test_register_tools_attaches_all_130_tools(self) -> None:
        """End-to-end: register_tools registers the full surface on a FastMCP."""
        from fastmcp import FastMCP

        from mikrotik_rest_mcp.tools import register_tools

        mcp = FastMCP("test")
        register_tools(mcp)
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        # All MikroTik-namespaced; preserve exact name convention
        assert all(n.startswith("mikrotik_") for n in names)
        # The submenu refactor preserves 130 tools total.
        assert len(names) == 130

    @pytest.mark.asyncio
    async def test_specific_tool_schema_matches_expected_shape(self) -> None:
        """Snapshot the shape of one synthesized tool's input schema."""
        from fastmcp import FastMCP

        from mikrotik_rest_mcp.tools import register_tools

        mcp = FastMCP("test")
        register_tools(mcp)
        tools = {t.name: t for t in await mcp.list_tools()}

        create_addr = tools["mikrotik_create_ip_address"]
        props: dict[str, Any] = create_addr.parameters["properties"]  # type: ignore[index]
        assert "address" in props
        assert "interface" in props
        assert "disabled" in props
        # required fields enforced at schema level
        assert "address" in create_addr.parameters["required"]  # type: ignore[index]
        assert "interface" in create_addr.parameters["required"]  # type: ignore[index]
