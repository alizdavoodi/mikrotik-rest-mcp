# Context

Glossary of domain and architectural vocabulary used in this codebase.

## RouterOS / network domain

### Submenu

A RouterOS REST path that exposes a uniform list/get/create/update/remove
shape over a collection of records — for example `ip/firewall/filter`,
`interface/wireguard`, or `user/group`. The term mirrors RouterOS's own CLI
nomenclature for these resource collections.

Each submenu has a Pydantic schema (defining its fields and their kebab-case
wire aliases) and a `Submenu` descriptor (in `src/mikrotik_rest_mcp/submenus.py`)
declaring its path, schema, identifier semantics, list filters, and which CRUD
operations to expose as MCP tools.

### Bespoke tool

An MCP tool that doesn't fit the Submenu CRUD shape — typically because it
operates on a singleton config (`ip/dns`), executes a workflow
(`system/backup/save`), filters a stream (`/log`), or composes multiple
endpoints (basic firewall setup). Bespoke tools live in their original
`src/mikrotik_rest_mcp/tools/*.py` modules.

### .id vs lookup_key

RouterOS identifies records by an internal `.id` field (e.g. `*1`, `*A3`).
Some submenus also expose a human name (`user.name`, `interface/vlan.name`,
`ip/pool.name`). A submenu with `lookup_key="name"` resolves the caller's
supplied name to a `.id` by scanning the submenu before issuing the actual
patch/delete. Submenus with `lookup_key=None` accept the `.id` directly.

### Wire format

RouterOS REST expects kebab-case field names (`src-address`, `lease-time`)
and stringified booleans (`"true"` / `"false"`). Python-side schemas use
snake_case attributes; Pydantic field aliases bridge the two on serialize.

## Architectural terms

### Deep module

A module whose interface is small relative to its implementation — a lot of
behavior behind a thin surface. The Submenu module is the project's
canonical deep module: 18 RouterOS submenus collapse onto one ~600-line
synthesizer that exposes the entire CRUD surface (102 MCP tools) from data
descriptors.

### Seam

A boundary where behavior can be altered without editing in place. Tests
target seams, not internal helpers.

### Predicate

A list-tool filter rule. Five predicate types: `Substring`, `SubstringAny`
(match any of N fields), `Equals`, `TrueFlag` (RouterOS-style
`"true"`/`"false"` string flag), and `Truthy` (non-empty value). Each
predicate becomes one parameter on the synthesized `list_*` MCP tool.
