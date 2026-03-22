from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.firewall_address_list import AddressListCreate


class TestAddressListCreate:
    def test_required_fields(self) -> None:
        model = AddressListCreate(list_name="blocked", address="192.168.1.1")
        payload = model.model_dump(exclude_none=True)

        assert payload["list_name"] == "blocked"
        assert payload["address"] == "192.168.1.1"
        assert payload["disabled"] is False

    def test_optional_fields_default_none(self) -> None:
        model = AddressListCreate(list_name="allowed", address="10.0.0.0/24")

        assert model.timeout is None
        assert model.comment is None

    def test_model_dump_excludes_none(self) -> None:
        model = AddressListCreate(
            list_name="allowed",
            address="10.0.0.0/24",
            timeout="1h",
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["timeout"] == "1h"
        assert payload["disabled"] is True
        assert "comment" not in payload

    def test_list_name_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            AddressListCreate(list_name="", address="10.0.0.1")

    def test_address_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            AddressListCreate(list_name="blocked", address="1")
