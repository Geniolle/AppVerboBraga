from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.page import get_page_data, get_user_edit_data, get_user_edit_defaults


def get_user_edit_data_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None,
) -> dict[str, Any]:
    if user_edit_id is None:
        return get_user_edit_defaults()

    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user_id),
        actor_login_email=str(actor_login_email),
        selected_entity_id=selected_entity_id,
    )

    return page_data.get("user_edit_data") or get_user_edit_defaults()


def execute_get_user_edit_data_v1(
    *,
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    return get_user_edit_data(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )
