from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from appverbo.admin_subprocesses.utilizador.common import (
    ensure_not_last_active_admin_for_member_v1,
    member_is_within_permissions_v1,
    redirect_admin_users_v1,
    redirect_login_required_v1,
)
from appverbo.core import SessionLocal
from appverbo.models import User, UserAccountStatus, UserProfile
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.services.user_status import is_user_account_status_inactive_v1


# ###################################################################################
# (1) USE CASE PRINCIPAL DE ELIMINACAO DE UTILIZADOR
# ###################################################################################

def execute_delete_user_v1(
    *,
    request: Request,
    user_id: str,
) -> RedirectResponse:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return redirect_admin_users_v1(
            error="Utilizador inv\u00e1lido para elimina\u00e7\u00e3o."
        )

    parsed_user_id = int(clean_user_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return redirect_login_required_v1()

        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return redirect_admin_users_v1(
                error="Apenas administradores podem eliminar utilizadores."
            )

        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if parsed_user_id == int(current_user["id"]):
            return redirect_admin_users_v1(
                error="N\u00e3o \u00e9 permitido eliminar o pr\u00f3prio utilizador ligado."
            )

        user = session.get(User, parsed_user_id)

        if user is None:
            return redirect_admin_users_v1(
                error="Utilizador n\u00e3o encontrado."
            )

        if not member_is_within_permissions_v1(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return redirect_admin_users_v1(
                error="Sem permiss\u00e3o para eliminar este utilizador."
            )

        if not is_user_account_status_inactive_v1(user.account_status):
            return redirect_admin_users_v1(
                error="S\u00f3 \u00e9 permitido eliminar utilizadores inativos."
            )

        target_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )

        if target_is_active_admin:
            can_delete_admin, admin_delete_error = ensure_not_last_active_admin_for_member_v1(
                session,
                int(user.member_id),
                int(user.id),
            )

            if not can_delete_admin:
                return redirect_admin_users_v1(error=admin_delete_error)

        session.execute(
            update(User)
            .where(User.created_by_user_id == parsed_user_id)
            .values(created_by_user_id=None)
        )
        session.execute(delete(UserProfile).where(UserProfile.user_id == parsed_user_id))
        session.delete(user)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return redirect_admin_users_v1(
                error="N\u00e3o foi poss\u00edvel eliminar utilizador."
            )

    return redirect_admin_users_v1(
        success="Utilizador eliminado com sucesso."
    )