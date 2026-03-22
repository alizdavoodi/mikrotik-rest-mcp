from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.ip_pool import PoolCreate, PoolUpdate


class TestPoolCreate:
    def test_valid_minimal_payload(self) -> None:
        model = PoolCreate(name="lan-pool", ranges="192.168.88.10-192.168.88.200")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "lan-pool"
        assert payload["ranges"] == "192.168.88.10-192.168.88.200"
        assert "next_pool" not in payload
        assert "comment" not in payload

    def test_valid_full_payload(self) -> None:
        model = PoolCreate(
            name="guest-pool",
            ranges="10.10.10.10-10.10.10.250",
            next_pool="fallback-pool",
            comment="Guest network pool",
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["next_pool"] == "fallback-pool"
        assert payload["comment"] == "Guest network pool"

    def test_name_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            PoolCreate(name="", ranges="10.0.0.2-10.0.0.50")

    def test_ranges_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            PoolCreate(name="pool", ranges="ab")


class TestPoolUpdate:
    def test_all_fields_optional(self) -> None:
        model = PoolUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update_payload(self) -> None:
        model = PoolUpdate(new_name="renamed-pool", comment="updated")
        payload = model.model_dump(exclude_none=True)

        assert payload["new_name"] == "renamed-pool"
        assert payload["comment"] == "updated"
        assert "ranges" not in payload
