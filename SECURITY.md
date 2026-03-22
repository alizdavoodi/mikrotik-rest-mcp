# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities through [GitHub Security Advisories](https://github.com/alirezadavoodi/mikrotik-rest-mcp/security/advisories/new) or by opening a private issue.

## Scope

This policy covers the `mikrotik-rest-mcp` server code only. It does not cover:

- RouterOS itself (report to MikroTik)
- Network infrastructure or router configuration

## Important Security Notes

This MCP server can modify live network configuration on your routers. To minimize risk:

- Use a dedicated RouterOS user with minimum required permissions
- Prefer HTTPS in production (`MIKROTIK_USE_SSL=true`, `MIKROTIK_PORT=443`)
- Restrict REST API access by source IP in your RouterOS firewall
- Never commit credentials to version control
- Consider running with read-only permissions when only monitoring is needed
