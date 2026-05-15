from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.get_user_edit import (
    execute_get_user_edit_v1,
    get_user_edit_defaults_v1,
)


def get_user_edit_data_v1(
    session: Session,
    *,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
    user_edit_id: int | None,
) -> dict[str, Any]:
    if user_edit_id is None:
        return get_user_edit_defaults_v1()

    permissions = get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email or ""),
        selected_entity_id,
    )

    allowed_entity_ids: set[int] | None

    if permissions.get("can_manage_all_entities"):
        allowed_entity_ids = None
    else:
        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
            if str(raw_id).strip().isdigit()
        }

    return execute_get_user_edit_v1(
        session=session,
        user_id=user_edit_id,
        allowed_entity_ids=allowed_entity_ids,
    )


def execute_get_user_edit_data_v1(
    *,
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    return execute_get_user_edit_v1(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )
