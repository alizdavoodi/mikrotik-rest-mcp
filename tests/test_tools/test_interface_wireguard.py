from __future__ import annotations

import pytest
from pydantic import ValidationError

from mikrotik_rest_mcp.tools.interface_wireguard import (
    WireguardInterfaceCreate,
    WireguardPeerCreate,
)


class TestWireguardInterfaceCreate:
    def test_required_fields(self) -> None:
        model = WireguardInterfaceCreate(name="wg0")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "wg0"
        assert payload["disabled"] is False

    def test_optional_fields_default_none(self) -> None:
        model = WireguardInterfaceCreate(name="wg1")

        assert model.listen_port is None
        assert model.private_key is None
        assert model.mtu is None
        assert model.comment is None

    def test_model_dump_excludes_none(self) -> None:
        model = WireguardInterfaceCreate(
            name="wg2",
            listen_port=51820,
            private_key="x" * 44,
            comment="tunnel",
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["listen_port"] == 51820
        assert payload["private_key"] == "x" * 44
        assert payload["disabled"] is True
        assert "mtu" not in payload

    def test_listen_port_validation(self) -> None:
        with pytest.raises(ValidationError):
            WireguardInterfaceCreate(name="wg-bad", listen_port=0)

        with pytest.raises(ValidationError):
            WireguardInterfaceCreate(name="wg-bad", listen_port=65536)


class TestWireguardPeerCreate:
    def test_required_fields(self) -> None:
        model = WireguardPeerCreate(
            interface="wg0",
            public_key="k" * 30,
            allowed_address="10.10.0.2/32",
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["interface"] == "wg0"
        assert payload["public_key"] == "k" * 30
        assert payload["allowed_address"] == "10.10.0.2/32"
        assert payload["disabled"] is False

    def test_optional_fields_default_none(self) -> None:
        model = WireguardPeerCreate(
            interface="wg0",
            public_key="p" * 30,
            allowed_address="10.10.0.3/32",
        )

        assert model.endpoint_address is None
        assert model.endpoint_port is None
        assert model.preshared_key is None
        assert model.persistent_keepalive is None
        assert model.comment is None

    def test_model_dump_excludes_none(self) -> None:
        model = WireguardPeerCreate(
            interface="wg0",
            public_key="z" * 30,
            allowed_address="10.10.0.4/32",
            endpoint_address="vpn.example.com",
            endpoint_port=51820,
            disabled=True,
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["endpoint_address"] == "vpn.example.com"
        assert payload["endpoint_port"] == 51820
        assert payload["disabled"] is True
        assert "preshared_key" not in payload

    def test_public_key_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            WireguardPeerCreate(
                interface="wg0",
                public_key="short",
                allowed_address="10.10.0.5/32",
            )

    def test_allowed_address_min_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            WireguardPeerCreate(
                interface="wg0", public_key="k" * 30, allowed_address="x"
            )

    def test_endpoint_port_validation(self) -> None:
        with pytest.raises(ValidationError):
            WireguardPeerCreate(
                interface="wg0",
                public_key="k" * 30,
                allowed_address="10.10.0.6/32",
                endpoint_port=0,
            )

        valid = WireguardPeerCreate(
            interface="wg0",
            public_key="k" * 30,
            allowed_address="10.10.0.6/32",
            endpoint_port=65535,
        )
        assert valid.endpoint_port == 65535
