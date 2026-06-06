from __future__ import annotations

from typing import Any


# ###################################################################################
# (1) REGRAS CENTRALIZADAS DE ACESSO POR LINHA
# ###################################################################################

DEFAULT_OWNER_ONLY_EDIT_SUBPROCESS_KEYS_V1 = frozenset(
    {
        "sessoes",
    }
)


def _normalize_subprocess_key_v1(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_entity_scope_v1(value: object) -> str:
    clean_value = str(value or "").strip().lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return ""


def _is_default_scope_label_v1(value: object) -> bool:
    return str(value or "").strip().lower() == "default"


def is_default_scope_row_v1(row: dict[str, Any] | None) -> bool:
    clean_row = dict(row or {})
    clean_scope_origin = str(clean_row.get("entity_scope_origin") or "").strip().lower()

    if clean_scope_origin == "default":
        return True

    if clean_scope_origin == "entity":
        return False

    if _is_default_scope_label_v1(clean_row.get("entity_internal_number")):
        return True

    if _is_default_scope_label_v1(clean_row.get("entity_name")):
        return True

    return False


def build_admin_subprocess_row_action_access_v1(
    *,
    subprocess_key: object,
    row: dict[str, Any] | None,
    current_entity_scope: object = "",
) -> dict[str, Any]:
    clean_subprocess_key = _normalize_subprocess_key_v1(subprocess_key)
    clean_entity_scope = _normalize_entity_scope_v1(current_entity_scope)

    can_edit = True
    edit_disabled_reason = ""
    can_move = True
    move_disabled_reason = ""
    can_delete = True
    delete_disabled_reason = ""

    if (
        clean_subprocess_key in DEFAULT_OWNER_ONLY_EDIT_SUBPROCESS_KEYS_V1
        and clean_entity_scope == "legado"
        and is_default_scope_row_v1(row)
    ):
        can_edit = False
        can_move = False
        can_delete = False
        edit_disabled_reason = "Registos Default só podem ser editados no sistema Owner."
        move_disabled_reason = "Registos Default só podem ser reordenados no sistema Owner."
        delete_disabled_reason = "Registos Default só podem ser eliminados no sistema Owner."

    return {
        "can_edit": can_edit,
        "edit_disabled_reason": edit_disabled_reason,
        "can_move": can_move,
        "move_disabled_reason": move_disabled_reason,
        "can_delete": can_delete,
        "delete_disabled_reason": delete_disabled_reason,
    }


def decorate_admin_subprocess_row_action_access_v1(
    *,
    subprocess_key: object,
    row: dict[str, Any] | None,
    current_entity_scope: object = "",
) -> dict[str, Any]:
    clean_row = dict(row or {})
    clean_row.update(
        build_admin_subprocess_row_action_access_v1(
            subprocess_key=subprocess_key,
            row=clean_row,
            current_entity_scope=current_entity_scope,
        )
    )
    return clean_row


__all__ = [
    "build_admin_subprocess_row_action_access_v1",
    "decorate_admin_subprocess_row_action_access_v1",
    "is_default_scope_row_v1",
]
