"""Tests for bespoke (non-CRUD) tool modules.

These tools don't fit the Submenu shape (singletons, workflows, multi-source
filters), so they stay in their original ``tools/*.py`` modules. This file
covers their behavior at the registered-tool seam.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from mikrotik_rest_mcp.tools import (
    dns,
    firewall_filter,
    interface_wireless,
    ip_pool,
    ip_route,
    system_backup,
    system_logs,
    system_users,
)


class _CapturingMCP:
    """MCP stand-in that captures registered tool callables by name."""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, name: str, annotations: dict[str, Any]) -> Any:
        del annotations

        def decorator(fn: Any) -> Any:
            self.tools[name] = fn
            return fn

        return decorator


def _register(module: Any) -> dict[str, Any]:
    mcp = _CapturingMCP()
    module.register(mcp)
    return mcp.tools


# ---- dns.py ---------------------------------------------------------------


class TestDnsBespoke:
    @pytest.mark.asyncio
    async def test_get_dns_settings_returns_payload(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(dns)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = {"servers": "8.8.8.8"}

        result = await tools["mikrotik_get_dns_settings"](ctx=mock_context)

        assert result == {"servers": "8.8.8.8"}
        manager.get.assert_awaited_once_with("ip/dns")

    @pytest.mark.asyncio
    async def test_set_dns_servers_joins_list_and_converts_bools(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(dns)
        manager = mock_context.lifespan_context["connection_manager"]

        result = await tools["mikrotik_set_dns_servers"](
            servers=["1.1.1.1", "8.8.8.8"],
            allow_remote_requests=True,
            ctx=mock_context,
        )

        assert result == {"updated": True}
        sent = manager.patch.call_args.kwargs["json"]
        assert sent["servers"] == "1.1.1.1,8.8.8.8"
        assert sent["allow-remote-requests"] == "true"

    @pytest.mark.asyncio
    async def test_flush_dns_cache(self, mock_context: MagicMock) -> None:
        tools = _register(dns)
        manager = mock_context.lifespan_context["connection_manager"]

        result = await tools["mikrotik_flush_dns_cache"](ctx=mock_context)

        assert result == {"flushed": True}
        manager.delete.assert_awaited_once_with("ip/dns/cache")


# ---- firewall_filter.py ---------------------------------------------------


class TestBasicFirewallSetup:
    @pytest.mark.asyncio
    async def test_create_basic_setup_installs_default_security_rules(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(firewall_filter)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*1"}

        result = await tools["mikrotik_create_basic_firewall_setup"](ctx=mock_context)

        assert result["created"] == 5

        calls = manager.put.call_args_list
        # Every rule is written to the firewall filter table.
        for call in calls:
            assert call.args == ("ip/firewall/filter",)
        payloads = [call.kwargs["json"] for call in calls]

        def _has_rule(**expected: Any) -> bool:
            return any(expected.items() <= p.items() for p in payloads)

        # Input chain: accept return traffic for already-established sessions.
        assert _has_rule(
            chain="input",
            action="accept",
            **{"connection-state": "established,related"},
        )
        # Input chain: allow ICMP so the router is pingable / responds to PMTUD.
        assert _has_rule(chain="input", action="accept", protocol="icmp")
        # Input chain: drop unsolicited traffic arriving on the WAN interface.
        assert _has_rule(
            chain="input", action="drop", **{"in-interface": "ether1"}
        )
        # Forward chain: accept return traffic for connections already in flight.
        assert _has_rule(
            chain="forward",
            action="accept",
            **{"connection-state": "established,related"},
        )
        # Forward chain: drop packets the conntracker has flagged as invalid.
        assert _has_rule(
            chain="forward", action="drop", **{"connection-state": "invalid"}
        )

        # Security invariant: within each chain, accept rules must be installed
        # before drops so legitimate traffic is matched first.
        for chain in ("input", "forward"):
            actions = [p["action"] for p in payloads if p["chain"] == chain]
            accept_idx = [i for i, a in enumerate(actions) if a == "accept"]
            drop_idx = [i for i, a in enumerate(actions) if a == "drop"]
            if accept_idx and drop_idx:
                assert max(accept_idx) < min(drop_idx), (
                    f"{chain} chain: accept rules must come before drops"
                )


# ---- interface_wireless.py -----------------------------------------------


class TestWirelessBespoke:
    @pytest.mark.asyncio
    async def test_scan_posts_then_lists(self, mock_context: MagicMock) -> None:
        tools = _register(interface_wireless)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{"ssid": "MyAP"}]

        result = await tools["mikrotik_scan_wireless_networks"](
            interface="wlan1", ctx=mock_context
        )

        assert result == [{"ssid": "MyAP"}]
        manager.post.assert_awaited_once_with("interface/wireless/wlan1/scan", json={})

    @pytest.mark.asyncio
    async def test_registration_table_filters_by_interface(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(interface_wireless)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"interface": "wlan1", "mac-address": "AA"},
            {"interface": "wlan2", "mac-address": "BB"},
        ]

        result = await tools["mikrotik_get_wireless_registration_table"](
            interface="wlan1", ctx=mock_context
        )

        assert len(result) == 1
        assert result[0]["interface"] == "wlan1"


# ---- ip_pool.py -----------------------------------------------------------


class TestIpPoolBespoke:
    @pytest.mark.asyncio
    async def test_list_used_filters_by_pool_name(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(ip_pool)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"pool": "p1", "address": "10.0.0.1", "info": "host:a"},
            {"pool": "p2", "address": "10.0.0.2", "info": "host:b"},
        ]

        result = await tools["mikrotik_list_ip_pool_used"](
            pool_name="p1", ctx=mock_context
        )

        assert len(result) == 1
        assert result[0]["pool"] == "p1"

    @pytest.mark.asyncio
    async def test_expand_ip_pool_appends_ranges(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(ip_pool)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get_list.return_value = [
            {".id": "*1", "name": "p1", "ranges": "10.0.0.1-10.0.0.10"}
        ]

        result = await tools["mikrotik_expand_ip_pool"](
            name="p1", additional_ranges="10.0.0.11-10.0.0.20", ctx=mock_context
        )

        assert result == {
            "expanded": True,
            "id": "*1",
            "new_ranges": "10.0.0.1-10.0.0.10,10.0.0.11-10.0.0.20",
        }
        manager.patch.assert_awaited_once_with(
            "ip/pool/*1", json={"ranges": "10.0.0.1-10.0.0.10,10.0.0.11-10.0.0.20"}
        )

    @pytest.mark.asyncio
    async def test_expand_ip_pool_raises_when_not_found(
        self, mock_context: MagicMock
    ) -> None:
        from mikrotik_rest_mcp.exceptions import MikrotikNotFound

        tools = _register(ip_pool)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get_list.return_value = []

        with pytest.raises(MikrotikNotFound):
            await tools["mikrotik_expand_ip_pool"](
                name="ghost", additional_ranges="10.0.0.0/24", ctx=mock_context
            )


# ---- ip_route.py ----------------------------------------------------------


class TestIpRouteBespoke:
    @pytest.mark.asyncio
    async def test_routing_table_filters_by_table_and_active(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(ip_route)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get_list.return_value = [
            {"routing-table": "main", "active": "true"},
            {"routing-table": "main", "active": "false"},
            {"routing-table": "alt", "active": "true"},
        ]

        result = await tools["mikrotik_get_routing_table"](
            table_name="main", active_only=True, ctx=mock_context
        )

        assert len(result) == 1
        assert result[0]["routing-table"] == "main"
        assert result[0]["active"] == "true"

    @pytest.mark.asyncio
    async def test_route_statistics_counts(self, mock_context: MagicMock) -> None:
        tools = _register(ip_route)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"active": "true", "static": "true"},
            {"active": "true", "dynamic": "true"},
            {"disabled": "true"},
        ]

        result = await tools["mikrotik_get_route_statistics"](ctx=mock_context)

        assert result == {
            "total": 3,
            "active": 2,
            "disabled": 1,
            "dynamic": 1,
            "static": 1,
        }

    @pytest.mark.asyncio
    async def test_add_default_route_payload(self, mock_context: MagicMock) -> None:
        tools = _register(ip_route)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*1"}

        result = await tools["mikrotik_add_default_route"](
            gateway="192.168.1.1", distance=5, ctx=mock_context
        )

        assert result == {"added": True, "id": "*1"}
        sent = manager.put.call_args.kwargs["json"]
        assert sent["dst-address"] == "0.0.0.0/0"
        assert sent["gateway"] == "192.168.1.1"
        assert sent["distance"] == 5

    @pytest.mark.asyncio
    async def test_add_blackhole_route_payload(self, mock_context: MagicMock) -> None:
        tools = _register(ip_route)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.put.return_value = {".id": "*2"}

        await tools["mikrotik_add_blackhole_route"](
            dst_address="10.0.0.0/8", ctx=mock_context
        )

        sent = manager.put.call_args.kwargs["json"]
        assert sent["dst-address"] == "10.0.0.0/8"
        assert sent["type"] == "blackhole"

    @pytest.mark.asyncio
    async def test_flush_route_cache(self, mock_context: MagicMock) -> None:
        tools = _register(ip_route)
        manager = mock_context.lifespan_context["connection_manager"]

        result = await tools["mikrotik_flush_route_cache"](ctx=mock_context)

        assert result == {"flushed": True}
        manager.delete.assert_awaited_once_with("ip/route/cache")


# ---- system_backup.py -----------------------------------------------------


class TestSystemBackupBespoke:
    @pytest.mark.asyncio
    async def test_create_backup_serializes_bools(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_backup)
        manager = mock_context.lifespan_context["connection_manager"]

        result = await tools["mikrotik_create_backup"](
            name="snap1", dont_encrypt=True, include_password=False, ctx=mock_context
        )

        assert result == {"created": True, "name": "snap1"}
        sent = manager.post.call_args.kwargs["json"]
        assert sent == {
            "name": "snap1",
            "dont-encrypt": "true",
            "password": "false",
        }

    @pytest.mark.asyncio
    async def test_list_backups_keeps_only_backup_files(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_backup)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"name": "snap1.backup"},
            {"name": "config.rsc"},
            {"name": "random.txt"},
        ]

        result = await tools["mikrotik_list_backups"](ctx=mock_context)

        assert len(result) == 1
        assert result[0]["name"] == "snap1.backup"

    @pytest.mark.asyncio
    async def test_list_backups_optionally_includes_exports(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_backup)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"name": "snap1.backup"},
            {"name": "config.rsc"},
        ]

        result = await tools["mikrotik_list_backups"](
            include_exports=True, ctx=mock_context
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_download_file_returns_base64(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_backup)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{"name": "snap1.backup", "contents": "BASE64"}]

        result = await tools["mikrotik_download_file"](
            filename="snap1.backup", ctx=mock_context
        )

        assert result["content_base64"] == "BASE64"
        assert result["filename"] == "snap1.backup"

    @pytest.mark.asyncio
    async def test_download_file_raises_when_absent(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_backup)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = []

        with pytest.raises(ValueError, match="File not found"):
            await tools["mikrotik_download_file"](filename="x", ctx=mock_context)


# ---- system_logs.py -------------------------------------------------------


class TestSystemLogs:
    @pytest.mark.asyncio
    async def test_get_logs_with_topic_filter(self, mock_context: MagicMock) -> None:
        tools = _register(system_logs)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"topics": "firewall,info", "message": "drop"},
            {"topics": "dhcp", "message": "lease"},
        ]

        result = await tools["mikrotik_get_logs"](topics="firewall", ctx=mock_context)

        assert len(result) == 1
        assert "firewall" in result[0]["topics"]

    @pytest.mark.asyncio
    async def test_search_logs_case_insensitive(
        self, mock_context: MagicMock
    ) -> None:
        tools = _register(system_logs)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"message": "ERROR: bad"},
            {"message": "info: ok"},
        ]

        result = await tools["mikrotik_search_logs"](
            search_term="error", ctx=mock_context
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_logs_by_severity_filter(self, mock_context: MagicMock) -> None:
        tools = _register(system_logs)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [
            {"topics": "error,critical", "message": "x"},
            {"topics": "info", "message": "y"},
        ]

        result = await tools["mikrotik_get_logs_by_severity"](
            severity="error", ctx=mock_context
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_clear_logs_posts(self, mock_context: MagicMock) -> None:
        tools = _register(system_logs)
        manager = mock_context.lifespan_context["connection_manager"]

        result = await tools["mikrotik_clear_logs"](ctx=mock_context)

        assert result == {"cleared": True}
        manager.post.assert_awaited_once_with("log/clear")


# ---- system_users.py ------------------------------------------------------


class TestActiveUsers:
    @pytest.mark.asyncio
    async def test_get_active_users(self, mock_context: MagicMock) -> None:
        tools = _register(system_users)
        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = [{"name": "admin", "via": "ssh"}]

        result = await tools["mikrotik_get_active_users"](ctx=mock_context)

        assert result == [{"name": "admin", "via": "ssh"}]
        manager.get.assert_awaited_once_with("user/active")
