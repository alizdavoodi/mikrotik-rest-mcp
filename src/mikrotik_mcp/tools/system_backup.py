from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.dependencies import CurrentContext
from pydantic import BaseModel

from ..app import DESTRUCTIVE, READ, WRITE
from . import get_manager


class BackupCreate(BaseModel):
    name: str | None = None
    dont_encrypt: bool = False
    include_password: bool = True
    comment: str | None = None


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="mikrotik_create_backup", annotations=WRITE)
    async def create_backup(
        name: str | None = None,
        dont_encrypt: bool = False,
        include_password: bool = True,
        comment: str | None = None,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """Create a RouterOS system backup."""
        manager = get_manager(ctx)
        payload = BackupCreate(
            name=name,
            dont_encrypt=dont_encrypt,
            include_password=include_password,
            comment=comment,
        ).model_dump(exclude_none=True)
        if "dont_encrypt" in payload:
            payload["dont-encrypt"] = str(payload.pop("dont_encrypt")).lower()
        if "include_password" in payload:
            payload["password"] = str(payload.pop("include_password")).lower()
        await manager.post("system/backup/save", json=payload)
        return {"created": True, "name": name}

    @mcp.tool(name="mikrotik_list_backups", annotations=READ)
    async def list_backups(
        name_filter: str | None = None,
        include_exports: bool = False,
        ctx: Context = CurrentContext(),
    ) -> list[dict[str, Any]]:
        """List backup and optional export files from RouterOS."""
        manager = get_manager(ctx)
        rows = await manager.get("file") or []
        filtered = []
        for row in rows:
            name = str(row.get("name", ""))
            is_backup = name.endswith(".backup")
            is_export = name.endswith(".rsc")
            if not is_backup and not (include_exports and is_export):
                continue
            if name_filter and name_filter not in name:
                continue
            filtered.append(row)
        return filtered

    @mcp.tool(name="mikrotik_download_file", annotations=READ)
    async def download_file(
        filename: str, file_type: str = "backup", ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Download file content as base64 text if available in API response."""
        manager = get_manager(ctx)
        rows = await manager.get("file", params={"name": filename}) or []
        if not rows:
            raise ValueError(f"File not found: {filename}")
        file_info = rows[0]
        content = file_info.get("contents") or file_info.get("content") or ""
        return {
            "filename": filename,
            "file_type": file_type,
            "content_base64": content,
            "metadata": file_info,
        }

    @mcp.tool(name="mikrotik_upload_file", annotations=WRITE)
    async def upload_file(
        filename: str, content_base64: str, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Upload base64 content as file contents via RouterOS file API."""
        manager = get_manager(ctx)
        await manager.post("file", json={"name": filename, "contents": content_base64})
        return {"uploaded": True, "filename": filename}

    @mcp.tool(name="mikrotik_restore_backup", annotations=DESTRUCTIVE)
    async def restore_backup(
        filename: str, password: str | None = None, ctx: Context = CurrentContext()
    ) -> dict[str, Any]:
        """Restore a RouterOS backup from file."""
        manager = get_manager(ctx)
        payload: dict[str, Any] = {"name": filename}
        if password:
            payload["password"] = password
        await manager.post("system/backup/load", json=payload)
        return {"restored": True, "filename": filename}
