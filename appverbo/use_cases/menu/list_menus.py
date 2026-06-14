from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import (
    MenuAdminRepository,
    MenuListFilters,
)
from appverbo.services.entity_scope import load_entity_profile_scope_v1
from appverbo.services.permissions import get_user_entity_permissions


# ###################################################################################
# (1) HELPERS DE FILTRO
# ###################################################################################


def normalize_list_menus_filters_v1(
    filters: dict[str, Any] | None,
) -> dict[str, Any]:
    raw_filters = filters or {}

    return {
        "status": str(raw_filters.get("status") or "").strip().lower(),
        "q": str(raw_filters.get("q") or raw_filters.get("search") or "").strip(),
        "page": str(raw_filters.get("page") or "").strip(),
        "page_size": str(raw_filters.get("page_size") or "").strip(),
    }


# ###################################################################################
# (2) USE CASE DE LISTAGEM
# ###################################################################################


def execute_list_menus_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = MenuAdminRepository(MENU_CONFIG)
    clean_filters = normalize_list_menus_filters_v1(filters)
    permissions = get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email or ""),
        selected_entity_id,
    )

    if permissions.get("can_manage_all_entities"):
        allowed_entity_ids: tuple[int, ...] = ()
    else:
        allowed_entity_ids = tuple(
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
            if str(raw_id).strip().isdigit()
        )

    page_value = int(clean_filters["page"]) if clean_filters["page"].isdigit() else 1
    page_size_value = (
        int(clean_filters["page_size"])
        if clean_filters["page_size"].isdigit()
        else 5000
    )

    list_filters = MenuListFilters(
        entity_id=selected_entity_id,
        allowed_entity_ids=allowed_entity_ids,
        status_values=tuple(
            status_part.strip().lower()
            for status_part in str(clean_filters["status"]).split(",")
            if status_part.strip()
        ),
        search_text=str(clean_filters["q"]),
        page=page_value,
        page_size=page_size_value,
    )

    resolved_selected_entity_id = permissions.get("selected_entity_id")
    current_entity_scope = load_entity_profile_scope_v1(session, resolved_selected_entity_id)
    if not current_entity_scope and permissions.get("can_manage_all_entities"):
        current_entity_scope = "owner"

    list_result = repository.list_menus(
        session=session,
        filters=list_filters,
        current_entity_scope=current_entity_scope,
    )
    all_rows = list(list_result.get("rows", []))
    active_rows = [
        row for row in all_rows if str(row.get("status") or "").strip().lower() == "active"
    ]
    inactive_rows = [
        row for row in all_rows if str(row.get("status") or "").strip().lower() == "inactive"
    ]
    deleted_rows = [row for row in all_rows if bool(row.get("is_deleted"))]
    recent_rows = list(all_rows)[:10]

    return {
        "menus": all_rows,
        "all_menus": all_rows,
        "active_menus": active_rows,
        "inactive_menus": inactive_rows,
        "deleted_menus": deleted_rows,
        "recent_menus": recent_rows,
        "menu_list_pagination": {
            "page": int(list_result.get("page", 1) or 1),
            "page_size": int(list_result.get("page_size", 5000) or 5000),
            "total": int(list_result.get("total", 0) or 0),
            "has_next": bool(list_result.get("has_next")),
        },
        "menu_permissions": permissions,
    }
