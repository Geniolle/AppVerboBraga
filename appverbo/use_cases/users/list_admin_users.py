from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data


def list_admin_users_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return {
        "created_users": page_data.get("created_users", []),
        "active_created_users": page_data.get("active_created_users", []),
        "inactive_users": page_data.get("inactive_users", []),
        "pending_users": page_data.get("pending_users", []),
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
