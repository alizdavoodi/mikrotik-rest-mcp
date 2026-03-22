from __future__ import annotations

from mikrotik_rest_mcp.tools.system_backup import BackupCreate


class TestBackupCreate:
    def test_default_payload(self) -> None:
        model = BackupCreate()
        payload = model.model_dump(exclude_none=True)

        assert payload["dont_encrypt"] is False
        assert payload["include_password"] is True
        assert "name" not in payload
        assert "comment" not in payload

    def test_full_payload(self) -> None:
        model = BackupCreate(
            name="daily-backup",
            dont_encrypt=True,
            include_password=False,
            comment="Nightly snapshot",
        )
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "daily-backup"
        assert payload["dont_encrypt"] is True
        assert payload["include_password"] is False
        assert payload["comment"] == "Nightly snapshot"

    def test_exclude_none_keeps_boolean_defaults(self) -> None:
        model = BackupCreate(name="manual")
        payload = model.model_dump(exclude_none=True)

        assert payload["name"] == "manual"
        assert payload["dont_encrypt"] is False
        assert payload["include_password"] is True
