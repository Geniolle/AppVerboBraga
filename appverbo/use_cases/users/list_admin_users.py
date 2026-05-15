from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.use_cases.users.list_users import execute_list_users_v1


def list_admin_users_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    result = execute_list_users_v1(
        session=session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )

    return {
        "all_users": result.get("all_users", []),
        "created_users": result.get("created_users", []),
        "active_created_users": result.get("active_created_users", []),
        "inactive_users": result.get("inactive_users", []),
        "pending_users": result.get("pending_users", []),
        "blocked_users": result.get("blocked_users", []),
        "non_active_users": result.get("non_active_users", []),
        "recent_users": result.get("recent_users", []),
        "superuser_users": result.get("superuser_users", []),
        "account_status_summary": result.get("account_status_summary", []),
        "pagination": result.get("pagination", {}),
        "entity_permissions": result.get("entity_permissions", {}),
    }


def execute_list_admin_users_v1(
    *,
    session: Session,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
    from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG

    repository = UserAdminRepository(UTILIZADOR_CONFIG)
    return repository.list_rows(session, context or {})
