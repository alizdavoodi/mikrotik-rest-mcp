"""RouterOS submenu descriptors.

One :class:`Submenu` per RouterOS REST path, paired with its Pydantic schema.
:func:`register_all` registers MCP tools for every submenu in :data:`SUBMENUS`.

Bespoke (non-CRUD) tools live in their original ``tools/*.py`` modules and are
registered separately by ``tools.register_tools``.
"""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP
from pydantic import Field

from .submenu import (
    Equals,
    RouterOSSchema,
    Submenu,
    Substring,
    SubstringAny,
    TrueFlag,
    Truthy,
    register_submenu,
)

# ---- Schemas --------------------------------------------------------------


class IpAddress(RouterOSSchema):
    address: str = Field(min_length=3)
    interface: str = Field(min_length=1)
    network: str | None = None
    broadcast: str | None = None
    comment: str | None = None
    disabled: bool = False


class IpRoute(RouterOSSchema):
    dst_address: str = Field(min_length=3, alias="dst-address")
    gateway: str = Field(min_length=1)
    distance: int | None = Field(default=None, ge=1, le=255)
    scope: int | None = None
    target_scope: int | None = Field(default=None, alias="target-scope")
    routing_mark: str | None = Field(default=None, alias="routing-mark")
    comment: str | None = None
    disabled: bool = False
    vrf_interface: str | None = Field(default=None, alias="vrf-interface")
    pref_src: str | None = Field(default=None, alias="pref-src")
    check_gateway: str | None = Field(default=None, alias="check-gateway")


class IpPool(RouterOSSchema):
    name: str = Field(min_length=1)
    ranges: str = Field(min_length=3)
    next_pool: str | None = Field(default=None, alias="next-pool")
    comment: str | None = None


class DnsStatic(RouterOSSchema):
    name: str = Field(min_length=1)
    address: str | None = None
    cname: str | None = None
    ttl: str | None = None
    comment: str | None = None
    disabled: bool = False
    regexp: str | None = None


class FirewallFilterRule(RouterOSSchema):
    chain: str
    action: str
    src_address: str | None = Field(default=None, alias="src-address")
    dst_address: str | None = Field(default=None, alias="dst-address")
    src_port: str | None = Field(default=None, alias="src-port")
    dst_port: str | None = Field(default=None, alias="dst-port")
    protocol: str | None = None
    in_interface: str | None = Field(default=None, alias="in-interface")
    out_interface: str | None = Field(default=None, alias="out-interface")
    connection_state: str | None = Field(default=None, alias="connection-state")
    src_address_list: str | None = Field(default=None, alias="src-address-list")
    dst_address_list: str | None = Field(default=None, alias="dst-address-list")
    limit: str | None = None
    tcp_flags: str | None = Field(default=None, alias="tcp-flags")
    connection_limit: str | None = Field(default=None, alias="connection-limit")
    address_list_timeout: str | None = Field(
        default=None, alias="address-list-timeout"
    )
    comment: str | None = None
    disabled: bool = False
    log: bool = False
    log_prefix: str | None = Field(default=None, alias="log-prefix")
    place_before: str | None = Field(default=None, alias="place-before")


class FirewallNatRule(RouterOSSchema):
    chain: str
    action: str
    src_address: str | None = Field(default=None, alias="src-address")
    dst_address: str | None = Field(default=None, alias="dst-address")
    src_port: str | None = Field(default=None, alias="src-port")
    dst_port: str | None = Field(default=None, alias="dst-port")
    protocol: str | None = None
    in_interface: str | None = Field(default=None, alias="in-interface")
    out_interface: str | None = Field(default=None, alias="out-interface")
    to_addresses: str | None = Field(default=None, alias="to-addresses")
    to_ports: str | None = Field(default=None, alias="to-ports")
    limit: str | None = None
    comment: str | None = None
    disabled: bool = False
    log: bool = False
    log_prefix: str | None = Field(default=None, alias="log-prefix")
    place_before: str | None = Field(default=None, alias="place-before")


