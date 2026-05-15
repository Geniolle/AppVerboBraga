from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import (
    UserAdminRepository,
    UserListFilters,
)
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.models import UserAccountStatus
from appverbo.services.permissions import get_user_entity_permissions


# ###################################################################################
# (1) CONVERSAO DE FILTROS E RESUMOS
# ###################################################################################

def _normalize_filters_v1(filters: dict[str, Any] | None = None) -> UserListFilters:
    raw_filters = filters or {}

    raw_page = str(raw_filters.get("page") or "").strip()
    raw_page_size = str(raw_filters.get("page_size") or "").strip()

    page = int(raw_page) if raw_page.isdigit() else 1
    page_size = int(raw_page_size) if raw_page_size.isdigit() else 5000

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 1

    if page_size > 5000:
        page_size = 5000

    raw_entity_id = str(raw_filters.get("entity_id") or "").strip()
    raw_profile_id = str(raw_filters.get("profile_id") or "").strip()
    raw_status = str(raw_filters.get("status") or "").strip().lower()
    clean_search = str(raw_filters.get("q") or raw_filters.get("search") or "").strip()

    entity_id = int(raw_entity_id) if raw_entity_id.isdigit() else None
    profile_id = int(raw_profile_id) if raw_profile_id.isdigit() else None

    status_values = tuple(
        clean_status
        for clean_status in (
            part.strip().lower()
            for part in raw_status.split(",")
        )
        if clean_status
    )

    return UserListFilters(
        entity_id=entity_id,
        profile_id=profile_id,
        status_values=status_values,
        search_text=clean_search,
        page=page,
        page_size=page_size,
    )


def _build_account_status_summary_v1(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    account_status_map: dict[str, int] = {
        UserAccountStatus.ACTIVE.value: 0,
        UserAccountStatus.PENDING.value: 0,
        UserAccountStatus.INACTIVE.value: 0,
        UserAccountStatus.BLOCKED.value: 0,
    }

    for row in rows:
        normalized_status = str(row.get("account_status") or "").strip().lower()

        if normalized_status not in account_status_map:
            account_status_map[normalized_status] = 0

        account_status_map[normalized_status] += 1

    return [
        {
            "status": UserAccountStatus.ACTIVE.value,
            "count": account_status_map.get(UserAccountStatus.ACTIVE.value, 0),
        },
        {
            "status": UserAccountStatus.PENDING.value,
            "count": account_status_map.get(UserAccountStatus.PENDING.value, 0),
        },
        {
            "status": UserAccountStatus.INACTIVE.value,
            "count": account_status_map.get(UserAccountStatus.INACTIVE.value, 0),
        },
        {
            "status": UserAccountStatus.BLOCKED.value,
            "count": account_status_map.get(UserAccountStatus.BLOCKED.value, 0),
        },
    ]


# ###################################################################################
# (2) USE CASE DE LISTAGEM
# ###################################################################################

def execute_list_users_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = UserAdminRepository(UTILIZADOR_CONFIG)
    normalized_filters = _normalize_filters_v1(filters)

    permissions = get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email or ""),
        selected_entity_id,
    )

    if permissions.get("can_manage_all_entities"):
        allowed_entity_ids: set[int] | None = None
    else:
        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
            if str(raw_id).strip().isdigit()
        }

    result = repository.list_users(
        session=session,
        allowed_entity_ids=allowed_entity_ids,
        filters=normalized_filters,
    )

    all_users = list(result.get("rows", []))
    pending_users = [
        row
        for row in all_users
        if row.get("account_status") == UserAccountStatus.PENDING.value
    ]
    created_users = [
        row
        for row in all_users
        if row.get("account_status") != UserAccountStatus.PENDING.value
    ]
    active_created_users = [
        row
        for row in created_users
        if row.get("account_status") == UserAccountStatus.ACTIVE.value
    ]
    inactive_users = [
        row
        for row in all_users
        if row.get("account_status") != UserAccountStatus.ACTIVE.value
    ]
    superuser_users = [
        row
        for row in all_users
        if bool(row.get("is_entity_superuser"))
    ]

    return {
        "all_users": all_users,
        "created_users": created_users,
        "active_created_users": active_created_users,
        "inactive_users": inactive_users,
        "pending_users": pending_users,
        "recent_users": all_users[:10],
        "superuser_users": superuser_users,
        "account_status_summary": _build_account_status_summary_v1(all_users),
        "pagination": {
            "page": int(result.get("page") or 1),
            "page_size": int(result.get("page_size") or 5000),
            "total": int(result.get("total") or 0),
            "has_next": bool(result.get("has_next")),
        },
        "entity_permissions": permissions,
    }
