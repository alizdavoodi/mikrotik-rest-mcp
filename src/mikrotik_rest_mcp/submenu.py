"""RouterOS submenu — deep module for CRUD over RouterOS REST submenus.

A RouterOS submenu is a path like ``ip/firewall/filter`` or ``interface/wireguard``
that exposes a uniform list/get/create/update/remove shape over its records.
This module collapses per-resource CRUD into a single :class:`Submenu` descriptor
plus :func:`register_submenu`, which synthesizes MCP tools from it.

Glossary:
    Submenu     The RouterOS submenu path and its record schema.
    Predicate   A list-tool filter (Substring, SubstringAny, Equals, TrueFlag, Truthy).
    lookup_key  Row field used to resolve ``.id`` from a caller-supplied name.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from types import UnionType
from typing import Any, Union, get_args, get_origin

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict

from .annotations import DESTRUCTIVE, READ, WRITE
from .connection import MikrotikConnectionManager
from .exceptions import MikrotikNotFound


def get_manager(ctx: Context) -> MikrotikConnectionManager:
    """Read the MikroTik connection manager from MCP lifespan context."""
    manager = ctx.lifespan_context.get("connection_manager")
    if not isinstance(manager, MikrotikConnectionManager):
        raise ToolError("MikroTik connection manager is not available")
    return manager


# ---- Schema base ----------------------------------------------------------


class RouterOSSchema(BaseModel):
    """Base class for RouterOS resource schemas.

    Use ``Field(alias="src-address")`` for fields whose RouterOS wire name
    differs from the Python attribute. ``to_router_os`` applies aliases and
    coerces booleans to the ``"true"``/``"false"`` strings RouterOS expects.
    """

    model_config = ConfigDict(populate_by_name=True)

    def to_router_os(self) -> dict[str, Any]:
        return _serialize(self.model_dump(by_alias=True, exclude_none=True))


def _serialize(data: dict[str, Any]) -> dict[str, Any]:
    """RouterOS wire conventions: bool -> 'true'/'false'; pass everything else."""
    result: dict[str, Any] = {}
    for k, v in data.items():
        if v is True:
            result[k] = "true"
        elif v is False:
            result[k] = "false"
        else:
            result[k] = v
    return result


def _payload_from_partial(
    schema: type[RouterOSSchema], values: dict[str, Any]
) -> dict[str, Any]:
    """Wire payload from a partial kwargs dict, using schema aliases."""
    aliases = {
        name: (info.alias or name) for name, info in schema.model_fields.items()
    }
    return _serialize(
        {aliases.get(k, k): v for k, v in values.items() if v is not None}
    )


# ---- Predicates -----------------------------------------------------------


@dataclass(frozen=True)
class Substring:
    """Keep rows where ``row[field]`` contains the param value."""

    param: str
    field: str

    def matches(self, row: dict[str, Any], value: Any) -> bool:
        return str(value) in str(row.get(self.field, ""))


@dataclass(frozen=True)
class SubstringAny:
    """Keep rows where any of ``fields`` contains the param value."""

    param: str
    fields: tuple[str, ...]

    def matches(self, row: dict[str, Any], value: Any) -> bool:
        return any(str(value) in str(row.get(f, "")) for f in self.fields)


@dataclass(frozen=True)
class Equals:
    """Keep rows where ``row[field] == value`` (with int-as-str fallback)."""

    param: str
    field: str

    def matches(self, row: dict[str, Any], value: Any) -> bool:
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value) == str(row.get(self.field))
        return row.get(self.field) == value


@dataclass(frozen=True)
class TrueFlag:
    """Boolean flag: when True, keep only rows where ``row[field] == 'true'``."""

    param: str
    field: str

    def matches(self, row: dict[str, Any], value: Any) -> bool:
        return row.get(self.field) == "true"


@dataclass(frozen=True)
class Truthy:
    """Boolean flag: when True, keep rows where ``row[field]`` is truthy."""

    param: str
    field: str

    def matches(self, row: dict[str, Any], value: Any) -> bool:
        return bool(row.get(self.field))


Predicate = Substring | SubstringAny | Equals | TrueFlag | Truthy


# ---- Submenu descriptor ---------------------------------------------------


@dataclass(frozen=True)
class Submenu:
    """Describes one RouterOS REST submenu and the MCP tools to expose for it."""

    path: str
    """RouterOS REST path, e.g. ``ip/firewall/filter``."""

    schema: type[RouterOSSchema]
    """Pydantic schema for the resource fields and their wire aliases."""

    id_param: str
    """MCP parameter name for the entity identifier (e.g. ``rule_id``, ``name``)."""

    singular: str
    """Singular phrase for docstrings, e.g. ``filter rule``."""

    plural: str
    """Plural phrase for docstrings, e.g. ``filter rules``."""

    tool_names: dict[str, str] = field(default_factory=dict)
    """Operation -> full MCP tool name. Ops omitted are not exposed.
    Valid keys: list, get, create, update, remove, enable, disable, move."""

    list_filters: tuple[Predicate, ...] = ()

    lookup_key: str | None = None
    """If set, update/remove/enable/disable/get resolve ``.id`` via this row
    field, matching ``id_param`` value against ``row[lookup_key]``."""

    update_name_field: str | None = None
    """Schema field that ``new_name`` maps to in update tool. Use when
    ``lookup_key`` rebinds the entity ID and the schema field is also the name
    (RouterOS rename: same field gets the new value)."""

    create_only_fields: tuple[str, ...] = ()
    """Schema fields that should appear only on create, not on update."""

    extra_excluded: tuple[str, ...] = ()
    """Schema fields suppressed from both create and update signatures."""


# ---- Public API -----------------------------------------------------------


def build_submenu_tools(
    submenu: Submenu,
) -> dict[str, tuple[Callable[..., Any], dict[str, Any]]]:
    """Return ``{tool_name: (async_fn, annotations)}`` for all ops on a submenu.

    Used directly by tests; ``register_submenu`` is the production path.
    """
    impls: dict[str, tuple[Callable[..., Any], dict[str, Any]]] = {}
    ops = {
        "list": (_make_list, READ),
        "get": (_make_get, READ),
        "create": (_make_create, WRITE),
        "update": (_make_update, WRITE),
        "remove": (_make_remove, DESTRUCTIVE),
        "enable": (lambda s: _make_toggle(s, enable=True), WRITE),
        "disable": (lambda s: _make_toggle(s, enable=False), WRITE),
        "move": (_make_move, WRITE),
    }
    for op, (builder, tool_annotations) in ops.items():
        if op in submenu.tool_names:
            impls[submenu.tool_names[op]] = (builder(submenu), tool_annotations)
    return impls


def register_submenu(mcp: FastMCP, submenu: Submenu) -> None:
    """Register all operations on this submenu as MCP tools on ``mcp``."""
    for name, (fn, tool_annotations) in build_submenu_tools(submenu).items():
        mcp.tool(fn, name=name, annotations=tool_annotations)


# ---- Synthesizers ---------------------------------------------------------


def _make_list(submenu: Submenu) -> Callable[..., Any]:
    filters = submenu.list_filters

    async def list_impl(**kwargs: Any) -> list[dict[str, Any]]:
        ctx = kwargs.pop("ctx")
        manager = get_manager(ctx)
        rows = await manager.get_list(submenu.path)
        for pred in filters:
            value = kwargs.get(pred.param)
            if value is None or value is False:
                continue
            rows = [r for r in rows if pred.matches(r, value)]
        return rows

    params: list[inspect.Parameter] = []
    annotations: dict[str, Any] = {}
    for pred in filters:
        if isinstance(pred, TrueFlag | Truthy):
            ann: Any = bool
            default: Any = False
        elif isinstance(pred, Equals):
            ann = int | str | None
            default = None
        else:
            ann = str | None
            default = None
        params.append(_kw(pred.param, ann, default))
        annotations[pred.param] = ann

    params.append(_ctx_param())
    annotations["ctx"] = Context
    annotations["return"] = list[dict[str, Any]]

    _finalize(
        list_impl,
        submenu.tool_names["list"],
        f"List {submenu.plural}.",
        params,
        annotations,
        list[dict[str, Any]],
    )
    return list_impl


def _make_get(submenu: Submenu) -> Callable[..., Any]:
    async def get_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        identifier = kwargs.pop(submenu.id_param)
        manager = get_manager(ctx)
        if submenu.lookup_key is not None:
            for row in await manager.get_list(submenu.path):
                if row.get(submenu.lookup_key) == identifier:
                    return row
            raise MikrotikNotFound(submenu.path, identifier)
        return await manager.get_one(submenu.path, identifier)

    params = [_kw(submenu.id_param, str, inspect.Parameter.empty), _ctx_param()]
    annotations = {submenu.id_param: str, "ctx": Context, "return": dict[str, Any]}
    _finalize(
        get_impl,
        submenu.tool_names["get"],
        f"Get one {submenu.singular} by {submenu.id_param}.",
        params,
        annotations,
        dict[str, Any],
    )
    return get_impl


def _make_create(submenu: Submenu) -> Callable[..., Any]:
    schema = submenu.schema
    excluded = set(submenu.extra_excluded)
    fields_to_use = {
        name: info
        for name, info in schema.model_fields.items()
        if name not in excluded
    }

    async def create_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        manager = get_manager(ctx)
        values = {k: v for k, v in kwargs.items() if k in schema.model_fields}
        instance = schema(**values)
        payload = instance.to_router_os()
        result = await manager.put(submenu.path, json=payload)
        return {
            "created": True,
            "id": result.get(".id") if isinstance(result, dict) else None,
        }

    params: list[inspect.Parameter] = []
    annotations: dict[str, Any] = {}
    for name, info in fields_to_use.items():
        ann = info.annotation if info.annotation is not None else Any
        default = inspect.Parameter.empty if info.is_required() else info.default
        params.append(_kw(name, ann, default))
        annotations[name] = ann

    params.append(_ctx_param())
    annotations["ctx"] = Context
    annotations["return"] = dict[str, Any]

    _finalize(
        create_impl,
        submenu.tool_names["create"],
        f"Create a {submenu.singular}.",
        params,
        annotations,
        dict[str, Any],
    )
    return create_impl


def _make_update(submenu: Submenu) -> Callable[..., Any]:
    schema = submenu.schema
    excluded = set(submenu.extra_excluded) | set(submenu.create_only_fields)
    rename_field = submenu.update_name_field
    has_rename = rename_field is not None
    fields_to_use = {
        name: info
        for name, info in schema.model_fields.items()
        if name not in excluded and name != rename_field
    }

    async def update_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        identifier = kwargs.pop(submenu.id_param)
        manager = get_manager(ctx)
        entity_id = await _resolve_id(manager, submenu, identifier)

        values: dict[str, Any] = {}
        for k, v in kwargs.items():
            if v is None:
                continue
            if has_rename and k == "new_name":
                values[rename_field] = v  # type: ignore[index]
            elif k in schema.model_fields:
                values[k] = v
        if not values:
            raise ValueError("At least one update field must be provided")
        payload = _payload_from_partial(schema, values)
        await manager.patch(f"{submenu.path}/{entity_id}", json=payload)
        return {"updated": True, "id": entity_id}

    params: list[inspect.Parameter] = [
        _kw(submenu.id_param, str, inspect.Parameter.empty),
    ]
    annotations: dict[str, Any] = {submenu.id_param: str}

    if has_rename:
        params.append(_kw("new_name", str | None, None))
        annotations["new_name"] = str | None

    for name, info in fields_to_use.items():
        ann = info.annotation if info.annotation is not None else Any
        ann = _as_optional(ann)
        params.append(_kw(name, ann, None))
        annotations[name] = ann

    params.append(_ctx_param())
    annotations["ctx"] = Context
    annotations["return"] = dict[str, Any]

    _finalize(
        update_impl,
        submenu.tool_names["update"],
        f"Update an existing {submenu.singular}.",
        params,
        annotations,
        dict[str, Any],
    )
    return update_impl


def _make_remove(submenu: Submenu) -> Callable[..., Any]:
    async def remove_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        identifier = kwargs.pop(submenu.id_param)
        manager = get_manager(ctx)
        entity_id = await _resolve_id(manager, submenu, identifier)
        await manager.delete(f"{submenu.path}/{entity_id}")
        return {"removed": True, "id": entity_id}

    params = [_kw(submenu.id_param, str, inspect.Parameter.empty), _ctx_param()]
    annotations = {submenu.id_param: str, "ctx": Context, "return": dict[str, Any]}
    _finalize(
        remove_impl,
        submenu.tool_names["remove"],
        f"Remove a {submenu.singular}.",
        params,
        annotations,
        dict[str, Any],
    )
    return remove_impl


def _make_toggle(submenu: Submenu, *, enable: bool) -> Callable[..., Any]:
    verb = "enable" if enable else "disable"
    wire = "false" if enable else "true"

    async def toggle_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        identifier = kwargs.pop(submenu.id_param)
        manager = get_manager(ctx)
        entity_id = await _resolve_id(manager, submenu, identifier)
        await manager.patch(
            f"{submenu.path}/{entity_id}", json={"disabled": wire}
        )
        return {f"{verb}d": True, "id": entity_id}

    params = [_kw(submenu.id_param, str, inspect.Parameter.empty), _ctx_param()]
    annotations = {submenu.id_param: str, "ctx": Context, "return": dict[str, Any]}
    _finalize(
        toggle_impl,
        submenu.tool_names[verb],
        f"{verb.capitalize()} a {submenu.singular}.",
        params,
        annotations,
        dict[str, Any],
    )
    return toggle_impl


def _make_move(submenu: Submenu) -> Callable[..., Any]:
    async def move_impl(**kwargs: Any) -> dict[str, Any]:
        ctx = kwargs.pop("ctx")
        identifier = kwargs.pop(submenu.id_param)
        destination = kwargs.pop("destination")
        manager = get_manager(ctx)
        entity_id = await _resolve_id(manager, submenu, identifier)
        await manager.patch(
            f"{submenu.path}/{entity_id}", json={"move": str(destination)}
        )
        return {"moved": True, "id": entity_id, "destination": destination}

    params = [
        _kw(submenu.id_param, str, inspect.Parameter.empty),
        _kw("destination", int, inspect.Parameter.empty),
        _ctx_param(),
    ]
    annotations: dict[str, Any] = {
        submenu.id_param: str,
        "destination": int,
        "ctx": Context,
        "return": dict[str, Any],
    }
    _finalize(
        move_impl,
        submenu.tool_names["move"],
        f"Move a {submenu.singular} to a different position.",
        params,
        annotations,
        dict[str, Any],
    )
    return move_impl


# ---- Helpers --------------------------------------------------------------


async def _resolve_id(
    manager: MikrotikConnectionManager, submenu: Submenu, identifier: str
) -> str:
    """Resolve a row ``.id`` from a caller-supplied identifier.

    With ``lookup_key=None`` the identifier *is* the ``.id``. Otherwise we scan
    the submenu and return the ``.id`` of the row whose ``lookup_key`` matches.
    """
    if submenu.lookup_key is None:
        return identifier
    for row in await manager.get_list(submenu.path):
        if row.get(submenu.lookup_key) == identifier:
            row_id = row.get(".id")
            if row_id is None:
                raise MikrotikNotFound(submenu.path, identifier)
            return str(row_id)
    raise MikrotikNotFound(submenu.path, identifier)


def _kw(name: str, annotation: Any, default: Any) -> inspect.Parameter:
    return inspect.Parameter(
        name,
        inspect.Parameter.KEYWORD_ONLY,
        default=default,
        annotation=annotation,
    )


def _ctx_param() -> inspect.Parameter:
    return inspect.Parameter(
        "ctx",
        inspect.Parameter.KEYWORD_ONLY,
        default=CurrentContext(),
        annotation=Context,
    )


def _as_optional(annotation: Any) -> Any:
    """Return ``annotation | None`` unless ``annotation`` is already nullable."""
    origin = get_origin(annotation)
    if origin in (Union, UnionType) and type(None) in get_args(annotation):
        return annotation
    return annotation | None


def _finalize(
    fn: Callable[..., Any],
    name: str,
    doc: str,
    params: list[inspect.Parameter],
    annotations: dict[str, Any],
    return_ann: Any,
) -> None:
    fn.__signature__ = inspect.Signature(params, return_annotation=return_ann)  # type: ignore[attr-defined]
    fn.__name__ = name
    fn.__qualname__ = name
    fn.__doc__ = doc
    fn.__annotations__ = annotations


__all__ = [
    "Equals",
    "Predicate",
    "RouterOSSchema",
    "Submenu",
    "Substring",
    "SubstringAny",
    "TrueFlag",
    "Truthy",
    "build_submenu_tools",
    "get_manager",
    "register_submenu",
]
