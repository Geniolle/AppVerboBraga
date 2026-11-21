from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from appgenesis.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository

FUNCTIONS_MENU_CONFIG_KEY = "authorization_functions"
FUNCTIONS_SCOPE_LABELS = {"all": "Default", "owner": "Owner", "legado": "Legado"}
FUNCTIONS_STATUS_LABELS = {"ativo": "Ativo", "inativo": "Inativo"}


def _normalize_status(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"inativo", "inactive", "0", "false", "off", "no", "nao"}:
        return "inativo"
    return "ativo"


def _normalize_scope_mode(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    return clean_value if clean_value in FUNCTIONS_SCOPE_LABELS else "all"


def build_function_key(label: Any) -> str:
    clean = str(label or "").strip().lower()
    clean = re.sub(r"[^a-z0-9]+", "_", clean).strip("_")
    return clean or "funcao"


def _load_functions(session: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'administrativo'
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return {}, []
    raw_config = row[0]
    menu_config = raw_config if isinstance(raw_config, dict) else json.loads(raw_config or "{}")
    raw_items = menu_config.get(FUNCTIONS_MENU_CONFIG_KEY) or []
    items = [dict(item) for item in raw_items if isinstance(item, dict)]
    return menu_config, items


def _store_functions(session: Any, menu_config: dict[str, Any], items: list[dict[str, Any]]) -> None:
    menu_config[FUNCTIONS_MENU_CONFIG_KEY] = items
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = 'administrativo'
            """
        ),
        {"menu_config": json.dumps(menu_config, ensure_ascii=False)},
    )


class FunctionsAdminRepository(BaseAdminSubprocessRepository):
    def _build_row(self, item: dict[str, Any]) -> dict[str, Any]:
        status_value = _normalize_status(item.get("status"))
        scope_mode = _normalize_scope_mode(item.get("visibility_scope_mode"))
        label = str(item.get("label") or "").strip()
        return {
            "key": str(item.get("key") or ""),
            "label": label,
            "status": status_value,
            "status_label": FUNCTIONS_STATUS_LABELS[status_value],
            "visibility_scope_mode": scope_mode,
            "visibility_scope_label": FUNCTIONS_SCOPE_LABELS[scope_mode],
            "entity_number": str(item.get("entity_number") or ""),
            "created_at": str(item.get("created_at") or ""),
            "values": {
                "label": label,
                "visibility_scope_mode": scope_mode,
                "status": status_value,
                "entity_number": str(item.get("entity_number") or ""),
            },
        }

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _menu_config, items = _load_functions(session)
        return [self._build_row(item) for item in items if str(item.get("key") or "").strip()]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_key = str(edit_key or "").strip().lower()
        for row in self.list_rows(session, context):
            if str(row.get("key") or "").lower() == clean_key:
                return row
        return None

    def save_row(
        self,
        session: Any,
        payload: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        edit_key: str = "",
    ) -> tuple[bool, str, str]:
        label = str(payload.get("label") or "").strip()
        if not label:
            return False, "label_required", ""

        menu_config, items = _load_functions(session)
        clean_edit_key = str(edit_key or "").strip().lower()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        scope_mode = _normalize_scope_mode(payload.get("visibility_scope_mode"))
        status_value = _normalize_status(payload.get("status"))
        entity_number = str((context or {}).get("entity_number") or "").strip()

        if clean_edit_key:
            target = next((item for item in items if str(item.get("key") or "").lower() == clean_edit_key), None)
            if target is None:
                return False, "not_found", ""
            target.update(
                {
                    "label": label,
                    "visibility_scope_mode": scope_mode,
                    "status": status_value,
                }
            )
            saved_key = str(target.get("key") or clean_edit_key)
        else:
            saved_key = build_function_key(label)
            existing_keys = {str(item.get("key") or "").lower() for item in items}
            base_key = saved_key
            suffix = 2
            while saved_key in existing_keys:
                saved_key = f"{base_key}_{suffix}"
                suffix += 1
            items.append(
                {
                    "key": saved_key,
                    "label": label,
                    "visibility_scope_mode": scope_mode,
                    "status": status_value,
                    "entity_number": entity_number,
                    "created_at": now,
                }
            )

        _store_functions(session, menu_config, items)
        return True, "saved", saved_key

    def delete_row(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        clean_key = str(edit_key or "").strip().lower()
        menu_config, items = _load_functions(session)
        target = next((item for item in items if str(item.get("key") or "").lower() == clean_key), None)
        if target is None:
            return False, "not_found"
        if _normalize_status(target.get("status")) == "ativo":
            return False, "active_function"
        items = [item for item in items if str(item.get("key") or "").lower() != clean_key]
        _store_functions(session, menu_config, items)
        return True, "deleted"


__all__ = [
    "FunctionsAdminRepository",
    "build_function_key",
]
