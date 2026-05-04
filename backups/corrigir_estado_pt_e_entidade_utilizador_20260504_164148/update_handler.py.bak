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
    _is_admin_profile,
    _member_is_within_permissions,
    _resolve_entity_from_user_email,
)

@router.post("/users/update", response_class=HTMLResponse)
def update_user(
    request: Request,
    user_id: str = Form(...),
    full_name: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    entity_id: str = Form(""),
    account_status: str = Form(UserAccountStatus.ACTIVE.value),
    profile_id: str = Form(""),
) -> RedirectResponse:
    clean_user_id = user_id.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_account_status = account_status.strip().lower()
    clean_profile_id = profile_id.strip()

    if not clean_user_id.isdigit():
        return RedirectResponse(
            url=build_users_new_url(
                error="Utilizador inválido para edição.",
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
                    error="Apenas administradores podem editar utilizadores.",
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
                    error="Sem permissão para editar este utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        member = session.get(Member, user.member_id)
        if member is None:
            return RedirectResponse(
                url=build_users_new_url(
                    error="Membro associado ao utilizador não encontrado.",
                    menu="administrativo",
                    admin_tab="utilizador",
                )
                + "#create-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        errors: list[str] = []
        if not clean_full_name:
            errors.append("Nome completo é obrigatório.")
        if not clean_primary_phone:
            errors.append("Telefone principal é obrigatório.")
        if not clean_email:
            errors.append("Email é obrigatório.")
        if clean_account_status not in ALLOWED_ACCOUNT_STATUS:
            errors.append("Estado de conta inválido.")

        selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
            session,
            clean_email,
            entity_permissions,
        )
        if selected_entity is None and entity_resolution_error:
            errors.append(entity_resolution_error)

        selected_profile: Profile | None = None
        if clean_profile_id:
            try:
                selected_profile = session.get(Profile, int(clean_profile_id))
            except ValueError:
                errors.append("Perfil selecionado inválido.")
            if selected_profile is None and not errors:
                errors.append("Perfil selecionado não existe.")
            elif not is_allowed_global_profile(selected_profile):
                errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

        duplicate_member_id = session.scalar(
            select(Member.id).where(
                func.lower(Member.email) == clean_email,
                Member.id != member.id,
            )
        )
        if duplicate_member_id is not None:
            errors.append("Já existe um membro com este email.")

        duplicate_user_id = session.scalar(
            select(User.id).where(
                func.lower(User.login_email) == clean_email,
                User.id != user.id,
            )
        )
        if duplicate_user_id is not None:
            errors.append("Já existe um utilizador com este email de login.")

        if errors:
            return RedirectResponse(
                url=build_users_new_url(
                    error=" ".join(errors),
                    menu="administrativo",
                    admin_tab="utilizador",
                    user_edit_id=str(parsed_user_id),
                )
                + "#edit-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        if selected_profile is None:
            selected_profile = get_or_create_entity_superuser_profile(session)

        current_is_active_admin = (
            str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
            and is_admin_user(session, int(user.id), str(user.login_email or ""))
        )
        resulting_is_admin = (
            (bool(ADMIN_LOGIN_EMAIL) and clean_email == ADMIN_LOGIN_EMAIL)
            or _is_admin_profile(selected_profile)
        )
        resulting_is_active_admin = (
            clean_account_status == UserAccountStatus.ACTIVE.value and resulting_is_admin
        )
        if current_is_active_admin and not resulting_is_active_admin:
            can_change_admin_state, admin_state_error = _ensure_not_last_active_admin_for_member(
                session,
                int(user.member_id),
                int(user.id),
            )
            if not can_change_admin_state:
                return RedirectResponse(
                    url=build_users_new_url(
                        error=admin_state_error,
                        menu="administrativo",
                        admin_tab="utilizador",
                        user_edit_id=str(parsed_user_id),
                    )
                    + "#edit-user-card",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        member.full_name = clean_full_name
        member.primary_phone = clean_primary_phone
        member.email = clean_email
        user.login_email = clean_email
        user.account_status = clean_account_status

        if selected_entity is not None:
            primary_link = session.execute(
                select(MemberEntity)
               .where(MemberEntity.member_id == member.id)
               .order_by(MemberEntity.id.asc())
               .limit(1)
            ).scalar_one_or_none()
            if primary_link is None:
                session.add(
                    MemberEntity(
                        member_id=member.id,
                        entity_id=selected_entity.id,
                        status=MemberEntityStatus.ACTIVE.value,
                        entry_date=date.today(),
                    )
                )
            else:
                primary_link.entity_id = selected_entity.id
                primary_link.status = MemberEntityStatus.ACTIVE.value

        session.execute(delete(UserProfile).where(UserProfile.user_id == user.id))
        session.add(
            UserProfile(
                user_id=user.id,
                profile_id=selected_profile.id,
                is_active=True,
            )
        )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return RedirectResponse(
                url=build_users_new_url(
                    error="Não foi possível atualizar utilizador.",
                    menu="administrativo",
                    admin_tab="utilizador",
                    user_edit_id=str(parsed_user_id),
                )
                + "#edit-user-card",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    return RedirectResponse(
        url=build_users_new_url(
            success="Utilizador atualizado com sucesso.",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
        status_code=status.HTTP_303_SEE_OTHER,
    )
