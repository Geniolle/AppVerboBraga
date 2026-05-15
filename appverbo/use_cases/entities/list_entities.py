from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.repositories.entity_repository import (
    EntityAdminRepository,
    EntityListFilters,
)
from appverbo.services.permissions import get_user_entity_permissions


# ###################################################################################
# (1) NORMALIZAÇÃO DE FILTROS
# ###################################################################################

def _normalize_status_filters_v1(raw_status: str) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen_values: set[str] = set()

    for raw_part in raw_status.split(","):
        clean_part = str(raw_part or "").strip().lower()

        if clean_part not in {"active", "inactive"}:
            continue

        if clean_part in seen_values:
            continue

        seen_values.add(clean_part)
        normalized_values.append(clean_part)

    return tuple(normalized_values)


def _normalize_filters_v1(filters: dict[str, Any] | None = None) -> EntityListFilters:
    raw_filters = filters or {}

    raw_page = str(raw_filters.get("page") or "").strip()
    raw_page_size = str(raw_filters.get("page_size") or "").strip()
    raw_entity_id = str(raw_filters.get("entity_id") or "").strip()
    raw_status = str(raw_filters.get("status") or "").strip().lower()
    clean_search = str(raw_filters.get("q") or raw_filters.get("search") or "").strip()

    page = int(raw_page) if raw_page.isdigit() else 1
    page_size = int(raw_page_size) if raw_page_size.isdigit() else 100
    entity_id = int(raw_entity_id) if raw_entity_id.isdigit() else None

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 1

    if page_size > 5000:
        page_size = 5000

    status_values = _normalize_status_filters_v1(raw_status)

    return EntityListFilters(
        entity_id=entity_id,
        status_values=status_values,
        search_text=clean_search,
        page=page,
        page_size=page_size,
    )


# ###################################################################################
# (2) USE CASE DE LISTAGEM
# ###################################################################################

def execute_list_entities_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repository = EntityAdminRepository(ENTIDADE_CONFIG)
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

    result = repository.list_entities(
        session=session,
        allowed_entity_ids=allowed_entity_ids,
        filters=normalized_filters,
    )

    all_rows = list(result.get("rows", []))
    active_rows = [row for row in all_rows if str(row.get("status")) == "active"]
    inactive_rows = [row for row in all_rows if str(row.get("status")) == "inactive"]

    return {
        "all_entities": all_rows,
        "active_entities": active_rows,
        "inactive_entities": inactive_rows,
        "recent_entities": active_rows[:10],
        "entities": [
            {
                "id": row.get("id"),
                "name": row.get("name", ""),
                "internal_number": row.get("internal_number"),
            }
            for row in active_rows
        ],
        "entity_list_pagination": {
            "page": int(result.get("page") or 1),
            "page_size": int(result.get("page_size") or 100),
            "total": int(result.get("total") or 0),
            "has_next": bool(result.get("has_next")),
        },
        "entity_permissions": permissions,
    }

