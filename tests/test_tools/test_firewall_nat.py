from __future__ import annotations

from mikrotik_rest_mcp.tools.firewall_nat import NatCreate, NatUpdate, _translate


class TestTranslate:
    def test_translates_all_mapped_snake_keys_to_kebab(self) -> None:
        payload = {
            "src_address": "192.168.1.0/24",
            "dst_address": "10.0.0.0/24",
            "src_port": "1234",
            "dst_port": "443",
            "in_interface": "ether1",
            "out_interface": "ether2",
            "to_addresses": "172.16.0.10",
            "to_ports": "8443",
            "log_prefix": "nat-log",
        }

        result = _translate(payload)

        assert result["src-address"] == "192.168.1.0/24"
        assert result["dst-address"] == "10.0.0.0/24"
        assert result["src-port"] == "1234"
        assert result["dst-port"] == "443"
        assert result["in-interface"] == "ether1"
        assert result["out-interface"] == "ether2"
        assert result["to-addresses"] == "172.16.0.10"
        assert result["to-ports"] == "8443"
        assert result["log-prefix"] == "nat-log"

    def test_converts_disabled_bool_to_string(self) -> None:
        assert _translate({"disabled": True}) == {"disabled": "true"}
        assert _translate({"disabled": False}) == {"disabled": "false"}

    def test_converts_log_bool_to_string(self) -> None:
        assert _translate({"log": True}) == {"log": "true"}
        assert _translate({"log": False}) == {"log": "false"}

    def test_unmapped_keys_pass_through(self) -> None:
        payload = {"chain": "srcnat", "action": "masquerade", "protocol": "tcp"}
        result = _translate(payload)

        assert result == payload

    def test_empty_payload(self) -> None:
        assert _translate({}) == {}


class TestNatCreate:
    def test_required_fields(self) -> None:
        model = NatCreate(chain="srcnat", action="masquerade")
        payload = model.model_dump(exclude_none=True)

        assert payload["chain"] == "srcnat"
        assert payload["action"] == "masquerade"
        assert payload["disabled"] is False
        assert payload["log"] is False

    def test_optional_fields_default_none(self) -> None:
        model = NatCreate(chain="srcnat", action="masquerade")

        assert model.src_address is None
        assert model.dst_address is None
        assert model.log_prefix is None

    def test_model_dump_excludes_none(self) -> None:
        model = NatCreate(chain="srcnat", action="masquerade", comment="edge")
        payload = model.model_dump(exclude_none=True)

        assert payload["comment"] == "edge"
        assert "src_address" not in payload
        assert "to_addresses" not in payload


class TestNatUpdate:
    def test_all_fields_optional(self) -> None:
        model = NatUpdate()
        assert model.model_dump(exclude_none=True) == {}

    def test_partial_update_dump(self) -> None:
        model = NatUpdate(dst_address="1.2.3.4", disabled=False)
        payload = model.model_dump(exclude_none=True)

        assert payload["dst_address"] == "1.2.3.4"
        assert payload["disabled"] is False
        assert "chain" not in payload
