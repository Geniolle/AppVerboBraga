from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from fastapi import Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.domains.auth.repositories import resolve_invite_entity_for_member
from appgenesis.domains.auth.schemas import (
    InviteAcceptSubmitFormInput,
    LoginFormInput,
    SignupFormInput,
)
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
from appgenesis.services.phone_country import (
    normalize_country_code,
    normalize_phone_value,
    validate_phone_prefix_for_country,
)
from appgenesis.services.profile import format_optional_date_pt, parse_optional_date_pt
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


@dataclass(frozen=True)
class OAuthCallbackFailure:
    error: str


@dataclass(frozen=True)
class OAuthCallbackSuccess:
    user: User
    full_name: str
    clean_email: str
    resolved_language: str = field(default="")


OAuthCallbackResult = OAuthCallbackSuccess | OAuthCallbackFailure


def execute_oauth_callback(
    session: Session, request: Request, userinfo: dict[str, Any]
) -> OAuthCallbackResult:
    email = (
        userinfo.get("email")
        or userinfo.get("preferred_username")
        or userinfo.get("upn")
        or ""
    ).strip().lower()
    if not email:
        return OAuthCallbackFailure(error="O provedor não devolveu email.")

    full_name = (
        userinfo.get("name")
        or userinfo.get("given_name")
        or email.split("@")[0]
    )

    existing_user = session.execute(
        select(User.id, User.account_status).where(func.lower(User.login_email) == email)
    ).one_or_none()
    if existing_user is not None and existing_user.account_status != UserAccountStatus.ACTIVE.value:
        return OAuthCallbackFailure(
            error=f"Conta com estado '{existing_user.account_status}'. Contacte o administrador."
        )

    try:
        user = upsert_user_by_email(
            session=session,
            email=email,
            full_name=full_name,
            primary_phone="N/D",
            entity_id=None,
        )
        user.account_status = UserAccountStatus.ACTIVE.value
        resolved_language, _ = resolve_user_language_after_auth(user, request)
        session.commit()
    except IntegrityError:
        session.rollback()
        return OAuthCallbackFailure(error="Falha ao concluir login externo.")

    return OAuthCallbackSuccess(
        user=user,
        full_name=full_name,
        clean_email=email,
        resolved_language=resolved_language,
    )


@dataclass(frozen=True)
class InvitePageInvalid:
    error: str
    status_code: int


@dataclass(frozen=True)
class InvitePageAlreadyActive:
    pass


@dataclass(frozen=True)
class InvitePageReady:
    form_data: dict[str, str]


InvitePageResult = InvitePageInvalid | InvitePageAlreadyActive | InvitePageReady


def resolve_invite_accept_page(
    session: Session, invite_payload: dict[str, Any]
) -> InvitePageResult:
    user = session.get(User, int(invite_payload["uid"]))
    if user is None or (user.login_email or "").strip().lower() != invite_payload["email"]:
        return InvitePageInvalid(
            error="Convite inválido. Utilizador não encontrado.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if user.account_status != UserAccountStatus.PENDING.value:
        return InvitePageAlreadyActive()

    member = session.get(Member, user.member_id)
    if member is None:
        return InvitePageInvalid(
            error="Membro associado ao convite não foi encontrado.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    _, entity_name = resolve_invite_entity_for_member(
        session,
        int(member.id),
        invite_payload.get("entity_id"),
    )

    return InvitePageReady(
        form_data={
            "full_name": member.full_name or "",
            "country": normalize_country_code(member.country or ""),
            "primary_phone": member.primary_phone or "",
            "address": member.address or "",
            "city": member.city or "",
            "freguesia": member.freguesia or "",
            "postal_code": member.postal_code or "",
            "birth_date": format_optional_date_pt(member.birth_date),
            "entity_name": entity_name,
            "email": user.login_email or "",
        }
    )


@dataclass(frozen=True)
class InviteAcceptInvalid:
    error: str
    form_data: dict[str, str]
    status_code: int


@dataclass(frozen=True)
class InviteAcceptAlreadyActive:
    pass


@dataclass(frozen=True)
class InviteAcceptSuccess:
    user: User
    member: Member
    invite_entity_id: int | None


InviteAcceptResult = InviteAcceptInvalid | InviteAcceptAlreadyActive | InviteAcceptSuccess


def execute_invite_accept(
    session: Session,
    form: InviteAcceptSubmitFormInput,
    invite_payload: dict[str, Any],
) -> InviteAcceptResult:
    clean_full_name = form.full_name.strip()
    clean_primary_phone = normalize_phone_value(form.primary_phone)
    clean_country = normalize_country_code(form.country)
    clean_address = form.address.strip()
    clean_city = form.city.strip()
    clean_freguesia = form.freguesia.strip()
    clean_postal_code = form.postal_code.strip()
    clean_birth_date = form.birth_date.strip()

    form_data: dict[str, str] = {
        "full_name": clean_full_name,
        "country": clean_country,
        "primary_phone": clean_primary_phone,
        "address": clean_address,
        "city": clean_city,
        "freguesia": clean_freguesia,
        "postal_code": clean_postal_code,
        "birth_date": clean_birth_date,
        "entity_name": "",
        "email": invite_payload["email"],
    }

    errors: list[str] = []
    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    phone_country_error = validate_phone_prefix_for_country(clean_country, clean_primary_phone)
    if phone_country_error:
        errors.append(phone_country_error)
    if not clean_address:
        errors.append("Morada é obrigatória.")
    if not clean_city:
        errors.append("Cidade é obrigatória.")
    if not clean_freguesia:
        errors.append("Freguesia é obrigatória.")
    if not clean_postal_code:
        errors.append("Código postal é obrigatório.")
    if len(form.password) < 8:
        errors.append("A palavra-passe deve ter no mínimo 8 caracteres.")
    if form.password != form.confirm_password:
        errors.append("A confirmação da palavra-passe não confere.")

    parsed_birth_date: date | None = None
    if clean_birth_date:
        try:
            parsed_birth_date = parse_optional_date_pt(clean_birth_date)
        except ValueError:
            errors.append("Data de nascimento inválida. Use o formato dd/mm/aaaa.")

    user = session.get(User, int(invite_payload["uid"]))
    if user is None or (user.login_email or "").strip().lower() != invite_payload["email"]:
        return InviteAcceptInvalid(
            error="Convite inválido. Utilizador não encontrado.",
            form_data=form_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if user.account_status != UserAccountStatus.PENDING.value:
        return InviteAcceptAlreadyActive()

    member = session.get(Member, user.member_id)
    if member is None:
        return InviteAcceptInvalid(
            error="Membro associado ao convite não foi encontrado.",
            form_data=form_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    invite_entity_id, invite_entity_name = resolve_invite_entity_for_member(
        session,
        int(member.id),
        invite_payload.get("entity_id"),
    )
    form_data["entity_name"] = invite_entity_name
    form_data["email"] = user.login_email or ""

    if errors:
        return InviteAcceptInvalid(
            error=" ".join(errors),
            form_data=form_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    member.full_name = clean_full_name
    member.primary_phone = clean_primary_phone
    member.country = clean_country or None
    member.address = clean_address
    member.city = clean_city
    member.freguesia = clean_freguesia
    member.postal_code = clean_postal_code
    member.birth_date = parsed_birth_date
    user.password_hash = hash_password(form.password)
    user.account_status = UserAccountStatus.ACTIVE.value

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return InviteAcceptInvalid(
            error="Não foi possível concluir a ativação da conta. Tente novamente.",
            form_data=form_data,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return InviteAcceptSuccess(user=user, member=member, invite_entity_id=invite_entity_id)
