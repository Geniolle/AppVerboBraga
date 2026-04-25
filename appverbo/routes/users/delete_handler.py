from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

from appverbo.routes.users.router import router
from appverbo.routes.users.helpers import (
    _ensure_not_last_active_admin_for_member,
    _member_is_within_permissions,
)

@router.post("/users/delete", response_class=HTMLResponse)
def delete_user(
    request: Request,
    user_id: str = Form(...),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para eliminação.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    parsed_user_id = int(clean_user_id)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Apenas administradores podem eliminar utilizadores.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if parsed_user_id == int(current_user["id"]):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não é permitido eliminar o próprio utilizador ligado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        user = session.get(User, parsed_user_id)
        if user is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if not _member_is_within_permissions(
            session,
            int(user.member_id),
            entity_permissions,
        ):
            return RedirectResponse(
                url=build_users_new_url(
                    error="Sem permissão para eliminar este utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        target_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        if target_is_active_admin:
            can_delete_admin, admin_delete_error = _ensure_not_last_active_admin_for_member(
                session,
                int(user.member_id),
                int(user.id),
            )
            if not can_delete_admin:
                return RedirectResponse(
                    url=build_users_new_url(
                        error=admin_delete_error,
                        menu="administrativo",
                        admin_tab="utilizador",
                    )
                    + "#create-user-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

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
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não foi possível eliminar utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            success="Utilizador eliminado com sucesso.",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )
