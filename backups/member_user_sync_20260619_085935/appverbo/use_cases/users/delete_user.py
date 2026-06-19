from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.policies import (
    ensure_actor_is_admin_v1,
    ensure_member_scope_v1,
    ensure_not_self_delete_v1,
    ensure_target_user_is_non_active_v1,
)


logger = logging.getLogger(__name__)

DELETE_USER_RETURN_TARGET_V1 = "admin-user-shadow-inactive-card"


# ###################################################################################
# (1) REDIRECTS
# ###################################################################################

def _redirect_v1(success: str = "", error: str = "") -> UserActionOutcome:
    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success=success,
            error=error,
            menu="administrativo",
            admin_tab="utilizador",
            target=DELETE_USER_RETURN_TARGET_V1,
        )
        + f"#{DELETE_USER_RETURN_TARGET_V1}",
    )


# ###################################################################################
# (2) USE CASE PRINCIPAL
# ###################################################################################

def execute_delete_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    user_id: int | str,
) -> UserActionOutcome:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return _redirect_v1(error="Utilizador inválido para eliminação.")

    parsed_user_id = int(clean_user_id)
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    logger.info(
        "APPVERBO_DELETE_USER_USE_CASE_V2 start actor_id=%s target_user_id=%s",
        actor_user.get("id"),
        parsed_user_id,
    )

    admin_error = ensure_actor_is_admin_v1(
        session=session,
        actor_user=actor_user,
    )

    if admin_error:
        return _redirect_v1(error=admin_error)

    self_delete_error = ensure_not_self_delete_v1(
        actor_user_id=int(actor_user["id"]),
        target_user_id=parsed_user_id,
    )

    if self_delete_error:
        return _redirect_v1(error=self_delete_error)

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user, member = repository.get_user_and_member(
        session=session,
        user_id=parsed_user_id,
    )

    if user is None:
        return _redirect_v1(error="Utilizador não encontrado.")

    if member is None:
        return _redirect_v1(error="Membro associado ao utilizador não encontrado.")

    scope_error = ensure_member_scope_v1(
        repository=repository,
        session=session,
        member_id=int(member.id),
        permissions=entity_permissions,
    )

    if scope_error:
        return _redirect_v1(error=scope_error)

    inactive_error = ensure_target_user_is_non_active_v1(user)

    if inactive_error:
        return _redirect_v1(error=inactive_error)

    repository.delete_inactive_user(
        session=session,
        user=user,
    )

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        logger.error(
            "APPVERBO_DELETE_USER_USE_CASE_V2 integrity_error target_user_id=%s error=%s",
            parsed_user_id,
            exc,
        )
        return _redirect_v1(
            error=(
                "Não foi possível eliminar utilizador porque existem registos relacionados. "
                "Remova ou desative as dependências associadas primeiro."
            )
        )

    return _redirect_v1(success="Utilizador eliminado com sucesso.")


execute_delete_user_v1 = execute_delete_user
