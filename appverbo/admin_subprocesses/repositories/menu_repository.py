
from __future__ import annotations

from typing import Any

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository


class MenuAdminRepository(BaseAdminSubprocessRepository):

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from appverbo.menu_settings import get_sidebar_menu_settings

        raw_rows = get_sidebar_menu_settings(session)
        result: list[dict[str, Any]] = []

        ctx = context or {}
        entity_number = ctx.get("entity_number")
        entity_number_display = str(entity_number) if entity_number is not None else "-"

        for raw_row in raw_rows:
            row = dict(raw_row)
            is_active = bool(row.get("is_active"))
            is_deleted = bool(row.get("is_deleted"))

            if is_active and not is_deleted:
                row["status"] = "ativo"
                row["status_label"] = "Ativo"
            else:
                row["status"] = "inativo"
                row["status_label"] = "Inativo"

            row["entity_number"] = entity_number_display

            result.append(row)

        return result

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_key = str(edit_key or "").strip().lower()

        if not clean_key:
            return None

        for row in self.list_rows(session, context):
            if str(row.get("key") or "").strip().lower() == clean_key:
                return dict(row)

        return None
