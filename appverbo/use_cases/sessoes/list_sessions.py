from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
    SESSION_STATUS_ACTIVE_V1,
    SESSION_ALLOWED_STATUS_VALUES_V1,
    SESSION_STATUS_BLOCKED_V1,
    SESSION_STATUS_INACTIVE_V1,
    SESSION_STATUS_PENDING_V1,
    SidebarSectionAdminRepository,
    SidebarSectionListFilters,
)
from appverbo.admin_subprocesses.sessoes.configuracao import SESSOES_CONFIG
from appverbo.menu_settings import get_sidebar_global_refresh_version_v1
from appverbo.services.permissions import get_user_entity_permissions


# ###################################################################################
# (1) NORMALIZACAO DE FILTROS
# ###################################################################################

def _normalize_filters_v1(filters: dict[str, Any] | None = None) -> SidebarSectionListFilters:
    raw_filters = filters or {}

    raw_page = str(raw_filters.get("page") or "").strip()
    raw_page_size = str(raw_filters.get("page_size") or "").strip()
    raw_entity_id = str(raw_filters.get("entity_id") or "").strip()
    raw_status = str(raw_filters.get("status") or "").strip().lower()
    clean_search = str(raw_filters.get("q") or raw_filters.get("search") or "").strip()

    page = int(raw_page) if raw_page.isdigit() else 1
    page_size = int(raw_page_size) if raw_page_size.isdigit() else 5000
    entity_id = int(raw_entity_id) if raw_entity_id.isdigit() else None

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 1

    if page_size > 5000:
        page_size = 5000

    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    status_values: list[str] = []
    seen_status_values: set[str] = set()

    for raw_part in raw_status.split(","):
        clean_part = str(raw_part or "").strip().lower()

        if not clean_part:
            continue

        normalized_status = repository.normalize_session_status(clean_part)

        if normalized_status not in SESSION_ALLOWED_STATUS_VALUES_V1:
            continue

        if normalized_status in seen_status_values:
            continue

        seen_status_values.add(normalized_status)
        status_values.append(normalized_status)

    return SidebarSectionListFilters(
        entity_id=entity_id,
        status_values=tuple(status_values),
        search_text=clean_search,
        page=page,
        page_size=page_size,
    )


# ###################################################################################
# (2) USE CASE DE LISTAGEM DE SESSOES
# ###################################################################################

def execute_list_sessions_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    normalized_filters = _normalize_filters_v1(filters)

    permissions = get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email or ""),
        selected_entity_id,
    )

    result = repository.list_sessions(
        session=session,
        filters=normalized_filters,
    )

    all_sessions = list(result.get("rows", []))

    active_sessions = [
        row
        for row in all_sessions
        if repository.normalize_session_status(row.get("status")) == SESSION_STATUS_ACTIVE_V1
    ]
    inactive_sessions = [
        row
        for row in all_sessions
        if repository.normalize_session_status(row.get("status")) == SESSION_STATUS_INACTIVE_V1
    ]
    pending_sessions = [
        row
        for row in all_sessions
        if repository.normalize_session_status(row.get("status")) == SESSION_STATUS_PENDING_V1
    ]
    blocked_sessions = [
        row
        for row in all_sessions
        if repository.normalize_session_status(row.get("status")) == SESSION_STATUS_BLOCKED_V1
    ]

    return {
        "sessions": all_sessions,
        "all_sessions": all_sessions,
        "active_sessions": active_sessions,
        "inactive_sessions": inactive_sessions,
        "pending_sessions": pending_sessions,
        "blocked_sessions": blocked_sessions,
        "recent_sessions": all_sessions[:10],
        "session_list_pagination": {
            "page": int(result.get("page") or 1),
            "page_size": int(result.get("page_size") or 5000),
            "total": int(result.get("total") or 0),
            "has_next": bool(result.get("has_next")),
        },
        "session_permissions": permissions,
    }


# ###################################################################################
# (3) USE CASES AUXILIARES PARA ENDPOINTS GET
# ###################################################################################

def execute_get_sidebar_refresh_version_v1(*, session: Session) -> str:
    return str(get_sidebar_global_refresh_version_v1(session) or "")


def execute_get_sidebar_sections_data_v1(*, session: Session) -> list[dict[str, Any]]:
    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    return repository.read_sidebar_sections(session=session)
