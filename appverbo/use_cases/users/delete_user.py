from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.repositories.user_profile_repository import delete_user_profiles
from appverbo.repositories.user_repository import get_user_by_id, null_created_by_for_deleted_user
from appverbo.services.auth import is_admin_user
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.user_status import is_user_account_status_inactive_v1
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


logger = logging.getLogger(__name__)

DELETE_USER_RETURN_TARGET_V1 = "admin-user-shadow-inactive-card"


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


def execute_delete_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    user_id: int,
) -> UserActionOutcome:
    parsed_user_id = int(user_id)

    logger.info(
        "APPVERBO_DELETE_USER_USE_CASE_V1 start actor_id=%s target_user_id=%s",
        actor_user.get("id"),
        parsed_user_id,
    )

    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_not_admin actor_id=%s target_user_id=%s",
            actor_user.get("id"),
            parsed_user_id,
        )
        return _redirect_v1(error="Apenas administradores podem eliminar utilizadores.")

    if parsed_user_id == int(actor_user["id"]):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_self_delete actor_id=%s",
            actor_user.get("id"),
        )
        return _redirect_v1(error="Não é permitido eliminar o próprio utilizador ligado.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user = get_user_by_id(session, parsed_user_id)

    if user is None:
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 not_found target_user_id=%s",
            parsed_user_id,
        )
        return _redirect_v1(error="Utilizador não encontrado.")

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user.member_id),
        permissions=entity_permissions,
    ):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_scope actor_id=%s target_user_id=%s member_id=%s",
            actor_user.get("id"),
            parsed_user_id,
            user.member_id,
        )
        return _redirect_v1(error="Sem permissão para eliminar este utilizador.")

    clean_status = str(user.account_status or "").strip().lower()

    if not is_user_account_status_inactive_v1(clean_status):
        logger.warning(
            "APPVERBO_DELETE_USER_USE_CASE_V1 denied_status target_user_id=%s status=%s",
            parsed_user_id,
            clean_status,
        )
        return _redirect_v1(
            error=(
                "Só é permitido eliminar utilizadores com estado Inativo. "
                f"Estado atual: {clean_status or '-'}."
            )
        )

    null_created_by_for_deleted_user(session, parsed_user_id)
    delete_user_profiles(session, parsed_user_id)
    session.delete(user)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        logger.error(
            "APPVERBO_DELETE_USER_USE_CASE_V1 integrity_error target_user_id=%s error=%s",
            parsed_user_id,
            exc,
        )
        return _redirect_v1(
            error=(
                "Não foi possível eliminar utilizador porque existem registos relacionados. "
                "Remova ou desative as dependências associadas primeiro."
            )
        )

    logger.info(
        "APPVERBO_DELETE_USER_USE_CASE_V1 success target_user_id=%s",
        parsed_user_id,
    )

    return _redirect_v1(success="Utilizador eliminado com sucesso.")


execute_delete_user_v1 = execute_delete_user
