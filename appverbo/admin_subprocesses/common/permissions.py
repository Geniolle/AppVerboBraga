from __future__ import annotations

from typing import Any

from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions


# ###################################################################################
# (1) VALIDACAO DE ADMINISTRADOR
# ###################################################################################

def is_actor_admin_v1(session: Any, actor_user: dict[str, Any] | None) -> bool:
    if not actor_user:
        return False

    return bool(
        is_admin_user(
            session,
            int(actor_user["id"]),
            str(actor_user["login_email"]),
        )
    )


def build_admin_permission_error_v1(action_label: str) -> str:
    clean_action_label = str(action_label or "executar esta a\u00e7\u00e3o").strip()
    return f"Apenas administradores podem {clean_action_label}."


# ###################################################################################
# (2) PERMISSOES POR ENTIDADE
# ###################################################################################

def get_actor_entity_permissions_v1(
    session: Any,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
) -> dict[str, Any]:
    return get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )


def get_allowed_entity_ids_set_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def can_manage_entity_id_v1(
    permissions: dict[str, Any],
    entity_id: int | str | None,
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True

    if entity_id is None:
        return False

    try:
        parsed_entity_id = int(entity_id)
    except (TypeError, ValueError):
        return False

    return parsed_entity_id in get_allowed_entity_ids_set_v1(permissions)