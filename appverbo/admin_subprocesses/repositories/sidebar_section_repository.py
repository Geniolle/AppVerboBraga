
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository


class SidebarSectionAdminRepository(BaseAdminSubprocessRepository):
    menu_key = "administrativo"

    def _normalize_sections(self, raw_sections: object) -> list[dict[str, Any]]:
        from appverbo.menu_settings import normalize_sidebar_sections

        return [dict(row) for row in normalize_sidebar_sections(raw_sections)]

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from appverbo.menu_settings import MENU_CONFIG_SIDEBAR_SECTIONS_KEY

        row = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": self.menu_key},
        ).fetchone()

        if not row:
            return []

        raw_config = row[0]

        if isinstance(raw_config, dict):
            menu_config = raw_config
        else:
            menu_config = json.loads(raw_config or "{}")

        return self._normalize_sections(menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) or [])

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip().lower()

        if not clean_edit_key:
            return None

        for row in self.list_rows(session, context):
            current_key = str(row.get("key") or "").strip().lower()

            if current_key == clean_edit_key:
                return dict(row)

        return None
