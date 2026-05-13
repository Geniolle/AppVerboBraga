
from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.models import Entity, Member, MemberStatus, Profile, User, UserAccountStatus
from appverbo.repositories.member_entity_repository import get_primary_entity_for_member, upsert_active_member_entity_link
from appverbo.repositories.member_repository import get_member_by_email_ci
from appverbo.repositories.user_profile_repository import replace_user_profile
from appverbo.repositories.user_repository import get_user_by_email_ci
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
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.resolve_user_entity import resolve_entity_from_user_email_v1
from appverbo.use_cases.users.user_permissions import member_is_within_permissions_v1


@dataclass(frozen=True)
class CreateUserInput:
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_profile_id: str
    clean_invite_delivery: str
    form_data: dict[str, str]
    errors: list[str]


CreateUserOutcome = UserActionOutcome


def normalize_create_user_input_v1(
    *,
    full_name: str,
    primary_phone: str,
    email: str,
    entity_id: str = "",
    profile_id: str = "",
    invite_delivery: str = "email",
) -> CreateUserInput:
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = entity_id.strip()
    clean_profile_id = profile_id.strip()
    clean_invite_delivery = invite_delivery.strip().lower()

    if clean_invite_delivery not in {"email", "link"}:
        clean_invite_delivery = "email"

    form_data = {
        "full_name": clean_full_name,
        "primary_phone": clean_primary_phone,
        "email": clean_email,
        "entity_id": clean_entity_id,
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


normalize_create_user_input = normalize_create_user_input_v1


def _build_error_context_v1(
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
        "generated_invite_link": "",
        "form_data": form_data,
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": get_entity_edit_defaults(),
        "user_edit_data": get_user_edit_defaults(),
        "entity_readonly_mode": False,
        "user_readonly_mode": False,
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "current_user_can_manage_all_entities": bool(can_manage_all_entities),
        "user_personal_data": user_personal_data,
        "entity_success": "",
        "entity_error": "",
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": "",
        "profile_error": "",
        "settings_success": "",
        "settings_error": "",
        "settings_edit_data": None,
        "settings_edit_key": "",
        "settings_action": "edit",
        "settings_tab": "",
        "profile_tab": "pessoal",
        "initial_menu": "administrativo",
        "initial_menu_target": "#create-user-card",
        "initial_dynamic_process_section": "",
        "initial_profile_section": "",
        "requested_profile_section": "",
        "requested_dynamic_process_section": "",
        "appverbo_after_save": False,
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
    explicit_entity_id: int | None = None,
) -> CreateUserOutcome:
    actor_user_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"])

    current_user_is_admin = bool(
        is_admin_user(session, actor_user_id, actor_login_email)
    )

    permission_entity_id = (
        explicit_entity_id if explicit_entity_id is not None else selected_entity_id
    )

    entity_permissions = get_user_entity_permissions(
        session,
        actor_user_id,
        actor_login_email,
        permission_entity_id,
    )

    page_data = get_page_data(
        session,
        actor_user_id=actor_user_id,
        actor_login_email=actor_login_email,
        selected_entity_id=selected_entity_id,
    )

    user_personal_data = get_user_personal_data(
        session,
        actor_user_id,
        selected_entity_id,
    )

    next_entity_internal_number = get_next_entity_internal_number(session)

    if not current_user_is_admin:
        return UserActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                error="Apenas administradores podem criar utilizadores.",
                menu="perfil",
            ),
        )

    errors = list(payload.errors)
    form_data = dict(payload.form_data)

    if explicit_entity_id is not None:
        selected_entity = session.get(Entity, int(explicit_entity_id))
        entity_resolution_error = ""

        if selected_entity is None or not selected_entity.is_active:
            selected_entity = None
            entity_resolution_error = "Entidade selecionada inválida ou inativa."
        elif not entity_permissions.get("can_manage_all_entities"):
            allowed_entity_ids = {
                int(raw_id)
                for raw_id in (entity_permissions.get("allowed_entity_ids") or set())
                if str(raw_id).strip().isdigit()
            }

            if int(selected_entity.id) not in allowed_entity_ids:
                selected_entity = None
                entity_resolution_error = "Sem permissão para utilizar a entidade selecionada."
    else:
        selected_entity, entity_resolution_error = resolve_entity_from_user_email_v1(
            session=session,
            user_email=payload.clean_email,
            permissions=entity_permissions,
            selected_entity_id=permission_entity_id,
        )

    if selected_entity is not None:
        form_data["entity_id"] = str(selected_entity.id)
        form_data["entity_name"] = selected_entity.name or ""
    elif entity_resolution_error:
        errors.append(entity_resolution_error)

    existing_member = get_member_by_email_ci(session, payload.clean_email)
    existing_user = get_user_by_email_ci(session, payload.clean_email)

    if existing_user is not None:
        existing_entity_id, existing_entity_name = get_primary_entity_for_member(
            session,
            int(existing_user.member_id),
        )
        can_manage_existing = member_is_within_permissions_v1(
            session=session,
            member_id=int(existing_user.member_id),
            permissions=entity_permissions,
        )

        if not can_manage_existing:
            errors.append("Sem permissão para gerir utilizador com este email.")
            existing_user = None
        else:
            linked_entity_name = (
                selected_entity.name
                if selected_entity is not None
                else existing_entity_name
            )
            linked_entity_id = (
                int(selected_entity.id)
                if selected_entity is not None
                else existing_entity_id
            )

            existing_status = str(existing_user.account_status or "").strip().lower()

            if existing_status == UserAccountStatus.PENDING.value:
                invite_token = build_user_invite_token(
                    int(existing_user.id),
                    str(existing_user.login_email),
                    linked_entity_id,
                )
                invite_link = build_user_invite_link(request, invite_token)

                if payload.clean_invite_delivery == "link":
                    return UserActionOutcome(
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
                    return UserActionOutcome(
                        kind="redirect",
                        redirect_url=build_users_new_url(
                            success="Utilizador já estava pendente. Convite reenviado por email.",
                            menu="administrativo",
                            admin_tab="utilizador",
                        )
                        + "#create-user-card",
                    )

                return UserActionOutcome(
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

    if existing_member is not None and existing_user is None:
        can_manage_member = member_is_within_permissions_v1(
            session=session,
            member_id=int(existing_member.id),
            permissions=entity_permissions,
        )
        existing_entity_id, _ = get_primary_entity_for_member(session, int(existing_member.id))

        if existing_entity_id is not None and not can_manage_member:
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
        elif selected_profile is not None and not is_allowed_global_profile(selected_profile):
            errors.append("Perfil global inválido. Escolha ADMIN, SUPER USER ou USER.")

    if errors:
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
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

    if selected_entity is None:
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
                request=request,
                errors=["Não foi possível determinar a entidade do utilizador."],
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

    upsert_active_member_entity_link(
        session=session,
        member_id=int(member.id),
        entity_id=int(selected_entity.id),
        replace_primary=False,
    )

    user = User(
        member_id=int(member.id),
        login_email=payload.clean_email,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        account_status=UserAccountStatus.PENDING.value,
        created_by_user_id=actor_user_id,
    )
    session.add(user)
    session.flush()

    replace_user_profile(
        session=session,
        user_id=int(user.id),
        profile_id=int(selected_profile.id),
        is_active=True,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return UserActionOutcome(
            kind="template",
            template_context=_build_error_context_v1(
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
        int(user.id),
        str(user.login_email),
        int(selected_entity.id),
    )
    invite_link = build_user_invite_link(request, invite_token)

    if payload.clean_invite_delivery == "link":
        return UserActionOutcome(
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
        entity_name=selected_entity.name or "",
        invite_link=invite_link,
        invited_by_name=str(actor_user["full_name"]),
    )

    if email_sent:
        return UserActionOutcome(
            kind="redirect",
            redirect_url=build_users_new_url(
                success="Utilizador criado em estado pendente. Convite enviado por email.",
                menu="administrativo",
                admin_tab="utilizador",
            )
            + "#create-user-card",
        )

    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(
            success="Utilizador criado em estado pendente.",
            error=f"{email_error} Link de ativação: {invite_link}",
            menu="administrativo",
            admin_tab="utilizador",
        )
        + "#create-user-card",
    )
