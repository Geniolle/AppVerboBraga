from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.repositories.entity_repository import EntityAdminRepository
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.entities.get_entity_edit import (
    execute_get_entity_edit_v1,
    get_entity_edit_defaults_v1,
)
from appverbo.use_cases.entities.list_entities import execute_list_entities_v1


# ###################################################################################
# (1) CONTEXTO DE LISTAGEM DE ENTIDADES
# ###################################################################################

def build_entity_admin_list_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = EntityAdminRepository(ENTIDADE_CONFIG)

    if actor_user_id is None:
        return {
            "entities": [],
            "all_entities": [],
            "recent_entities": [],
            "active_entities": [],
            "inactive_entities": [],
            "entity_list_pagination": {
                "page": 1,
                "page_size": 100,
                "total": 0,
                "has_next": False,
            },
            "entity_permissions": {
                "is_admin": False,
                "can_manage_all_entities": False,
                "allowed_entity_ids": set(),
                "selected_entity_id": None,
            },
            "current_user_can_manage_all_entities": False,
            "next_entity_internal_number": str(repository.get_next_internal_number(session=session)),
        }

    list_result = execute_list_entities_v1(
        session=session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email or ""),
        selected_entity_id=selected_entity_id,
        filters=filters,
    )
    permissions = dict(list_result.get("entity_permissions") or {})

    return {
        "entities": list(list_result.get("entities", [])),
        "all_entities": list(list_result.get("all_entities", [])),
        "recent_entities": list(list_result.get("recent_entities", [])),
        "active_entities": list(list_result.get("active_entities", [])),
        "inactive_entities": list(list_result.get("inactive_entities", [])),
        "entity_list_pagination": dict(list_result.get("entity_list_pagination", {})),
        "entity_permissions": permissions,
        "current_user_can_manage_all_entities": bool(permissions.get("can_manage_all_entities")),
        "next_entity_internal_number": str(repository.get_next_internal_number(session=session)),
    }


# ###################################################################################
# (2) CONTEXTO DE EDIÇÃO DE ENTIDADE
# ###################################################################################

def build_entity_admin_edit_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    entity_edit_id: int | None,
) -> dict[str, Any]:
    if entity_edit_id is None or actor_user_id is None:
        return {
            "entity_edit_data": get_entity_edit_defaults_v1(),
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
        "entity_edit_data": execute_get_entity_edit_v1(
            session=session,
            entity_id=entity_edit_id,
            allowed_entity_ids=allowed_entity_ids,
        )
    }


# ###################################################################################
# (3) CONTEXTO COMPLETO DO SUBPROCESSO ENTIDADE
# ###################################################################################

def build_entity_admin_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    entity_edit_id: int | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    list_context = build_entity_admin_list_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        filters=filters,
    )

    edit_context = build_entity_admin_edit_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        entity_edit_id=entity_edit_id,
    )

    return {
        **list_context,
        **edit_context,
    }


def build_entity_admin_page_payload_v1(
    entity_admin_context: dict[str, Any] | None,
) -> dict[str, Any]:
    context = entity_admin_context or {}

    return {
        "entities": list(context.get("entities", [])),
        "all_entities": list(context.get("all_entities", [])),
        "recent_entities": list(context.get("recent_entities", [])),
        "active_entities": list(context.get("active_entities", [])),
        "inactive_entities": list(context.get("inactive_entities", [])),
        "entity_edit_data": dict(context.get("entity_edit_data", {})),
        "entity_list_pagination": dict(context.get("entity_list_pagination", {})),
        "entity_permissions": dict(context.get("entity_permissions", {})),
        "current_user_can_manage_all_entities": bool(
            context.get("current_user_can_manage_all_entities")
        ),
        "next_entity_internal_number": str(context.get("next_entity_internal_number") or "1"),
    }

