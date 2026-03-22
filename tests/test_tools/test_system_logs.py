from __future__ import annotations

from typing import Any

import pytest

from mikrotik_rest_mcp.tools.system_logs import _filter_logs


class TestFilterLogs:
    @pytest.fixture
    def sample_logs(self) -> list[dict[str, Any]]:
        return [
            {
                ".id": "*1",
                "topics": "system,info",
                "message": "system rebooted successfully",
                "prefix": "SYS",
            },
            {
                ".id": "*2",
                "topics": "firewall,warning",
                "message": "drop action for invalid connection",
                "prefix": "FW",
            },
            {
                ".id": "*3",
                "topics": "dhcp,error",
                "message": "Lease assignment failed",
                "prefix": "DHCP",
            },
            {
                ".id": "*4",
                "topics": "firewall,info",
                "message": "accept action from trusted host",
                "prefix": "ALLOW",
            },
        ]

    def test_no_filters_returns_all(self, sample_logs: list[dict[str, Any]]) -> None:
        result = _filter_logs(sample_logs, None, None, None, None)
        assert len(result) == 4

    def test_topics_filter_single_topic(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, "firewall", None, None, None)
        assert len(result) == 2
        assert all("firewall" in str(r.get("topics", "")) for r in result)

    def test_topics_filter_multiple_topics_or_logic(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, "dhcp,system", None, None, None)
        assert len(result) == 2
        assert {r[".id"] for r in result} == {"*1", "*3"}

    def test_action_filter_is_case_insensitive(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, None, "AcTiOn", None, None)
        assert len(result) == 2
        assert {r[".id"] for r in result} == {"*2", "*4"}

    def test_message_filter_is_case_insensitive(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, None, None, "LEASE", None)
        assert len(result) == 1
        assert result[0][".id"] == "*3"

    def test_prefix_filter_matches_message_prefix(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, None, None, None, "system")
        assert len(result) == 1
        assert result[0][".id"] == "*1"

    def test_prefix_filter_matches_prefix_field(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, None, None, None, "FW")
        assert len(result) == 1
        assert result[0][".id"] == "*2"

    def test_prefix_filter_supports_multi_prefix_or(
        self, sample_logs: list[dict[str, Any]]
    ) -> None:
        result = _filter_logs(sample_logs, None, None, None, "ALLOW,DHCP")
        assert len(result) == 2
        assert {r[".id"] for r in result} == {"*3", "*4"}

    def test_combined_filters(self, sample_logs: list[dict[str, Any]]) -> None:
        result = _filter_logs(sample_logs, "firewall", "accept", "trusted", "ALLOW")
        assert len(result) == 1
        assert result[0][".id"] == "*4"

    def test_empty_logs_returns_empty(self) -> None:
        result = _filter_logs([], "firewall", "drop", "invalid", "FW")
        assert result == []
