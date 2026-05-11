from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request

from appverbo.services.auth import is_admin_user
from appverbo.services.page import get_next_entity_internal_number, get_page_data
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import get_user_personal_data
from appverbo.services.session import get_current_user, get_session_entity_id


# ###################################################################################
# (1) MODELO DO CONTEXTO BASE DO ADMINISTRATIVO
# ###################################################################################

@dataclass(frozen=True)
class AdminBaseContext:
    current_user: dict[str, Any] | None
    selected_entity_id: int | None
    current_user_is_admin: bool
    entity_permissions: dict[str, Any]
    page_data: dict[str, Any]
    user_personal_data: dict[str, Any]
    next_entity_internal_number: int


# ###################################################################################
# (2) CONSTRUCAO DO CONTEXTO BASE
# ###################################################################################

def build_admin_base_context_v1(
    *,
    session: Any,
    request: Request,
    selected_entity_id: int | None = None,
) -> AdminBaseContext:
    current_user = get_current_user(request, session)

    if current_user is None:
        return AdminBaseContext(
            current_user=None,
            selected_entity_id=None,
            current_user_is_admin=False,
            entity_permissions={
                "is_admin": False,
                "can_manage_all_entities": False,
                "allowed_entity_ids": set(),
                "selected_entity_id": None,
            },
            page_data={},
            user_personal_data={},
            next_entity_internal_number=1,
        )

    resolved_selected_entity_id = (
        selected_entity_id
        if selected_entity_id is not None
        else get_session_entity_id(request)
    )

    current_user_is_admin = bool(
        is_admin_user(
            session,
            int(current_user["id"]),
            str(current_user["login_email"]),
        )
    )

    entity_permissions = get_user_entity_permissions(
        session,
        int(current_user["id"]),
        str(current_user["login_email"]),
        resolved_selected_entity_id,
    )

    page_data = get_page_data(
        session,
        actor_user_id=int(current_user["id"]),
        actor_login_email=str(current_user["login_email"]),
        selected_entity_id=resolved_selected_entity_id,
    )

    user_personal_data = get_user_personal_data(
        session,
        int(current_user["id"]),
        resolved_selected_entity_id,
    )

    next_entity_internal_number = get_next_entity_internal_number(session)

    return AdminBaseContext(
        current_user=current_user,
        selected_entity_id=resolved_selected_entity_id,
        current_user_is_admin=current_user_is_admin,
        entity_permissions=entity_permissions,
        page_data=page_data,
        user_personal_data=user_personal_data,
        next_entity_internal_number=next_entity_internal_number,
    )