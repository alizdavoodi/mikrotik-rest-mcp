# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-03-20

### Added
- GitHub Actions CI/CD workflows (lint, typecheck, test, build, release)
- Nix flake support for reproducible development

### Fixed
- Logging rule update model validation

## [0.1.0] - 2026-03-18

### Added
- Initial release with 122 MCP tools across 17 modules
- IP management (addresses, routes, pools)
- DNS configuration and static entries
- Firewall filter rules, NAT, and address lists
- Interface management (VLAN, wireless, WireGuard)
- DHCP server, lease, and pool management
- System administration (users, backups, logs, logging rules)
- stdio, SSE, and streamable-http transport modes
- Pydantic validation for all inputs
- MIT license
