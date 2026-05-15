from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.user_status import user_account_status_label_pt_v1


# ###################################################################################
# (1) CONTEXTO DE LISTAGEM DE UTILIZADORES
# ###################################################################################

def build_user_admin_list_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from appverbo.use_cases.users.list_users import execute_list_users_v1

    if actor_user_id is None:
        return {
            "all_users": [],
            "created_users": [],
            "active_created_users": [],
            "inactive_users": [],
            "pending_users": [],
            "recent_users": [],
            "superuser_users": [],
            "account_status_summary": [],
            "user_list_pagination": {
                "page": 1,
                "page_size": 5000,
                "total": 0,
                "has_next": False,
            },
            "entity_permissions": {
                "is_admin": False,
                "can_manage_all_entities": False,
                "allowed_entity_ids": set(),
                "selected_entity_id": None,
            },
        }

    list_result = execute_list_users_v1(
        session=session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email or ""),
        selected_entity_id=selected_entity_id,
        filters=filters,
    )

    return {
        "all_users": list_result.get("all_users", []),
        "created_users": list_result.get("created_users", []),
        "active_created_users": list_result.get("active_created_users", []),
        "inactive_users": list_result.get("inactive_users", []),
        "pending_users": list_result.get("pending_users", []),
        "recent_users": list_result.get("recent_users", []),
        "superuser_users": list_result.get("superuser_users", []),
        "account_status_summary": list_result.get("account_status_summary", []),
        "user_list_pagination": list_result.get("pagination", {}),
        "entity_permissions": list_result.get("entity_permissions", {}),
    }


def build_user_admin_page_payload_v1(
    user_admin_context: dict[str, Any] | None,
) -> dict[str, Any]:
    context = user_admin_context or {}
    recent_rows = list(context.get("recent_users") or [])

    return {
        "all_users": list(context.get("all_users", [])),
        "created_users": list(context.get("created_users", [])),
        "active_created_users": list(context.get("active_created_users", [])),
        "inactive_users": list(context.get("inactive_users", [])),
        "pending_users": list(context.get("pending_users", [])),
        "superuser_users": list(context.get("superuser_users", [])),
        "account_status_summary": list(context.get("account_status_summary", [])),
        "user_list_pagination": dict(context.get("user_list_pagination", {})),
        "recent_users": [
            {
                "id": row.get("id"),
                "full_name": row.get("full_name", ""),
                "login_email": row.get("login_email", ""),
                "account_status": row.get("account_status", ""),
                "account_status_label": row.get(
                    "account_status_label",
                    user_account_status_label_pt_v1(row.get("account_status")),
                ),
                "created_at": row.get("created_at", "-"),
            }
            for row in recent_rows
        ],
    }


# ###################################################################################
# (2) CONTEXTO DE EDICAO DE UTILIZADOR
# ###################################################################################

def build_user_admin_edit_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None,
) -> dict[str, Any]:
    from appverbo.use_cases.users.get_user_edit import (
        execute_get_user_edit_v1,
        get_user_edit_defaults_v1,
    )

    if user_edit_id is None or actor_user_id is None:
        return {
            "user_edit_data": get_user_edit_defaults_v1(),
        }

    permissions = get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email or ""),
        selected_entity_id,
    )

    if permissions.get("can_manage_all_entities"):
        allowed_entity_ids = None
    else:
        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
            if str(raw_id).strip().isdigit()
        }

    return {
        "user_edit_data": execute_get_user_edit_v1(
            session=session,
            user_id=user_edit_id,
            allowed_entity_ids=allowed_entity_ids,
        )
    }


# ###################################################################################
# (3) CONTEXTO COMPLETO DO SUBPROCESSO UTILIZADOR
# ###################################################################################

def build_user_admin_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    list_context = build_user_admin_list_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        filters=filters,
    )

    edit_context = build_user_admin_edit_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        user_edit_id=user_edit_id,
    )

    return {
        **list_context,
        **edit_context,
    }
