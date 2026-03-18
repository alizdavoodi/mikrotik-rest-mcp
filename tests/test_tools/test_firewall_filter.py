"""Tests for firewall filter Pydantic models and _translate helper."""

from __future__ import annotations

from typing import Any

import pytest

from mikrotik_rest_mcp.tools.firewall_filter import (
    FirewallFilterCreate,
    FirewallFilterUpdate,
    _translate,
)


class TestTranslate:
    """Tests for _translate helper function."""

    def test_translates_snake_to_kebab(self) -> None:
        payload = {
            "src_address": "192.168.1.0/24",
            "dst_address": "10.0.0.0/24",
            "src_port": "80",
            "dst_port": "443",
            "in_interface": "ether1",
            "out_interface": "ether2",
        }
        result = _translate(payload)

        assert "src-address" in result
        assert "dst-address" in result
        assert "src-port" in result
        assert "dst-port" in result
        assert "in-interface" in result
        assert "out-interface" in result
        assert "src_address" not in result
        assert "dst_address" not in result

    def test_converts_bool_disabled_to_string_true(self) -> None:
        payload = {"disabled": True}
        result = _translate(payload)
        assert result["disabled"] == "true"

    def test_converts_bool_disabled_to_string_false(self) -> None:
        payload = {"disabled": False}
        result = _translate(payload)
        assert result["disabled"] == "false"

    def test_converts_bool_log_to_string_true(self) -> None:
        payload = {"log": True}
        result = _translate(payload)
        assert result["log"] == "true"

    def test_converts_bool_log_to_string_false(self) -> None:
        payload = {"log": False}
        result = _translate(payload)
        assert result["log"] == "false"

    def test_preserves_other_fields(self) -> None:
        payload = {
            "chain": "input",
            "action": "accept",
            "src_address": "192.168.1.0/24",
        }
        result = _translate(payload)

        assert result["chain"] == "input"
        assert result["action"] == "accept"
        assert result["src-address"] == "192.168.1.0/24"

    def test_all_translations_combined(self) -> None:
        payload = {
            "src_address": "192.168.1.0/24",
            "dst_address": "10.0.0.0/24",
            "src_port": "80",
            "dst_port": "443",
            "in_interface": "ether1",
            "out_interface": "ether2",
            "connection_state": "established",
            "src_address_list": "allowed",
            "dst_address_list": "blocked",
            "tcp_flags": "syn",
            "connection_limit": "100",
            "address_list_timeout": "1h",
            "log_prefix": "firewall",
            "disabled": True,
            "log": False,
        }
        result = _translate(payload)

        assert result["src-address"] == "192.168.1.0/24"
        assert result["dst-address"] == "10.0.0.0/24"
        assert result["src-port"] == "80"
        assert result["dst-port"] == "443"
        assert result["in-interface"] == "ether1"
        assert result["out-interface"] == "ether2"
        assert result["connection-state"] == "established"
        assert result["src-address-list"] == "allowed"
        assert result["dst-address-list"] == "blocked"
        assert result["tcp-flags"] == "syn"
        assert result["connection-limit"] == "100"
        assert result["address-list-timeout"] == "1h"
        assert result["log-prefix"] == "firewall"
        assert result["disabled"] == "true"
        assert result["log"] == "false"


class TestFirewallFilterCreate:
    """Tests for FirewallFilterCreate Pydantic model."""

    def test_valid_minimal_payload(self) -> None:
        model = FirewallFilterCreate(chain="input", action="accept")
        payload = model.model_dump(exclude_none=True)
        assert payload["chain"] == "input"
        assert payload["action"] == "accept"

    def test_valid_full_payload(self) -> None:
        model = FirewallFilterCreate(
            chain="input",
            action="accept",
            src_address="192.168.1.0/24",
            dst_address="10.0.0.0/24",
            protocol="tcp",
            src_port="80",
            dst_port="443",
            comment="Allow HTTP",
            disabled=True,
            log=True,
        )
        payload = model.model_dump(exclude_none=True)
        assert payload["chain"] == "input"
        assert payload["action"] == "accept"
        assert payload["disabled"] is True
        assert payload["log"] is True


class TestFirewallFilterUpdate:
    """Tests for FirewallFilterUpdate Pydantic model."""

    def test_all_fields_optional(self) -> None:
        model = FirewallFilterUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update(self) -> None:
        model = FirewallFilterUpdate(comment="Updated", disabled=True)
        payload = model.model_dump(exclude_none=True)
        assert payload["comment"] == "Updated"
        assert payload["disabled"] is True
