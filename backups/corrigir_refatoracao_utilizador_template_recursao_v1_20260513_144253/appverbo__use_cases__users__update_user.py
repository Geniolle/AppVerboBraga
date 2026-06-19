
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.models import Profile, UserAccountStatus
from appverbo.repositories.member_entity_repository import upsert_active_member_entity_link
from appverbo.repositories.member_repository import get_duplicate_member_id_by_email_ci, get_member_by_id
from appverbo.repositories.user_profile_repository import replace_user_profile
from appverbo.repositories.user_repository import get_duplicate_user_id_by_email_ci, get_user_by_id
from appverbo.services.auth import get_or_create_entity_superuser_profile, is_admin_user, is_allowed_global_profile
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.resolve_user_entity import resolve_edit_entity_v1
from appverbo.use_cases.users.user_permissions import (
    ensure_not_last_active_admin_for_member_v1,
    is_admin_profile_v1,
    member_is_within_permissions_v1,
)


ALLOWED_ACCOUNT_STATUS = {
    UserAccountStatus.ACTIVE.value,
    UserAccountStatus.PENDING.value,
    UserAccountStatus.INACTIVE.value,
}


@dataclass(frozen=True)
class UpdateUserInput:
    clean_user_id: str
    clean_full_name: str
    clean_primary_phone: str
    clean_email: str
    clean_entity_id: str
    clean_account_status: str
    clean_profile_id: str
    errors: list[str]


def normalize_update_user_input_v1(
    *,
    user_id: str,
    full_name: str,
    primary_phone: str,
    email: str,
    entity_id: str,
    account_status: str,
    profile_id: str,
) -> UpdateUserInput:
    clean_user_id = user_id.strip()
    clean_full_name = full_name.strip()
    clean_primary_phone = primary_phone.strip()
    clean_email = email.strip().lower()
    clean_entity_id = entity_id.strip()
    clean_account_status = account_status.strip().lower()
    clean_profile_id = profile_id.strip()

    errors: list[str] = []

    if not clean_user_id.isdigit():
        errors.append("Utilizador inválido para edição.")

    if not clean_full_name:
        errors.append("Nome completo é obrigatório.")

    if not clean_primary_phone:
        errors.append("Telefone principal é obrigatório.")

    if not clean_email:
        errors.append("Email é obrigatório.")

    if clean_account_status not in ALLOWED_ACCOUNT_STATUS:
        errors.append("Estado de conta inválido.")

    return UpdateUserInput(
        clean_user_id=clean_user_id,
        clean_full_name=clean_full_name,
        clean_primary_phone=clean_primary_phone,
        clean_email=clean_email,
        clean_entity_id=clean_entity_id,
        clean_account_status=clean_account_status,
        clean_profile_id=clean_profile_id,
        errors=errors,
    )


def _redirect_v1(
    *,
    success: str = "",
    error: str = "",
    user_edit_id: str = "",
    anchor: str = "#create-user-card",
) -> UserActionOutcome:
    kwargs: dict[str, str] = {
        "success": success,
        "error": error,
        "menu": "administrativo",
        "admin_tab": "utilizador",
    }

    if user_edit_id:
        kwargs["user_edit_id"] = user_edit_id

    return UserActionOutcome(
        kind="redirect",
        redirect_url=build_users_new_url(**kwargs) + anchor,
    )


def execute_update_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateUserInput,
) -> UserActionOutcome:
    if payload.errors and not payload.clean_user_id.isdigit():
        return _redirect_v1(error=" ".join(payload.errors))

    parsed_user_id = int(payload.clean_user_id)

    if not is_admin_user(session, int(actor_user["id"]), str(actor_user["login_email"])):
        return _redirect_v1(error="Apenas administradores podem editar utilizadores.")

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user = get_user_by_id(session, parsed_user_id)

    if user is None:
        return _redirect_v1(error="Utilizador não encontrado.")

    if not member_is_within_permissions_v1(
        session=session,
        member_id=int(user.member_id),
        permissions=entity_permissions,
    ):
        return _redirect_v1(error="Sem permissão para editar este utilizador.")

    member = get_member_by_id(session, int(user.member_id))

    if member is None:
        return _redirect_v1(error="Membro associado ao utilizador não encontrado.")

    errors = list(payload.errors)

    selected_entity, entity_resolution_error = resolve_edit_entity_v1(
        session=session,
        email=payload.clean_email,
        clean_entity_id=payload.clean_entity_id,
        member_id=int(member.id),
        permissions=entity_permissions,
    )

    if selected_entity is None and entity_resolution_error:
        errors.append(entity_resolution_error)

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

    duplicate_member_id = get_duplicate_member_id_by_email_ci(
        session=session,
        email=payload.clean_email,
        excluded_member_id=int(member.id),
    )

    if duplicate_member_id is not None:
        errors.append("Já existe um membro com este email.")

    duplicate_user_id = get_duplicate_user_id_by_email_ci(
        session=session,
        login_email=payload.clean_email,
        excluded_user_id=int(user.id),
    )

    if duplicate_user_id is not None:
        errors.append("Já existe um utilizador com este email de login.")

    if errors:
        return _redirect_v1(
            error=" ".join(errors),
            user_edit_id=str(parsed_user_id),
            anchor="#edit-user-card",
        )

    if selected_profile is None:
        selected_profile = get_or_create_entity_superuser_profile(session)

    current_is_active_admin = (
        str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
        and is_admin_user(session, int(user.id), str(user.login_email or ""))
    )
    resulting_is_active_admin = (
        payload.clean_account_status == UserAccountStatus.ACTIVE.value
        and is_admin_profile_v1(selected_profile)
    )

    if current_is_active_admin and not resulting_is_active_admin:
        can_change, admin_error = ensure_not_last_active_admin_for_member_v1(
            session=session,
            member_id=int(user.member_id),
            excluded_user_id=int(user.id),
        )

        if not can_change:
            return _redirect_v1(
                error=admin_error,
                user_edit_id=str(parsed_user_id),
                anchor="#edit-user-card",
            )

    member.full_name = payload.clean_full_name
    member.primary_phone = payload.clean_primary_phone
    member.email = payload.clean_email

    user.login_email = payload.clean_email
    user.account_status = payload.clean_account_status

    if selected_entity is not None:
        upsert_active_member_entity_link(
            session=session,
            member_id=int(member.id),
            entity_id=int(selected_entity.id),
            replace_primary=True,
        )

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
        return _redirect_v1(
            error="Não foi possível atualizar utilizador.",
            user_edit_id=str(parsed_user_id),
            anchor="#edit-user-card",
        )

    return _redirect_v1(success="Utilizador atualizado com sucesso.")
