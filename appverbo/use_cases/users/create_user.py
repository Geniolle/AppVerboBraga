from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from appverbo.services.auth import (
    build_user_invite_link,
    build_user_invite_token,
    get_or_create_entity_superuser_profile,
    hash_password,
    is_admin_user,
    is_allowed_global_profile,
    send_user_invite_email,
)
from appverbo.services.page import (
    build_users_new_url,
    get_entity_edit_defaults,
    get_entity_form_defaults,
    get_next_entity_internal_number,
    get_page_data,
    get_user_edit_defaults,
)
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.profile import get_user_personal_data


def _extract_email_domain(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()
    if "@" not in clean_email:
        return ""
    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _resolve_entity_from_user_email(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return None, "Email inválido para determinar entidade."

    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
    if not permissions.get("can_manage_all_entities"):
        allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
        if not allowed_entity_ids:
            return None, "Sem entidades disponíveis para este utilizador."
        query = query.where(Entity.id.in_(allowed_entity_ids))

    scoped_entities = list(session.execute(query).scalars().all())
    if not scoped_entities:
        return None, "Sem entidades ativas disponíveis para atribuição."

    exact_matches = [
        entity
        for entity in scoped_entities
        if (entity.email or "").strip().lower() == clean_email
    ]
    if len(exact_matches) == 1:
        return exact_matches[0], ""
    if len(exact_matches) > 1:
        return (
            None,
            "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades.",
        )

    email_domain = _extract_email_domain(clean_email)
    if email_domain:
        domain_matches = [
            entity
            for entity in scoped_entities
            if _extract_email_domain((entity.email or "").strip().lower()) == email_domain
        ]
        if len(domain_matches) == 1:
            return domain_matches[0], ""
        if len(domain_matches) > 1:
            return (
                None,
                "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades.",
            )

    if not permissions.get("can_manage_all_entities") and len(scoped_entities) == 1:
        return scoped_entities[0], ""

    return (
        None,
        "Não foi possível determinar a entidade pelo email. "
        "Verifique o email da entidade (domínio) ou ajuste os dados.",
    )


def _get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    entity_row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()
    if entity_row is None:
        return None, "-"
    return int(entity_row.id), str(entity_row.name or "-")


def _member_is_within_permissions(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True
    allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
    if not allowed_entity_ids:
        return False
    scoped_link_id = session.scalar(
        select(MemberEntity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_entity_ids),
        )
        .limit(1)
    )
    return scoped_link_id is not None


@dataclass(frozen=True)
class CreateUserInput:
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_profile_id: str
    clean_invite_delivery: str
    form_data: dict[str, str]
    errors: list[str]


@dataclass(frozen=True)
class CreateUserOutcome:
    kind: str
    redirect_url: str = ""
    redirect_status_code: int = 303
    template_context: dict[str, Any] | None = None
    template_status_code: int = 400


def normalize_create_user_input(
    *,
    full_name: str,
    primary_phone: str,
    email: str,
    profile_id: str,
    invite_delivery: str,
) -> CreateUserInput:
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_profile_id = profile_id.strip()
    clean_invite_delivery = invite_delivery.strip().lower()
    if clean_invite_delivery not in {"email", "link"}:
        clean_invite_delivery = "email"

    form_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": "",
        "entity_name": "",
        "profile_id": clean_profile_id,
    }

    errors: list[str] = []
    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")
    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")
    if not clean_email:
        errors.append("Email é obrigatório.")

    return CreateUserInput(
        clean_full_name=clean_full_name,
        clean_primary_phone=clean_primary_phone,
        clean_email=clean_email,
        clean_profile_id=clean_profile_id,
        clean_invite_delivery=clean_invite_delivery,
        form_data=form_data,
        errors=errors,
    )


def _build_error_context(
    *,
    request: Request,
    errors: list[str],
    form_data: dict[str, str],
    current_user: dict[str, Any],
    current_user_is_admin: bool,
    can_manage_all_entities: bool,
    user_personal_data: dict[str, Any],
    next_entity_internal_number: int,
    page_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "request": request,
        "errors": errors,
        "success": "",
        "form_data": form_data,
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": get_entity_edit_defaults(),
        "user_edit_data": get_user_edit_defaults(),
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "current_user_can_manage_all_entities": bool(can_manage_all_entities),
        "user_personal_data": user_personal_data,
        "entity_success": "",
        "entity_error": "",
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": "",
        "profile_error": "",
        "profile_tab": "pessoal",
        "initial_menu": "administrativo",
        "admin_tab": "utilizador",
        **page_data,
    }


def execute_create_user(
    *,
    session: Session,
    request: Request,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: CreateUserInput,
) -> CreateUserOutcome:
    current_user_is_admin = bool(
        is_admin_user(
            session,
            int(actor_user["id"]),
            str(actor_user["login_email"]),
        )
    )
    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )
    page_data = get_page_data(
        session,
        actor_user_id=int(actor_user["id"]),
        actor_login_email=str(actor_user["login_email"]),
        selected_entity_id=selected_entity_id,
    )
    user_personal_data = get_user_personal_data(
        session, int(actor_user["id"]), selected_entity_id
    )
    next_entity_internal_number = get_next_entity_internal_number(session)

    if not current_user_is_admin:
        return CreateUserOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                error="Apenas administradores podem criar utilizadores.",
                menu="perfil",
            ),
        )

    errors = list(payload.errors)
    form_data = dict(payload.form_data)
    selected_entity = None

    selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
        session,
        payload.clean_email,
        entity_permissions,
    )
    if selected_entity is not None:
        form_data["entity_id"] = str(selected_entity.id)
        form_data["entity_name"] = selected_entity.name or ""
    elif entity_resolution_error:
        errors.append(entity_resolution_error)

    existing_member: Member | None = None
    existing_user_row: Any | None = None
    if payload.clean_email:
        existing_member = session.execute(
            select(Member).where(func.lower(Member.email) == payload.clean_email)
        ).scalar_one_or_none()
        existing_user_row = session.execute(
            select(User.id, User.account_status, User.login_email, User.member_id).where(
                func.lower(User.login_email) == payload.clean_email
            )
        ).one_or_none()

        if existing_user_row is not None:
            existing_user_entity_id, existing_user_entity_name = _get_primary_entity_for_member(
                session,
                int(existing_user_row.member_id),
            )
            can_manage_existing_user = _member_is_within_permissions(
                session,
                int(existing_user_row.member_id),
                entity_permissions,
            )
            if not can_manage_existing_user:
                errors.append("Sem permissão para gerir utilizador com este email.")
                existing_user_row = None
            else:
                linked_entity_name = (
                    selected_entity.name
                    if selected_entity is not None
                    else existing_user_entity_name
                )
                linked_entity_id = (
                    int(selected_entity.id)
                    if selected_entity is not None
                    else existing_user_entity_id
                )

        if existing_user_row is not None:
            existing_status = str(existing_user_row.account_status or "").strip().lower()
            if existing_status == UserAccountStatus.PENDING.value:
                invite_token = build_user_invite_token(
                    int(existing_user_row.id),
                    str(existing_user_row.login_email),
                    linked_entity_id,
                )
                invite_link = build_user_invite_link(request, invite_token)
                if payload.clean_invite_delivery == "link":
                    return CreateUserOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Link de ativação gerado.",
                            invite_link=invite_link,
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )
                email_sent, email_error = send_user_invite_email(
                    recipient_email=payload.clean_email,
                    recipient_name=payload.clean_full_name,
                    entity_name=linked_entity_name,
                    invite_link=invite_link,
                    invited_by_name=str(actor_user["full_name"]),
                )
                if email_sent:
                    return CreateUserOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Convite reenviado por email.",
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )
                return CreateUserOutcome(
                    kind="redirect",
                    redirect_url=build_users_new_url(
                        success="Utilizador já estava pendente.",
                        error=f"{email_error} Link de ativação: {invite_link}",
                        menu="administrativo",
                        admin_tab="utilizador",
                    )
                    + "#create-user-card",
                )
            errors.append("Já existe um utilizador com este email de login.")

        if existing_member is not None and existing_user_row is None:
            existing_member_entity_id, _ = _get_primary_entity_for_member(
                session,
                int(existing_member.id),
            )
            if (
                existing_member_entity_id is not None
                and not _member_is_within_permissions(
                    session,
                    int(existing_member.id),
                    entity_permissions,
                )
            ):
                errors.append("Sem permissão para utilizar este email noutra entidade.")
                existing_member = None

    selected_profile: Profile | None = None
    if payload.clean_profile_id:
        try:
            selected_profile = session.get(Profile, int(payload.clean_profile_id))
        except ValueError:
            errors.append("Perfil selecionado inválido.")
        if selected_profile is None and not errors:
            errors.append("Perfil selecionado não existe.")
        elif not is_allowed_global_profile(selected_profile):
            errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

    if errors:
        return CreateUserOutcome(
            kind="template",
            template_context=_build_error_context(
                request=request,
                errors=errors,
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_internal_number=next_entity_internal_number,
                page_data=page_data,
            ),
        )

    if selected_profile is None:
        selected_profile = get_or_create_entity_superuser_profile(session)

    if existing_member is None:
        member = Member(
            full_name=payload.clean_full_name,
            primary_phone=payload.clean_primary_phone,
            email=payload.clean_email,
            member_status=MemberStatus.ACTIVE.value,
            is_collaborator=True,
        )
        session.add(member)
        session.flush()
    else:
        member = existing_member
        member.full_name = payload.clean_full_name
        member.primary_phone = payload.clean_primary_phone
        member.email = payload.clean_email
        member.member_status = MemberStatus.ACTIVE.value
        member.is_collaborator = True

    existing_member_link = session.execute(
        select(MemberEntity)
        .where(
            MemberEntity.member_id == member.id,
            MemberEntity.entity_id == selected_entity.id,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if existing_member_link is None:
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=selected_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
                entry_date=date.today(),
            )
        )
    else:
        existing_member_link.status = MemberEntityStatus.ACTIVE.value
        if existing_member_link.entry_date is None:
            existing_member_link.entry_date = date.today()

    user = User(
        member_id=member.id,
        login_email=payload.clean_email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        account_status=UserAccountStatus.PENDING.value,
        created_by_user_id=int(actor_user["id"]),
    )
    session.add(user)
    session.flush()

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
        return CreateUserOutcome(
            kind="template",
            template_context=_build_error_context(
                request=request,
                errors=[
                    "Falha ao gravar no banco. Verifique dados duplicados e tente novamente."
                ],
                form_data=form_data,
                current_user=actor_user,
                current_user_is_admin=current_user_is_admin,
                can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
                user_personal_data=user_personal_data,
                next_entity_internal_number=next_entity_internal_number,
                page_data=page_data,
            ),
        )

    invite_token = build_user_invite_token(
        user.id,
        user.login_email,
        int(selected_entity.id) if selected_entity is not None else None,
    )
    invite_link = build_user_invite_link(request, invite_token)
    if payload.clean_invite_delivery == "link":
        return CreateUserOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Link de ativação gerado.",
                invite_link=invite_link,
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    email_sent, email_error = send_user_invite_email(
        recipient_email=payload.clean_email,
        recipient_name=payload.clean_full_name,
        entity_name=selected_entity.name if selected_entity is not None else "",
        invite_link=invite_link,
        invited_by_name=str(actor_user["full_name"]),
    )
    if email_sent:
        return CreateUserOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Convite enviado por email.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    return CreateUserOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success="Utilizador criado em estado pendente.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
    )
