from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.policies import (
    allowed_entity_ids_from_permissions_v1,
    ensure_member_scope_v1,
    ensure_not_last_active_admin_for_member_v1 as ensure_not_last_active_admin_policy_v1,
    is_admin_profile_v1,
)


def allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return allowed_entity_ids_from_permissions_v1(permissions)


def member_is_within_permissions_v1(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    scope_error = ensure_member_scope_v1(
        repository=repository,
        session=session,
        member_id=member_id,
        permissions=permissions,
    )

    return not bool(scope_error)


def execute_get_user_permissions_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    return get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email),
        selected_entity_id,
    )


def ensure_not_last_active_admin_for_member_v1(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    return ensure_not_last_active_admin_policy_v1(
        repository=repository,
        session=session,
        member_id=member_id,
        excluded_user_id=excluded_user_id,
    )
