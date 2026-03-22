from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.ip_route import (
    IpRouteCreate,
    IpRouteUpdate,
    _convert_create_payload,
    _convert_update_payload,
    _filter_routes,
)


class TestIpRouteCreate:
    def test_valid_minimal_payload(self) -> None:
        model = IpRouteCreate(dst_address="0.0.0.0/0", gateway="192.168.88.254")
        payload = model.model_dump(exclude_none=True)

        assert payload["dst_address"] == "0.0.0.0/0"
        assert payload["gateway"] == "192.168.88.254"
        assert payload["disabled"] is False

    def test_valid_full_payload(self) -> None:
        model = IpRouteCreate(
            dst_address="10.10.10.0/24",
            gateway="172.16.1.1",
            distance=2,
            scope=30,
            target_scope=10,
            routing_mark="wan2",
            comment="backup route",
            disabled=True,
            vrf_interface="ether2",
            pref_src="10.10.10.1",
            check_gateway="ping",
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["distance"] == 2
        assert payload["scope"] == 30
        assert payload["target_scope"] == 10
        assert payload["routing_mark"] == "wan2"
        assert payload["disabled"] is True
        assert payload["vrf_interface"] == "ether2"
        assert payload["pref_src"] == "10.10.10.1"
        assert payload["check_gateway"] == "ping"

    def test_distance_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            IpRouteCreate(dst_address="0.0.0.0/0", gateway="1.1.1.1", distance=0)

    def test_distance_above_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            IpRouteCreate(dst_address="0.0.0.0/0", gateway="1.1.1.1", distance=256)


class TestIpRouteUpdate:
    def test_all_fields_optional(self) -> None:
        model = IpRouteUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update_payload(self) -> None:
        model = IpRouteUpdate(gateway="10.0.0.254", disabled=False)
        payload = model.model_dump(exclude_none=True)

        assert payload["gateway"] == "10.0.0.254"
        assert payload["disabled"] is False
        assert "routing_mark" not in payload

    def test_distance_validation(self) -> None:
        with pytest.raises(ValidationError):
            IpRouteUpdate(distance=999)


class TestFilterRoutes:
    @pytest.fixture
    def sample_routes(self) -> list[dict[str, Any]]:
        return [
            {
                ".id": "*1",
                "dst-address": "0.0.0.0/0",
                "gateway": "192.168.88.254",
                "routing-mark": "main",
                "distance": "1",
                "active": "true",
                "disabled": "false",
                "dynamic": "false",
                "static": "true",
            },
            {
                ".id": "*2",
                "dst-address": "10.10.0.0/16",
                "gateway": "172.16.1.1",
                "routing-mark": "wan2",
                "distance": "2",
                "active": "false",
                "disabled": "true",
                "dynamic": "false",
                "static": "true",
            },
            {
                ".id": "*3",
                "dst-address": "192.168.50.0/24",
                "gateway": "pppoe-out1",
                "routing-mark": "main",
                "distance": "1",
                "active": "true",
                "disabled": "false",
                "dynamic": "true",
                "static": "false",
            },
            {
                ".id": "*4",
                "dst-address": "172.20.0.0/16",
                "gateway": "10.0.0.1",
                "routing-mark": "guest",
                "distance": "5",
                "active": "true",
                "disabled": "false",
                "dynamic": "false",
                "static": "true",
            },
        ]

    def test_no_filters_returns_all(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, None, False, False, False, False
        )
        assert len(result) == 4

    def test_filter_by_dst(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, "10.10", None, None, None, False, False, False, False
        )
        assert len(result) == 1
        assert result[0][".id"] == "*2"

    def test_filter_by_gateway(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, "pppoe", None, None, False, False, False, False
        )
        assert len(result) == 1
        assert result[0][".id"] == "*3"

    def test_filter_by_routing_mark(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, "main", None, False, False, False, False
        )
        assert len(result) == 2
        assert all(r["routing-mark"] == "main" for r in result)

    def test_filter_by_distance(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, 1, False, False, False, False
        )
        assert len(result) == 2
        assert all(r["distance"] == "1" for r in result)

    def test_filter_active_only(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, None, True, False, False, False
        )
        assert len(result) == 3
        assert all(r["active"] == "true" for r in result)

    def test_filter_disabled_only(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, None, False, True, False, False
        )
        assert len(result) == 1
        assert result[0]["disabled"] == "true"

    def test_filter_dynamic_only(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, None, False, False, True, False
        )
        assert len(result) == 1
        assert result[0]["dynamic"] == "true"

    def test_filter_static_only(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes, None, None, None, None, False, False, False, True
        )
        assert len(result) == 3
        assert all(r["static"] == "true" for r in result)

    def test_combined_filters(self, sample_routes: list[dict[str, Any]]) -> None:
        result = _filter_routes(
            sample_routes,
            "172.20",
            "10.0.0.1",
            "guest",
            5,
            True,
            False,
            False,
            True,
        )
        assert len(result) == 1
        assert result[0][".id"] == "*4"

    def test_no_matches_returns_empty(
        self, sample_routes: list[dict[str, Any]]
    ) -> None:
        result = _filter_routes(
            sample_routes, None, None, "nonexistent", None, False, False, False, False
        )
        assert result == []

    def test_empty_rows(self) -> None:
        result = _filter_routes([], None, None, None, None, True, True, True, True)
        assert result == []


class TestConvertCreatePayload:
    def test_converts_snake_case_and_bool_and_preserves_other_keys(self) -> None:
        payload = {
            "dst_address": "10.0.0.0/24",
            "target_scope": 10,
            "routing_mark": "wan1",
            "vrf_interface": "ether3",
            "pref_src": "10.0.0.1",
            "check_gateway": "ping",
            "gateway": "172.16.0.1",
            "distance": 2,
            "disabled": True,
        }

        result = _convert_create_payload(payload)

        assert result["dst-address"] == "10.0.0.0/24"
        assert result["target-scope"] == 10
        assert result["routing-mark"] == "wan1"
        assert result["vrf-interface"] == "ether3"
        assert result["pref-src"] == "10.0.0.1"
        assert result["check-gateway"] == "ping"
        assert result["gateway"] == "172.16.0.1"
        assert result["distance"] == 2
        assert result["disabled"] == "true"

    def test_converts_disabled_false_to_string_false(self) -> None:
        result = _convert_create_payload(
            {"dst_address": "0.0.0.0/0", "disabled": False}
        )
        assert result["disabled"] == "false"

    def test_passthrough_payload_when_no_convertible_fields(self) -> None:
        payload = {"gateway": "1.1.1.1", "distance": 1}
        result = _convert_create_payload(payload)
        assert result == {"gateway": "1.1.1.1", "distance": 1}


class TestConvertUpdatePayload:
    def test_converts_snake_case_and_bool(self) -> None:
        payload = {
            "dst_address": "192.168.0.0/16",
            "target_scope": 20,
            "routing_mark": "main",
            "check_gateway": "arp",
            "disabled": True,
        }

        result = _convert_update_payload(payload)

        assert result["dst-address"] == "192.168.0.0/16"
        assert result["target-scope"] == 20
        assert result["routing-mark"] == "main"
        assert result["check-gateway"] == "arp"
        assert result["disabled"] == "true"

    def test_converts_disabled_false_to_string_false(self) -> None:
        result = _convert_update_payload({"disabled": False, "gateway": "2.2.2.2"})
        assert result["disabled"] == "false"
        assert result["gateway"] == "2.2.2.2"

    def test_keeps_unrelated_keys(self) -> None:
        payload = {"comment": "updated", "scope": 30}
        result = _convert_update_payload(payload)
        assert result == {"comment": "updated", "scope": 30}
