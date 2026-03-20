"""Tests for IP address Pydantic models and helper functions."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.ip_address import (
    IpAddressCreate,
    IpAddressUpdate,
    _filter_rows,
)


class TestIpAddressCreate:
    """Tests for IpAddressCreate Pydantic model."""

    def test_valid_minimal_payload(self) -> None:
        model = IpAddressCreate(address="192.168.1.1/24", interface="ether1")
        payload = model.model_dump(exclude_none=True)
        assert payload["address"] == "192.168.1.1/24"
        assert payload["interface"] == "ether1"
        assert payload["disabled"] is False

    def test_valid_full_payload(self) -> None:
        model = IpAddressCreate(
            address="192.168.1.1/24",
            interface="ether1",
            network="192.168.1.0",
            broadcast="192.168.1.255",
            comment="LAN address",
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)
        assert payload["address"] == "192.168.1.1/24"
        assert payload["interface"] == "ether1"
        assert payload["network"] == "192.168.1.0"
        assert payload["broadcast"] == "192.168.1.255"
        assert payload["comment"] == "LAN address"
        assert payload["disabled"] is True

    def test_address_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            IpAddressCreate(address="ab", interface="ether1")

    def test_interface_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            IpAddressCreate(address="192.168.1.1/24", interface="")


class TestIpAddressUpdate:
    """Tests for IpAddressUpdate Pydantic model."""

    def test_all_fields_optional(self) -> None:
        model = IpAddressUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update(self) -> None:
        model = IpAddressUpdate(address="10.0.0.1/24", disabled=True)
        payload = model.model_dump(exclude_none=True)
        assert payload["address"] == "10.0.0.1/24"
        assert payload["disabled"] is True
        assert "interface" not in payload


class TestFilterRows:
    """Tests for _filter_rows helper function."""

    @pytest.fixture
    def sample_rows(self) -> list[dict[str, Any]]:
        return [
            {
                ".id": "*1",
                "address": "192.168.88.1/24",
                "interface": "ether1",
                "disabled": "false",
                "dynamic": "false",
            },
            {
                ".id": "*2",
                "address": "10.0.0.1/24",
                "interface": "ether2",
                "disabled": "true",
                "dynamic": "false",
            },
            {
                ".id": "*3",
                "address": "192.168.1.1/24",
                "interface": "ether1",
                "disabled": "false",
                "dynamic": "true",
            },
            {
                ".id": "*4",
                "address": "172.16.0.1/16",
                "interface": "bridge",
                "disabled": "false",
                "dynamic": "false",
            },
        ]

    def test_no_filters_returns_all(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, None, None, None, False, False)
        assert len(result) == 4

    def test_filter_by_interface(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, "ether1", None, None, False, False)
        assert len(result) == 2
        assert all(r["interface"] == "ether1" for r in result)

    def test_filter_by_address(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, None, "192.168", None, False, False)
        assert len(result) == 2
        assert all("192.168" in r["address"] for r in result)

    def test_filter_by_network(self, sample_rows: list[dict[str, Any]]) -> None:
        rows_with_network = [
            {
                ".id": "*1",
                "address": "192.168.88.1/24",
                "interface": "ether1",
                "network": "192.168.88.0",
                "disabled": "false",
            },
            {
                ".id": "*2",
                "address": "10.0.0.1/24",
                "interface": "ether2",
                "network": "10.0.0.0",
                "disabled": "true",
            },
        ]
        result = _filter_rows(
            rows_with_network, None, None, "192.168.88.0", False, False
        )
        assert len(result) == 1
        assert result[0]["network"] == "192.168.88.0"

    def test_filter_disabled_only(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, None, None, None, True, False)
        assert len(result) == 1
        assert result[0]["disabled"] == "true"

    def test_filter_dynamic_only(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, None, None, None, False, True)
        assert len(result) == 1
        assert result[0]["dynamic"] == "true"

    def test_multiple_filters(self, sample_rows: list[dict[str, Any]]) -> None:
        result = _filter_rows(sample_rows, "ether1", "192.168", None, False, False)
        assert len(result) == 2

    def test_empty_rows(self) -> None:
        result = _filter_rows([], None, None, None, False, False)
        assert result == []
