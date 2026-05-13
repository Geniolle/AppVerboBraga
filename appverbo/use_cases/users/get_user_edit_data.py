from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.services.page import get_user_edit_data, get_user_edit_defaults


def execute_get_user_edit_data_v1(
    *,
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    return get_user_edit_data(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )


__all__ = [
    "execute_get_user_edit_data_v1",
    "get_user_edit_defaults",
]

