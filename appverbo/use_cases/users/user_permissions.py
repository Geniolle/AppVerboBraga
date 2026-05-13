from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.services.permissions import get_user_entity_permissions


def execute_get_user_permissions_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict:
    return get_user_entity_permissions(
        session,
        actor_user_id,
        actor_login_email,
        selected_entity_id,
    )


__all__ = ["execute_get_user_permissions_v1"]

