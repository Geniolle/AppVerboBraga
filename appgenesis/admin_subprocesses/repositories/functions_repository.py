from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from appgenesis.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appgenesis.services.user_system import (
    ALLOWED_USER_SYSTEM_TYPES,
    get_user_system_type_label_v1,
    normalize_user_system_type_v1,
)

from appgenesis.services.entity_menu_data import get_entity_menu_data, set_entity_menu_data

FUNCTIONS_MENU_CONFIG_KEY = "authorization_functions"
FUNCTIONS_MENU_KEY = "administrativo"
ALL_PROFILES_VALUE = "__all__"
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


def normalize_profile_keys(raw_value: Any) -> list[str]:
    raw_items = [raw_value] if isinstance(raw_value, str) else list(raw_value or [])
    keys: list[str] = []
    for item in raw_items:
        clean_key = str(item or "").strip().lower()
        if clean_key:
            keys.append(clean_key)
    return keys


def list_active_profile_options(
    session: Any,
    auth_config: Any,
    *,
    user_id: Any,
    entity_number: str,
) -> list[tuple[str, str]]:
    # Opcoes do campo Perfil de autorizacao: so perfis ativos da aba Perfil de autorizacao.
    from appgenesis.admin_subprocesses.repositories.auth_profile_repository import (
        AuthorizationProfileAdminRepository,
    )

    rows = AuthorizationProfileAdminRepository(auth_config).list_rows(
        session,
        context={"user_id": user_id, "entity_number": entity_number},
    )
    return [
        (str(row.get("key") or ""), str(row.get("label") or ""))
        for row in rows
        if row.get("key") and str(row.get("status") or "") == "ativo"
    ]


def _entity_id_from_context(context: dict[str, Any] | None) -> int | None:
    raw_value = (context or {}).get("entity_id")
    try:
        return int(raw_value) if raw_value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _load_functions(session: Any, context: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    # Dados por entidade (entity_menu_data): sem entidade nao ha funcoes.
    entity_id = _entity_id_from_context(context)
    if entity_id is None:
        return {}, []
    raw_items = get_entity_menu_data(
        session, entity_id, FUNCTIONS_MENU_KEY, FUNCTIONS_MENU_CONFIG_KEY, []
    )
    items = [dict(item) for item in (raw_items or []) if isinstance(item, dict)]
    return {}, items


def _store_functions(
    session: Any,
    context: dict[str, Any] | None,
    menu_config: dict[str, Any],
    items: list[dict[str, Any]],
) -> bool:
    entity_id = _entity_id_from_context(context)
    if entity_id is None:
        return False
    # Funcoes so existem com o menu Administrativo (linha compartilhada) no BD.
    menu_exists = session.execute(
        text("SELECT 1 FROM sidebar_menu_settings WHERE lower(trim(menu_key)) = 'administrativo' LIMIT 1")
    ).fetchone()
    if menu_exists is None:
        return False
    set_entity_menu_data(
        session, entity_id, FUNCTIONS_MENU_KEY, FUNCTIONS_MENU_CONFIG_KEY, items
    )
    return True


class FunctionsAdminRepository(BaseAdminSubprocessRepository):
    def _build_row(self, item: dict[str, Any]) -> dict[str, Any]:
        status_value = _normalize_status(item.get("status"))
        scope_mode = _normalize_scope_mode(item.get("visibility_scope_mode"))
        label = str(item.get("label") or "").strip()
        profile_keys = normalize_profile_keys(item.get("authorization_profiles"))
        system_profile = normalize_user_system_type_v1(item.get("system_profile"))
        return {
            "key": str(item.get("key") or ""),
            "label": label,
            "system_profile": system_profile,
            "system_profile_label": get_user_system_type_label_v1(system_profile),
            "status": status_value,
            "status_label": FUNCTIONS_STATUS_LABELS[status_value],
            "visibility_scope_mode": scope_mode,
            "visibility_scope_label": FUNCTIONS_SCOPE_LABELS[scope_mode],
            "entity_number": str(item.get("entity_number") or ""),
            "created_at": str(item.get("created_at") or ""),
            "authorization_profiles": profile_keys,
            "values": {
                "label": label,
                "visibility_scope_mode": scope_mode,
                "status": status_value,
                "entity_number": str(item.get("entity_number") or ""),
                "authorization_profiles": profile_keys,
            },
        }

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _menu_config, items = _load_functions(session, context)
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

        system_profile = str(payload.get("system_profile") or "").strip().lower()
        if system_profile not in ALLOWED_USER_SYSTEM_TYPES:
            return False, "system_profile_required", ""
        # Admin de entidade (nao owner) so gere funcoes de membros: nao pode dar-se mais acesso.
        member_profiles_only = bool((context or {}).get("member_profiles_only"))
        if member_profiles_only and system_profile != "default":
            return False, "admin_profile_owner_only", ""

        profile_keys = normalize_profile_keys(payload.get("authorization_profiles"))
        if not profile_keys:
            return False, "profile_required", ""
        if ALL_PROFILES_VALUE in profile_keys:
            # "Todos os perfis" e exclusivo: guarda o marcador, que vale para todos os perfis ativos.
            if len(profile_keys) > 1:
                return False, "profile_all_exclusive", ""
            profile_keys = [ALL_PROFILES_VALUE]
        else:
            if len(set(profile_keys)) != len(profile_keys):
                return False, "profile_duplicate", ""
            allowed_keys = {str(key).strip().lower() for key in (context or {}).get("allowed_profile_keys") or []}
            if any(key not in allowed_keys for key in profile_keys):
                return False, "profile_not_found", ""

        menu_config, items = _load_functions(session, context)
        clean_edit_key = str(edit_key or "").strip().lower()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        scope_mode = _normalize_scope_mode(payload.get("visibility_scope_mode"))
        status_value = _normalize_status(payload.get("status"))
        entity_number = str((context or {}).get("entity_number") or "").strip()

        if clean_edit_key:
            target = next((item for item in items if str(item.get("key") or "").lower() == clean_edit_key), None)
            if target is None:
                return False, "not_found", ""
            if member_profiles_only and normalize_user_system_type_v1(target.get("system_profile")) != "default":
                return False, "admin_profile_owner_only", ""
            target.update(
                {
                    "label": label,
                    "system_profile": system_profile,
                    "visibility_scope_mode": scope_mode,
                    "status": status_value,
                    "authorization_profiles": profile_keys,
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
                    "system_profile": system_profile,
                    "visibility_scope_mode": scope_mode,
                    "status": status_value,
                    "entity_number": entity_number,
                    "authorization_profiles": profile_keys,
                    "created_at": now,
                }
            )

        if not _store_functions(session, context, menu_config, items):
            return False, "menu_not_found", ""
        return True, "saved", saved_key

    def delete_row(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        clean_key = str(edit_key or "").strip().lower()
        menu_config, items = _load_functions(session, context)
        target = next((item for item in items if str(item.get("key") or "").lower() == clean_key), None)
        if target is None:
            return False, "not_found"
        if (context or {}).get("member_profiles_only") and normalize_user_system_type_v1(
            target.get("system_profile")
        ) != "default":
            return False, "admin_profile_owner_only"
        if _normalize_status(target.get("status")) == "ativo":
            return False, "active_function"
        items = [item for item in items if str(item.get("key") or "").lower() != clean_key]
        if not _store_functions(session, context, menu_config, items):
            return False, "menu_not_found"
        return True, "deleted"


__all__ = [
    "FunctionsAdminRepository",
    "build_function_key",
]
