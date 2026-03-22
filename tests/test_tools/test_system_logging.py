from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.system_logging import (
    LoggingActionCreate,
    LoggingActionUpdate,
    LoggingRuleCreate,
    LoggingRuleUpdate,
    _translate,
)


class TestTranslate:
    def test_translates_snake_case_keys(self) -> None:
        payload = {
            "remote_port": 514,
            "src_address": "10.0.0.2",
            "remote_protocol": "udp",
            "remote_log_format": "syslog",
            "syslog_facility": "daemon",
            "syslog_severity": "warning",
            "syslog_time_format": "iso8601",
            "bsd_syslog": True,
        }

        result = _translate(payload)

        assert result["remote-port"] == 514
        assert result["src-address"] == "10.0.0.2"
        assert result["remote-protocol"] == "udp"
        assert result["remote-log-format"] == "syslog"
        assert result["syslog-facility"] == "daemon"
        assert result["syslog-severity"] == "warning"
        assert result["syslog-time-format"] == "iso8601"
        assert result["bsd-syslog"] == "true"

    def test_converts_any_bool_value_to_routeros_string(self) -> None:
        result = _translate({"disabled": False, "bsd_syslog": True})
        assert result["disabled"] == "false"
        assert result["bsd-syslog"] == "true"

    def test_preserves_unmapped_keys(self) -> None:
        result = _translate({"name": "remote-syslog", "target": "remote"})
        assert result == {"name": "remote-syslog", "target": "remote"}


class TestLoggingRuleCreate:
    def test_valid_minimal_payload(self) -> None:
        model = LoggingRuleCreate(topics="firewall")
        payload = model.model_dump(exclude_none=True)

        assert payload["topics"] == "firewall"
        assert payload["action"] == "memory"
        assert payload["disabled"] is False

    def test_topics_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            LoggingRuleCreate(topics="")


class TestLoggingRuleUpdate:
    def test_all_fields_optional(self) -> None:
        model = LoggingRuleUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update_payload(self) -> None:
        model = LoggingRuleUpdate(prefix="FW", disabled=True)
        payload = model.model_dump(exclude_none=True)

        assert payload["prefix"] == "FW"
        assert payload["disabled"] is True
        assert "topics" not in payload


class TestLoggingActionCreate:
    def test_valid_remote_action_payload(self) -> None:
        model = LoggingActionCreate(
            name="remote-syslog",
            target="remote",
            remote="10.10.10.10",
            remote_port=514,
            remote_protocol="udp",
            remote_log_format="syslog",
            disabled=False,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "remote-syslog"
        assert payload["target"] == "remote"
        assert payload["remote"] == "10.10.10.10"
        assert payload["remote_port"] == 514

    def test_remote_port_bounds_validation(self) -> None:
        with pytest.raises(ValidationError):
            LoggingActionCreate(name="bad-port", remote_port=70000)

    def test_target_literal_validation(self) -> None:
        with pytest.raises(ValidationError):
            LoggingActionCreate(name="invalid-target", target="file")


class TestLoggingActionUpdate:
    def test_all_fields_optional(self) -> None:
        model = LoggingActionUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update_payload(self) -> None:
        model = LoggingActionUpdate(remote_port=6514, disabled=True, bsd_syslog=False)
        payload = model.model_dump(exclude_none=True)

        assert payload["remote_port"] == 6514
        assert payload["disabled"] is True
        assert payload["bsd_syslog"] is False
