from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.system_users import UserCreate, UserUpdate


class TestUserCreate:
    def test_valid_minimal_payload(self) -> None:
        model = UserCreate(name="alice", password="secret")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "alice"
        assert payload["password"] == "secret"
        assert payload["group"] == "read"
        assert payload["disabled"] is False

    def test_valid_full_payload(self) -> None:
        model = UserCreate(
            name="ops",
            password="strong-pass",
            group="full",
            address="192.168.88.0/24",
            comment="Operations user",
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["group"] == "full"
        assert payload["address"] == "192.168.88.0/24"
        assert payload["comment"] == "Operations user"
        assert payload["disabled"] is True

    def test_name_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(name="", password="secret")

    def test_password_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(name="bob", password="")


class TestUserUpdate:
    def test_all_fields_optional(self) -> None:
        model = UserUpdate()
        payload = model.model_dump(exclude_none=True)
        assert payload == {}

    def test_partial_update_payload(self) -> None:
        model = UserUpdate(new_name="new-user", disabled=False, group="write")
        payload = model.model_dump(exclude_none=True)

        assert payload["new_name"] == "new-user"
        assert payload["disabled"] is False
        assert payload["group"] == "write"
        assert "password" not in payload