class FirewallAddressListEntry(RouterOSSchema):
    list_name: str = Field(min_length=1, alias="list")
    address: str = Field(min_length=3)
    timeout: str | None = None
    comment: str | None = None
    disabled: bool = False


class VlanInterface(RouterOSSchema):
    name: str = Field(min_length=1)
    vlan_id: int = Field(ge=1, le=4094, alias="vlan-id")
    interface: str = Field(min_length=1)
    comment: str | None = None
    disabled: bool = False
    mtu: int | None = None


class WirelessInterface(RouterOSSchema):
    name: str
    ssid: str | None = None
    disabled: bool = False
    comment: str | None = None


class WireguardInterface(RouterOSSchema):
    name: str = Field(min_length=1)
    listen_port: int | None = Field(default=None, ge=1, le=65535, alias="listen-port")
    private_key: str | None = Field(default=None, alias="private-key")
    mtu: int | None = None
    comment: str | None = None
    disabled: bool = False


class WireguardPeer(RouterOSSchema):
    interface: str = Field(min_length=1)
    public_key: str = Field(min_length=30, alias="public-key")
    allowed_address: str = Field(min_length=3, alias="allowed-address")
    endpoint_address: str | None = Field(default=None, alias="endpoint-address")
    endpoint_port: int | None = Field(
        default=None, ge=1, le=65535, alias="endpoint-port"
    )
    preshared_key: str | None = Field(default=None, alias="preshared-key")
    persistent_keepalive: str | None = Field(
        default=None, alias="persistent-keepalive"
    )
    comment: str | None = None
    disabled: bool = False


class DhcpLease(RouterOSSchema):
    address: str
    mac_address: str = Field(alias="mac-address")
    server: str | None = None
    comment: str | None = None
    disabled: bool = False


class DhcpServer(RouterOSSchema):
    name: str
    interface: str
    lease_time: str = Field(default="1d", alias="lease-time")
    address_pool: str | None = Field(default=None, alias="address-pool")
    disabled: bool = False
    authoritative: str = "yes"
    delay_threshold: str | None = Field(default=None, alias="delay-threshold")
    comment: str | None = None


class DhcpPool(RouterOSSchema):
    name: str
    ranges: str
    next_pool: str | None = Field(default=None, alias="next-pool")
    comment: str | None = None


class User(RouterOSSchema):
    name: str = Field(min_length=1)
    password: str = Field(min_length=1)
    group: str = "read"
    address: str | None = None
    comment: str | None = None
    disabled: bool = False


class UserGroup(RouterOSSchema):
    name: str = Field(min_length=1)
    policy: str
    comment: str | None = None


class LoggingRule(RouterOSSchema):
    topics: str = Field(min_length=1)
    action: str = "memory"
    prefix: str | None = None
    disabled: bool = False


class LoggingAction(RouterOSSchema):
    name: str = Field(min_length=1)
    target: Literal["memory", "disk", "echo", "remote"] = "remote"
    remote: str | None = None
    remote_port: int | None = Field(
        default=None, ge=1, le=65535, alias="remote-port"
    )
    src_address: str | None = Field(default=None, alias="src-address")
    remote_protocol: Literal["udp", "tcp", "tls"] | None = Field(
        default=None, alias="remote-protocol"
    )
    remote_log_format: Literal["default", "cef", "syslog"] | None = Field(
        default=None, alias="remote-log-format"
    )
    syslog_facility: str | None = Field(default=None, alias="syslog-facility")
    syslog_severity: str | None = Field(default=None, alias="syslog-severity")
    syslog_time_format: Literal["bsd-syslog", "iso8601"] | None = Field(
        default=None, alias="syslog-time-format"
    )
    bsd_syslog: bool | None = Field(default=None, alias="bsd-syslog")
    vrf: str | None = None
    comment: str | None = None
    disabled: bool = False


