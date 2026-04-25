from __future__ import annotations

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

from appverbo.routes.auth.router import router

@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    entity_id: str = Form(""),
    login_mode: str = Form("login"),
) -> HTMLResponse:
    clean_email = email.strip().lower()
    clean_password = password
    clean_entity_id = entity_id.strip()
    login_data = {
        "entity_id": clean_entity_id,
    }
    requested_mode = "admin" if login_mode.strip().lower() == "admin" else "login"

    if not clean_email or not clean_password:
        return render_login(
            request,
            error="Informe email e palavra-passe.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    parsed_entity_id: int | None = None
    if clean_entity_id:
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            return render_login(
                request,
                error="Entidade selecionada inválida.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    selected_entity_context: dict[str, Any] | None = None
    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

        row = session.execute(
            select(
                User.id,
                User.login_email,
                User.password_hash,
                User.account_status,
                User.member_id,
                Member.full_name,
            )
           .join(Member, Member.id == User.member_id)
           .where(func.lower(User.login_email) == clean_email)
        ).one_or_none()

        if row is None or not verify_password(clean_password, row.password_hash):
            return render_login(
                request,
                error="Credenciais inválidas.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if row.account_status != UserAccountStatus.ACTIVE.value:
            return render_login(
                request,
                error=f"Conta com estado '{row.account_status}'. Contacte o administrador.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        current_user_is_admin = is_admin_user(session, row.id, row.login_email)
        if requested_mode == "admin" and not current_user_is_admin:
            return render_login(
                request,
                error="Acesso administrativo disponivel apenas para utilizadores administradores.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        linked_entity_ids_rows = session.scalars(
            select(MemberEntity.entity_id)
           .where(
                MemberEntity.member_id == int(row.member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .order_by(MemberEntity.id.asc())
        ).all()
        linked_entity_ids = [
            int(entity_id)
            for entity_id in linked_entity_ids_rows
            if isinstance(entity_id, int)
        ]
        if not linked_entity_ids:
            return render_login(
                request,
                error="Utilizador sem entidade ativa associada.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if parsed_entity_id is None:
            resolved_entity, resolution_error = resolve_active_entity_by_email(session, clean_email)
            if resolved_entity is None:
                return render_login(
                    request,
                    error=resolution_error or "Selecione a entidade para entrar.",
                    email=clean_email,
                    mode=requested_mode,
                    login_data=login_data,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            parsed_entity_id = int(resolved_entity.id)
            login_data["entity_id"] = str(parsed_entity_id)

        if parsed_entity_id not in linked_entity_ids:
            return render_login(
                request,
                error="Não é permitido entrar com uma entidade diferente da associada ao seu utilizador.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        selected_entity_context = get_entity_context_for_user(
            session,
            row.id,
            row.login_email,
            parsed_entity_id,
        )
        if selected_entity_context is None:
            return render_login(
                request,
                error="Não tem permissão para entrar na entidade selecionada.",
                email=clean_email,
                mode=requested_mode,
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

    request.session["user_id"] = row.id
    request.session["user_name"] = row.full_name
    request.session["user_email"] = row.login_email
    set_session_entity_context(request, selected_entity_context)
    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/signup", response_class=HTMLResponse)
def signup(
    request: Request,
    full_name: str = Form(...),
    country: str = Form(...),
    primary_phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    entity_id: str = Form(""),
) -> HTMLResponse:
    errors: list[str] = []
    clean_full_name = full_name.strip()
    clean_country = country.strip().upper()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = entity_id.strip()

    signup_data = {
        "full_name": clean_full_name,
        "country": clean_country,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": clean_entity_id,
        "entity_name": "",
        "entity_locked": "",
    }

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    phone_country_error = validate_signup_phone_country(clean_country, clean_primary_phone)
    if phone_country_error:
        errors.append(phone_country_error)
    if not clean_email:
        errors.append("Email é obrigatório.")
    if len(password) < 8:
        errors.append("A palavra-passe deve ter no minimo 8 caracteres.")
    if password != confirm_password:
        errors.append("A confirmação da palavra-passe não confere.")

    parsed_entity_id: int | None = None
    if clean_entity_id:
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            errors.append("Entidade inválida.")

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is not None:
            return RedirectResponse(url="/users/new", status_code=status.HTTP_302_FOUND)

        existing_user = session.execute(
            select(User.id).where(func.lower(User.login_email) == clean_email)
        ).scalar_one_or_none()
        if existing_user:
            errors.append("Já existe conta com este email. Use o login.")

        if parsed_entity_id is not None:
            existing_entity = session.get(Entity, parsed_entity_id)
            if existing_entity is None:
                errors.append("Entidade selecionada não existe.")
            elif existing_entity.is_active:
                signup_data["entity_name"] = existing_entity.name or ""
                signup_data["entity_locked"] = "1"

        if errors:
            return render_login(
                request,
                error=" ".join(errors),
                mode="signup",
                signup_data=signup_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = upsert_user_by_email(
            session=session,
            email=clean_email,
            full_name=clean_full_name,
            primary_phone=clean_primary_phone,
            entity_id=parsed_entity_id,
        )
        user.password_hash = hash_password(password)
        user.account_status = UserAccountStatus.ACTIVE.value

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_login(
                request,
                error="Falha ao criar conta. Tente novamente.",
                mode="signup",
                signup_data=signup_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.session["user_id"] = user.id
        request.session["user_name"] = clean_full_name
        request.session["user_email"] = clean_email
        set_session_entity_context(
            request,
            get_entity_context_for_user(session, user.id, user.login_email, parsed_entity_id),
        )

    return RedirectResponse(url="/users/new", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(
        url="/login?success=Sessão encerrada com sucesso.",
        status_code=status.HTTP_303_SEE_OTHER,
    )
