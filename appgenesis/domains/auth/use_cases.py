from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.domains.auth.schemas import LoginFormInput, SignupFormInput
from appgenesis.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    User,
    UserAccountStatus,
)
from appgenesis.services.auth import (
    get_signup_defaults,
    hash_password,
    is_admin_user,
    upsert_user_by_email,
    validate_signup_phone_country,
    verify_login_password_v1,
)
from appgenesis.services.i18n import resolve_user_language_after_auth
from appgenesis.services.session import get_current_user, get_entity_context_for_user
from appgenesis.shared.results import RedirectOutcome


@dataclass(frozen=True)
class LoginFailure:
    error: str
    email: str
    mode: str
    login_data: dict[str, Any]
    status_code: int


@dataclass(frozen=True)
class LoginSuccess:
    user: User
    user_full_name: str
    selected_entity_context: dict[str, Any]


LoginResult = LoginSuccess | LoginFailure | RedirectOutcome


def execute_login(session: Session, request: Request, form: LoginFormInput) -> LoginResult:
    clean_email = form.email.strip().lower()
    clean_password = form.password
    requested_mode = "admin" if form.login_mode.strip().lower() == "admin" else "login"
    clean_entity_id = form.entity_id.strip() if requested_mode == "admin" else ""
    login_data = {
        "entity_id": clean_entity_id,
    }

    if not clean_email or not clean_password:
        return LoginFailure(
            error="Informe email e palavra-passe.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    parsed_entity_id: int | None = None
    if requested_mode == "admin":
        if not clean_entity_id:
            return LoginFailure(
                error="Selecione a entidade para entrar como administrador.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            return LoginFailure(
                error="Entidade selecionada inválida.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectOutcome(url="/users/new", status_code=status.HTTP_302_FOUND)

    row = session.execute(
        select(
            User,
            Member.full_name,
        )
        .join(Member, Member.id == User.member_id)
        .where(func.lower(User.login_email) == clean_email)
    ).one_or_none()

    user = row[0] if row is not None else None
    user_full_name = str(row.full_name or "") if row is not None else ""

    if user is None or not verify_login_password_v1(
        user.login_email,
        clean_password,
        user.password_hash,
    ):
        return LoginFailure(
            error="Credenciais inválidas.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if user.account_status != UserAccountStatus.ACTIVE.value:
        return LoginFailure(
            error=f"Conta com estado '{user.account_status}'. Contacte o administrador.",
            email=clean_email,
            mode=requested_mode,
            login_data=login_data,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    current_user_is_admin = is_admin_user(session, user.id, user.login_email)
    if requested_mode == "admin" and not current_user_is_admin:
        return LoginFailure(
            error="Acesso administrativo disponível apenas para utilizadores administradores.",
            email=clean_email,
            mode="admin",
            login_data=login_data,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    selected_entity_context: dict[str, Any] | None = None

    if requested_mode == "admin":
        linked_entity_ids_rows = session.scalars(
            select(MemberEntity.entity_id)
            .where(
                MemberEntity.member_id == int(user.member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
            .order_by(MemberEntity.id.asc())
        ).all()

        linked_entity_ids = [
            int(linked_entity_id)
            for linked_entity_id in linked_entity_ids_rows
            if isinstance(linked_entity_id, int)
        ]

        if not linked_entity_ids:
            return LoginFailure(
                error="Utilizador sem entidade ativa associada.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if parsed_entity_id not in linked_entity_ids:
            return LoginFailure(
                error="Não é permitido entrar com uma entidade diferente da associada ao seu utilizador.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

        selected_entity_context = get_entity_context_for_user(
            session,
            user.id,
            user.login_email,
            parsed_entity_id,
        )

        if selected_entity_context is None:
            return LoginFailure(
                error="Não tem permissão para entrar na entidade selecionada.",
                email=clean_email,
                mode="admin",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )
    else:
        selected_entity_context = get_entity_context_for_user(
            session,
            user.id,
            user.login_email,
            None,
        )

        if selected_entity_context is None:
            return LoginFailure(
                error="Utilizador sem entidade ativa associada.",
                email=clean_email,
                mode="login",
                login_data=login_data,
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return LoginSuccess(
        user=user,
        user_full_name=user_full_name,
        selected_entity_context=selected_entity_context,
    )


@dataclass(frozen=True)
class SignupFailure:
    errors: list[str]
    signup_data: dict[str, Any]
    status_code: int


@dataclass(frozen=True)
class SignupSuccess:
    user: User
    clean_full_name: str
    clean_email: str
    parsed_entity_id: int | None
    resolved_language: str = field(default="")


SignupResult = SignupSuccess | SignupFailure | RedirectOutcome


def execute_signup(session: Session, request: Request, form: SignupFormInput) -> SignupResult:
    errors: list[str] = []
    clean_full_name = form.full_name.strip()
    clean_country = form.country.strip().upper()
    clean_primary_phone = form.primary_phone.strip()
    clean_email = form.email.strip().lower()
    clean_entity_id = form.entity_id.strip()

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
    if len(form.password) < 8:
        errors.append("A palavra-passe deve ter no minimo 8 caracteres.")
    if form.password != form.confirm_password:
        errors.append("A confirmação da palavra-passe não confere.")

    parsed_entity_id: int | None = None
    if clean_entity_id:
        try:
            parsed_entity_id = int(clean_entity_id)
        except ValueError:
            errors.append("Entidade inválida.")

    current_user = get_current_user(request, session)
    if current_user is not None:
        return RedirectOutcome(url="/users/new", status_code=status.HTTP_302_FOUND)

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
        return SignupFailure(
            errors=errors,
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
    user.password_hash = hash_password(form.password)
    user.account_status = UserAccountStatus.ACTIVE.value
    resolved_language, _ = resolve_user_language_after_auth(user, request)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return SignupFailure(
            errors=["Falha ao criar conta. Tente novamente."],
            signup_data=signup_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return SignupSuccess(
        user=user,
        clean_full_name=clean_full_name,
        clean_email=clean_email,
        parsed_entity_id=parsed_entity_id,
        resolved_language=resolved_language,
    )


def resolve_signup_entity_lock(session: Session, clean_entity_id: str) -> dict[str, Any]:
    signup_data = get_signup_defaults()
    linked_entity = session.get(Entity, int(clean_entity_id))
    if linked_entity is not None and linked_entity.is_active:
        signup_data["entity_id"] = clean_entity_id
        signup_data["entity_name"] = linked_entity.name or ""
        signup_data["entity_locked"] = "1"
    return signup_data
