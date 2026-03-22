from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.dns import DnsSettingsUpdate, register


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


class TestDnsSettingsUpdate:
    def test_valid_minimal_payload_defaults(self) -> None:
        model = DnsSettingsUpdate(servers=["1.1.1.1"])
        data = model.model_dump(exclude_none=True)

        assert data["servers"] == ["1.1.1.1"]
        assert data["allow_remote_requests"] is False
        assert data["use_doh"] is False
        assert data["verify_doh_cert"] is True
        assert "doh_server" not in data
        assert "cache_size" not in data

    def test_valid_full_payload(self) -> None:
        model = DnsSettingsUpdate(
            servers=["1.1.1.1", "8.8.8.8"],
            allow_remote_requests=True,
            max_udp_packet_size=4096,
            max_concurrent_queries=150,
            cache_size=4096,
            cache_max_ttl="1d",
            use_doh=True,
            doh_server="https://dns.google/dns-query",
            verify_doh_cert=False,
        )
        data = model.model_dump(exclude_none=True)

        assert data["servers"] == ["1.1.1.1", "8.8.8.8"]
        assert data["allow_remote_requests"] is True
        assert data["max_udp_packet_size"] == 4096
        assert data["max_concurrent_queries"] == 150
        assert data["cache_size"] == 4096
        assert data["cache_max_ttl"] == "1d"
        assert data["use_doh"] is True
        assert data["doh_server"] == "https://dns.google/dns-query"
        assert data["verify_doh_cert"] is False

    def test_servers_requires_at_least_one(self) -> None:
        with pytest.raises(ValidationError):
            DnsSettingsUpdate(servers=[])


class TestDnsTools:
    @pytest.mark.asyncio
    async def test_get_dns_settings_returns_empty_dict_when_none(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        get_dns_settings = tools["mikrotik_get_dns_settings"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = None

        result = await get_dns_settings(ctx=mock_context)

        assert result == {}
        manager.get.assert_awaited_once_with("ip/dns")

    @pytest.mark.asyncio
    async def test_set_dns_servers_builds_expected_payload(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        set_dns_servers = tools["mikrotik_set_dns_servers"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await set_dns_servers(
            servers=["1.1.1.1", "8.8.8.8"],
            allow_remote_requests=True,
            max_udp_packet_size=4096,
            max_concurrent_queries=200,
            cache_size=8192,
            cache_max_ttl="12h",
            use_doh=True,
            doh_server="https://cloudflare-dns.com/dns-query",
            verify_doh_cert=False,
            ctx=mock_context,
        )

        assert result == {"updated": True}
        manager.patch.assert_awaited_once_with(
            "ip/dns",
            json={
                "servers": "1.1.1.1,8.8.8.8",
                "allow-remote-requests": "true",
                "use-doh-server": "true",
                "verify-doh-cert": "false",
                "max-udp-packet-size": 4096,
                "max-concurrent-queries": 200,
                "cache-size": 8192,
                "cache-max-ttl": "12h",
                "doh-server": "https://cloudflare-dns.com/dns-query",
            },
        )

    @pytest.mark.asyncio
    async def test_get_dns_cache_returns_empty_list_when_none(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        get_dns_cache = tools["mikrotik_get_dns_cache"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = None

        result = await get_dns_cache(ctx=mock_context)

        assert result == []
        manager.get.assert_awaited_once_with("ip/dns/cache")

    @pytest.mark.asyncio
    async def test_flush_dns_cache_calls_delete(self, mock_context: object) -> None:
        tools = _registered_tools()
        flush_dns_cache = tools["mikrotik_flush_dns_cache"]

        manager = mock_context.lifespan_context["connection_manager"]

        result = await flush_dns_cache(ctx=mock_context)

        assert result == {"flushed": True}
        manager.delete.assert_awaited_once_with("ip/dns/cache")

    @pytest.mark.asyncio
    async def test_get_dns_cache_statistics_returns_empty_dict_when_none(
        self, mock_context: object
    ) -> None:
        tools = _registered_tools()
        get_dns_cache_statistics = tools["mikrotik_get_dns_cache_statistics"]

        manager = mock_context.lifespan_context["connection_manager"]
        manager.get.return_value = None

        result = await get_dns_cache_statistics(ctx=mock_context)

        assert result == {}
        manager.get.assert_awaited_once_with("ip/dns/cache/all")