# ---- Submenu descriptors --------------------------------------------------

# Filter chains shared across firewall_filter and firewall_nat (same shape).
_FW_RULE_FILTERS = (
    Equals("chain_filter", "chain"),
    Equals("action_filter", "action"),
    Substring("src_address_filter", "src-address"),
    Substring("dst_address_filter", "dst-address"),
    Equals("protocol_filter", "protocol"),
    SubstringAny("interface_filter", ("in-interface", "out-interface")),
    TrueFlag("disabled_only", "disabled"),
    TrueFlag("invalid_only", "invalid"),
)


SUBMENUS: list[Submenu] = [
    Submenu(
        path="ip/address",
        schema=IpAddress,
        id_param="address_id",
        singular="IP address",
        plural="IP addresses",
        tool_names={
            "list": "mikrotik_list_ip_addresses",
            "get": "mikrotik_get_ip_address",
            "create": "mikrotik_create_ip_address",
            "update": "mikrotik_update_ip_address",
            "remove": "mikrotik_remove_ip_address",
            "enable": "mikrotik_enable_ip_address",
            "disable": "mikrotik_disable_ip_address",
        },
        list_filters=(
            Equals("interface_filter", "interface"),
            Substring("address_filter", "address"),
            Equals("network_filter", "network"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("dynamic_only", "dynamic"),
        ),
    ),
    Submenu(
        path="ip/route",
        schema=IpRoute,
        id_param="route_id",
        singular="route",
        plural="routes",
        tool_names={
            "list": "mikrotik_list_routes",
            "get": "mikrotik_get_route",
            "create": "mikrotik_add_route",
            "update": "mikrotik_update_route",
            "remove": "mikrotik_remove_route",
            "enable": "mikrotik_enable_route",
            "disable": "mikrotik_disable_route",
        },
        list_filters=(
            Substring("dst_filter", "dst-address"),
            Substring("gateway_filter", "gateway"),
            Equals("routing_mark_filter", "routing-mark"),
            Equals("distance_filter", "distance"),
            TrueFlag("active_only", "active"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("dynamic_only", "dynamic"),
            TrueFlag("static_only", "static"),
        ),
    ),
    Submenu(
        path="ip/pool",
        schema=IpPool,
        id_param="name",
        singular="IP pool",
        plural="IP pools",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_ip_pools",
            "get": "mikrotik_get_ip_pool",
            "create": "mikrotik_create_ip_pool",
            "update": "mikrotik_update_ip_pool",
            "remove": "mikrotik_remove_ip_pool",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Substring("ranges_filter", "ranges"),
        ),
    ),
    Submenu(
        path="ip/dns/static",
        schema=DnsStatic,
        id_param="entry_id",
        singular="static DNS entry",
        plural="static DNS entries",
        tool_names={
            "list": "mikrotik_list_dns_static",
            "get": "mikrotik_get_dns_static",
            "create": "mikrotik_create_dns_static",
            "update": "mikrotik_update_dns_static",
            "remove": "mikrotik_remove_dns_static",
            "enable": "mikrotik_enable_dns_static",
            "disable": "mikrotik_disable_dns_static",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Substring("address_filter", "address"),
            Equals("type_filter", "type"),
            TrueFlag("disabled_only", "disabled"),
            Truthy("regexp_only", "regexp"),
        ),
    ),
    Submenu(
        path="ip/firewall/filter",
        schema=FirewallFilterRule,
        id_param="rule_id",
        singular="firewall filter rule",
        plural="firewall filter rules",
        create_only_fields=("place_before",),
        tool_names={
            "list": "mikrotik_list_filter_rules",
            "get": "mikrotik_get_filter_rule",
            "create": "mikrotik_create_filter_rule",
            "update": "mikrotik_update_filter_rule",
            "remove": "mikrotik_remove_filter_rule",
            "enable": "mikrotik_enable_filter_rule",
            "disable": "mikrotik_disable_filter_rule",
            "move": "mikrotik_move_filter_rule",
        },
        list_filters=(
            *_FW_RULE_FILTERS,
            TrueFlag("dynamic_only", "dynamic"),
        ),
    ),
    Submenu(
        path="ip/firewall/nat",
        schema=FirewallNatRule,
        id_param="rule_id",
        singular="NAT rule",
        plural="NAT rules",
        create_only_fields=("place_before",),
        tool_names={
            "list": "mikrotik_list_nat_rules",
            "get": "mikrotik_get_nat_rule",
            "create": "mikrotik_create_nat_rule",
            "update": "mikrotik_update_nat_rule",
            "remove": "mikrotik_remove_nat_rule",
            "enable": "mikrotik_enable_nat_rule",
            "disable": "mikrotik_disable_nat_rule",
            "move": "mikrotik_move_nat_rule",
        },
        list_filters=_FW_RULE_FILTERS,
    ),
    Submenu(
        path="ip/firewall/address-list",
        schema=FirewallAddressListEntry,
        id_param="entry_id",
        singular="firewall address-list entry",
        plural="firewall address-list entries",
        tool_names={
            "list": "mikrotik_list_firewall_address_list",
            "get": "mikrotik_get_firewall_address_list",
            "create": "mikrotik_create_firewall_address_list",
            "remove": "mikrotik_remove_firewall_address_list",
        },
        list_filters=(
            Equals("list_filter", "list"),
            Substring("address_filter", "address"),
            TrueFlag("disabled_only", "disabled"),
        ),
    ),
    Submenu(
        path="interface/vlan",
        schema=VlanInterface,
        id_param="name",
        singular="VLAN interface",
        plural="VLAN interfaces",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_vlan_interfaces",
            "get": "mikrotik_get_vlan_interface",
            "create": "mikrotik_create_vlan_interface",
            "update": "mikrotik_update_vlan_interface",
            "remove": "mikrotik_remove_vlan_interface",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Equals("vlan_id_filter", "vlan-id"),
            Equals("interface_filter", "interface"),
            TrueFlag("disabled_only", "disabled"),
        ),
    ),
    Submenu(
        path="interface/wireless",
        schema=WirelessInterface,
        id_param="name",
        singular="wireless interface",
        plural="wireless interfaces",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_wireless_interfaces",
            "get": "mikrotik_get_wireless_interface",
            "create": "mikrotik_create_wireless_interface",
            "update": "mikrotik_update_wireless_interface",
            "remove": "mikrotik_remove_wireless_interface",
        },
        list_filters=(
            Substring("name_filter", "name"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("running_only", "running"),
        ),
    ),
    Submenu(
        path="interface/wireguard",
        schema=WireguardInterface,
        id_param="name",
        singular="WireGuard interface",
        plural="WireGuard interfaces",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_wireguard_interfaces",
            "get": "mikrotik_get_wireguard_interface",
            "create": "mikrotik_create_wireguard_interface",
            "update": "mikrotik_update_wireguard_interface",
            "remove": "mikrotik_remove_wireguard_interface",
        },
        list_filters=(
            Substring("name_filter", "name"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("running_only", "running"),
        ),
    ),
    Submenu(
        path="interface/wireguard/peers",
        schema=WireguardPeer,
        id_param="peer_id",
        singular="WireGuard peer",
        plural="WireGuard peers",
        create_only_fields=("interface", "public_key"),
        tool_names={
            "list": "mikrotik_list_wireguard_peers",
            "get": "mikrotik_get_wireguard_peer",
            "create": "mikrotik_create_wireguard_peer",
            "update": "mikrotik_update_wireguard_peer",
            "remove": "mikrotik_remove_wireguard_peer",
        },
        list_filters=(
            Equals("interface_filter", "interface"),
            TrueFlag("disabled_only", "disabled"),
        ),
    ),
    Submenu(
        path="ip/dhcp-server/lease",
        schema=DhcpLease,
        id_param="lease_id",
        singular="DHCP lease",
        plural="DHCP leases",
        tool_names={
            "list": "mikrotik_list_dhcp_leases",
            "get": "mikrotik_get_dhcp_lease",
            "create": "mikrotik_create_dhcp_lease",
            "remove": "mikrotik_remove_dhcp_lease",
        },
        list_filters=(
            Equals("server", "server"),
            Equals("mac_address", "mac-address"),
            Equals("address", "address"),
            Equals("status", "status"),
        ),
    ),
    Submenu(
        path="ip/dhcp-server",
        schema=DhcpServer,
        id_param="name",
        singular="DHCP server",
        plural="DHCP servers",
        lookup_key="name",
        tool_names={
            "list": "mikrotik_list_dhcp_servers",
            "get": "mikrotik_get_dhcp_server",
            "create": "mikrotik_create_dhcp_server",
            "remove": "mikrotik_remove_dhcp_server",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Equals("interface_filter", "interface"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("invalid_only", "invalid"),
        ),
    ),
    Submenu(
        path="ip/pool",
        schema=DhcpPool,
        id_param="name",
        singular="DHCP pool",
        plural="DHCP pools",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_dhcp_pools",
            "get": "mikrotik_get_dhcp_pool",
            "create": "mikrotik_create_dhcp_pool",
            "update": "mikrotik_update_dhcp_pool",
            "remove": "mikrotik_remove_dhcp_pool",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Substring("ranges_filter", "ranges"),
        ),
    ),
    Submenu(
        path="user",
        schema=User,
        id_param="name",
        singular="user",
        plural="users",
        lookup_key="name",
        update_name_field="name",
        tool_names={
            "list": "mikrotik_list_users",
            "get": "mikrotik_get_user",
            "create": "mikrotik_create_user",
            "update": "mikrotik_update_user",
            "remove": "mikrotik_remove_user",
            "enable": "mikrotik_enable_user",
            "disable": "mikrotik_disable_user",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Equals("group_filter", "group"),
            TrueFlag("disabled_only", "disabled"),
            TrueFlag("active_only", "active"),
        ),
    ),
    Submenu(
        path="user/group",
        schema=UserGroup,
        id_param="name",
        singular="user group",
        plural="user groups",
        lookup_key="name",
        tool_names={
            "list": "mikrotik_list_user_groups",
            "get": "mikrotik_get_user_group",
            "create": "mikrotik_create_user_group",
            "remove": "mikrotik_remove_user_group",
        },
        list_filters=(
            Substring("name_filter", "name"),
            Substring("policy_filter", "policy"),
        ),
    ),
    Submenu(
        path="system/logging",
        schema=LoggingRule,
        id_param="rule_id",
        singular="logging rule",
        plural="logging rules",
        tool_names={
            "list": "mikrotik_list_logging_rules",
            "get": "mikrotik_get_logging_rule",
            "create": "mikrotik_create_logging_rule",
            "update": "mikrotik_update_logging_rule",
            "remove": "mikrotik_remove_logging_rule",
            "enable": "mikrotik_enable_logging_rule",
            "disable": "mikrotik_disable_logging_rule",
        },
        list_filters=(
            Substring("topics_filter", "topics"),
            Equals("action_filter", "action"),
        ),
    ),
    Submenu(
        path="system/logging/action",
        schema=LoggingAction,
        id_param="action_id",
        singular="logging action",
        plural="logging actions",
        tool_names={
            "list": "mikrotik_list_logging_actions",
            "get": "mikrotik_get_logging_action",
            "create": "mikrotik_create_logging_action",
            "update": "mikrotik_update_logging_action",
            "remove": "mikrotik_remove_logging_action",
        },
        list_filters=(Equals("target_filter", "target"),),
    ),
]


def register_all(mcp: FastMCP) -> None:
    """Register every submenu in :data:`SUBMENUS` as MCP tools."""
    for submenu in SUBMENUS:
        register_submenu(mcp, submenu)
