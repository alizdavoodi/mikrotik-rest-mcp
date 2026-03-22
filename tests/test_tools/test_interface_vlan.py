from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.interface_vlan import VlanCreate, VlanUpdate


class TestVlanCreate:
    def test_required_fields(self) -> None:
        model = VlanCreate(name="vlan10", vlan_id=10, interface="bridge")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "vlan10"
        assert payload["vlan_id"] == 10
        assert payload["interface"] == "bridge"
        assert payload["disabled"] is False

    def test_optional_fields_default_none(self) -> None:
        model = VlanCreate(name="vlan20", vlan_id=20, interface="ether1")

        assert model.comment is None
        assert model.mtu is None

    def test_model_dump_excludes_none(self) -> None:
        model = VlanCreate(
            name="vlan30",
            vlan_id=30,
            interface="ether2",
            comment="guest",
            mtu=1500,
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["comment"] == "guest"
        assert payload["mtu"] == 1500
        assert payload["disabled"] is True

    def test_vlan_id_must_be_in_valid_range(self) -> None:
        with pytest.raises(ValidationError):
            VlanCreate(name="bad-low", vlan_id=0, interface="bridge")

        with pytest.raises(ValidationError):
            VlanCreate(name="bad-high", vlan_id=4095, interface="bridge")


class TestVlanUpdate:
    def test_all_fields_optional(self) -> None:
        model = VlanUpdate()
        assert model.model_dump(exclude_none=True) == {}

    def test_partial_update_dump(self) -> None:
        model = VlanUpdate(new_name="vlan100", disabled=False)
        payload = model.model_dump(exclude_none=True)

        assert payload["new_name"] == "vlan100"
        assert payload["disabled"] is False
        assert "interface" not in payload

    def test_vlan_id_validation_when_provided(self) -> None:
        with pytest.raises(ValidationError):
            VlanUpdate(vlan_id=0)

        valid = VlanUpdate(vlan_id=4094)
        assert valid.vlan_id == 4094
