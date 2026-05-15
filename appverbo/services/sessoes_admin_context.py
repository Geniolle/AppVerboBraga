from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.use_cases.sessoes.get_session_edit import (
    execute_get_session_edit_v1,
    get_session_edit_defaults_v1,
)
from appverbo.use_cases.sessoes.list_sessions import execute_list_sessions_v1


# ###################################################################################
# (1) CONTEXTO DE LISTAGEM DE SESSOES
# ###################################################################################

def build_sessoes_admin_list_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if actor_user_id is None:
        return {
            "sessions": [],
            "all_sessions": [],
            "active_sessions": [],
            "inactive_sessions": [],
            "pending_sessions": [],
            "blocked_sessions": [],
            "recent_sessions": [],
            "session_list_pagination": {
                "page": 1,
                "page_size": 5000,
                "total": 0,
                "has_next": False,
            },
            "session_permissions": {
                "is_admin": False,
                "can_manage_all_entities": False,
                "allowed_entity_ids": set(),
                "selected_entity_id": None,
            },
            "current_user_can_manage_all_entities": False,
            "sidebar_sections_tab": "sessoes",
        }

    list_result = execute_list_sessions_v1(
        session=session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email or ""),
        selected_entity_id=selected_entity_id,
        filters=filters,
    )
    session_permissions = dict(list_result.get("session_permissions") or {})

    return {
        "sessions": list(list_result.get("sessions", [])),
        "all_sessions": list(list_result.get("all_sessions", [])),
        "active_sessions": list(list_result.get("active_sessions", [])),
        "inactive_sessions": list(list_result.get("inactive_sessions", [])),
        "pending_sessions": list(list_result.get("pending_sessions", [])),
        "blocked_sessions": list(list_result.get("blocked_sessions", [])),
        "recent_sessions": list(list_result.get("recent_sessions", [])),
        "session_list_pagination": dict(list_result.get("session_list_pagination", {})),
        "session_permissions": session_permissions,
        "current_user_can_manage_all_entities": bool(
            session_permissions.get("can_manage_all_entities")
        ),
        "sidebar_sections_tab": "sessoes",
    }


# ###################################################################################
# (2) CONTEXTO DE EDICAO DE SESSAO
# ###################################################################################

def build_sessoes_admin_edit_context_v1(
    *,
    session: Session,
    session_edit_key: str,
) -> dict[str, Any]:
    clean_session_edit_key = str(session_edit_key or "").strip().lower()

    if not clean_session_edit_key:
        return {
            "session_edit_data": get_session_edit_defaults_v1(),
        }

    return {
        "session_edit_data": execute_get_session_edit_v1(
            session=session,
            session_key=clean_session_edit_key,
        ),
    }


# ###################################################################################
# (3) CONTEXTO COMPLETO DO SUBPROCESSO SESSOES
# ###################################################################################

def build_sessoes_admin_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    session_edit_key: str = "",
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    list_context = build_sessoes_admin_list_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        filters=filters,
    )

    edit_context = build_sessoes_admin_edit_context_v1(
        session=session,
        session_edit_key=session_edit_key,
    )

    return {
        **list_context,
        **edit_context,
    }


def build_sessoes_admin_page_payload_v1(
    sessoes_admin_context: dict[str, Any] | None,
) -> dict[str, Any]:
    context = sessoes_admin_context or {}

    return {
        "sessions": list(context.get("sessions", [])),
        "all_sessions": list(context.get("all_sessions", [])),
        "active_sessions": list(context.get("active_sessions", [])),
        "inactive_sessions": list(context.get("inactive_sessions", [])),
        "pending_sessions": list(context.get("pending_sessions", [])),
        "blocked_sessions": list(context.get("blocked_sessions", [])),
        "recent_sessions": list(context.get("recent_sessions", [])),
        "session_edit_data": dict(context.get("session_edit_data", {})),
        "session_permissions": dict(context.get("session_permissions", {})),
        "session_list_pagination": dict(context.get("session_list_pagination", {})),
        "sidebar_sections_tab": str(context.get("sidebar_sections_tab") or "sessoes"),
        "active_sidebar_sections": list(context.get("active_sessions", [])),
        "inactive_sidebar_sections": list(context.get("inactive_sessions", [])),
        "sidebar_section_edit_data": dict(context.get("session_edit_data", {})),
        "current_user_can_manage_all_entities": bool(
            context.get("current_user_can_manage_all_entities")
        ),
    }
