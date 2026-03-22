from __future__ import annotations

from mikrotik_rest_mcp.tools.interface_wireless import WirelessCreate, WirelessUpdate


class TestWirelessCreate:
    def test_required_fields(self) -> None:
        model = WirelessCreate(name="wlan1")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "wlan1"
        assert payload["disabled"] is False

    def test_optional_fields_default_none(self) -> None:
        model = WirelessCreate(name="wlan2")

        assert model.ssid is None
        assert model.comment is None

    def test_model_dump_excludes_none(self) -> None:
        model = WirelessCreate(name="wlan3", ssid="LabNet", disabled=True)
        payload = model.model_dump(exclude_none=True)

        assert payload["ssid"] == "LabNet"
        assert payload["disabled"] is True
        assert "comment" not in payload


class TestWirelessUpdate:
    def test_all_fields_optional(self) -> None:
        model = WirelessUpdate()
        assert model.model_dump(exclude_none=True) == {}

    def test_partial_update_dump(self) -> None:
        model = WirelessUpdate(new_name="wlan-main", comment="renamed", disabled=False)
        payload = model.model_dump(exclude_none=True)

        assert payload["new_name"] == "wlan-main"
        assert payload["comment"] == "renamed"
        assert payload["disabled"] is False
        assert "ssid" not in payload
