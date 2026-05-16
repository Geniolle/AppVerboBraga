from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.use_cases.menu.get_menu_edit import (
    execute_get_menu_edit_v1,
    get_menu_edit_defaults_v1,
)
from appverbo.use_cases.menu.list_menus import execute_list_menus_v1


# ###################################################################################
# (1) CONTEXTO DE LISTAGEM DE MENU
# ###################################################################################


def build_menu_admin_list_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = MenuAdminRepository(MENU_CONFIG)
    menu_section_options = repository.get_section_options(session=session)

    if actor_user_id is None:
        return {
            "menu_settings": [],
            "menus": [],
            "all_menus": [],
            "active_menus": [],
            "inactive_menus": [],
            "deleted_menus": [],
            "recent_menus": [],
            "menu_list_pagination": {
                "page": 1,
                "page_size": 5000,
                "total": 0,
                "has_next": False,
            },
            "menu_permissions": {
                "is_admin": False,
                "can_manage_all_entities": False,
                "allowed_entity_ids": set(),
                "selected_entity_id": None,
            },
            "menu_section_options": menu_section_options,
            "sidebar_section_options": menu_section_options,
            "current_user_can_manage_all_entities": False,
        }

    list_result = execute_list_menus_v1(
        session=session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email or ""),
        selected_entity_id=selected_entity_id,
        filters=filters,
    )
    permissions = dict(list_result.get("menu_permissions") or {})

    return {
        "menu_settings": list(list_result.get("menus", [])),
        "menus": list(list_result.get("menus", [])),
        "all_menus": list(list_result.get("all_menus", [])),
        "active_menus": list(list_result.get("active_menus", [])),
        "inactive_menus": list(list_result.get("inactive_menus", [])),
        "deleted_menus": list(list_result.get("deleted_menus", [])),
        "recent_menus": list(list_result.get("recent_menus", [])),
        "menu_list_pagination": dict(list_result.get("menu_list_pagination", {})),
        "menu_permissions": permissions,
        "menu_section_options": menu_section_options,
        "sidebar_section_options": menu_section_options,
        "current_user_can_manage_all_entities": bool(
            permissions.get("can_manage_all_entities")
        ),
    }


# ###################################################################################
# (2) CONTEXTO DE EDIÇÃO DE MENU
# ###################################################################################


def build_menu_admin_edit_context_v1(
    *,
    session: Session,
    menu_edit_key: str,
) -> dict[str, Any]:
    clean_menu_edit_key = str(menu_edit_key or "").strip().lower()

    if not clean_menu_edit_key:
        edit_data = get_menu_edit_defaults_v1()
    else:
        edit_data = execute_get_menu_edit_v1(
            session=session,
            menu_key=clean_menu_edit_key,
        )

    return {
        "menu_edit_data": dict(edit_data),
        "additional_field_type_options": list(
            (edit_data.get("additional_field_type_options") or [])
        ),
        "process_field_options": list(edit_data.get("process_field_options") or []),
        "process_selectable_field_options": list(
            edit_data.get("process_selectable_field_options") or []
        ),
        "process_header_options": list(edit_data.get("process_header_options") or []),
        "process_visible_field_rows": list(
            edit_data.get("process_visible_field_rows") or []
        ),
        "process_lists": list(edit_data.get("process_lists") or []),
    }


# ###################################################################################
# (3) CONTEXTO COMPLETO DO SUBPROCESSO MENU
# ###################################################################################


def build_menu_admin_context_v1(
    *,
    session: Session,
    actor_user_id: int | None,
    actor_login_email: str,
    selected_entity_id: int | None,
    menu_edit_key: str = "",
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    list_context = build_menu_admin_list_context_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
        filters=filters,
    )

    edit_context = build_menu_admin_edit_context_v1(
        session=session,
        menu_edit_key=menu_edit_key,
    )

    return {
        **list_context,
        **edit_context,
    }


def build_menu_admin_page_payload_v1(
    menu_admin_context: dict[str, Any] | None,
) -> dict[str, Any]:
    context = menu_admin_context or {}

    return {
        "menu_settings": list(context.get("menu_settings", [])),
        "menus": list(context.get("menus", [])),
        "all_menus": list(context.get("all_menus", [])),
        "active_menus": list(context.get("active_menus", [])),
        "inactive_menus": list(context.get("inactive_menus", [])),
        "deleted_menus": list(context.get("deleted_menus", [])),
        "recent_menus": list(context.get("recent_menus", [])),
        "menu_edit_data": dict(context.get("menu_edit_data", {})),
        "menu_permissions": dict(context.get("menu_permissions", {})),
        "menu_list_pagination": dict(context.get("menu_list_pagination", {})),
        "menu_section_options": list(context.get("menu_section_options", [])),
        "sidebar_section_options": list(context.get("sidebar_section_options", [])),
        "additional_field_type_options": list(
            context.get("additional_field_type_options", [])
        ),
        "process_field_options": list(context.get("process_field_options", [])),
        "process_selectable_field_options": list(
            context.get("process_selectable_field_options", [])
        ),
        "process_header_options": list(context.get("process_header_options", [])),
        "process_visible_field_rows": list(
            context.get("process_visible_field_rows", [])
        ),
        "process_lists": list(context.get("process_lists", [])),
        "current_user_can_manage_all_entities": bool(
            context.get("current_user_can_manage_all_entities")
        ),
    }
