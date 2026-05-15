from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.models import Profile, UserAccountStatus
from appverbo.services.auth import get_or_create_entity_superuser_profile
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.users.outcome import UserActionOutcome
from appverbo.use_cases.users.policies import (
    ensure_actor_is_admin_v1,
    ensure_not_last_active_admin_for_member_v1,
    ensure_profile_allowed_v1,
    ensure_member_scope_v1,
    should_validate_last_admin_guard_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################

ALLOWED_ACCOUNT_STATUS = {
    UserAccountStatus.ACTIVE.value,
    UserAccountStatus.PENDING.value,
    UserAccountStatus.INACTIVE.value,
    UserAccountStatus.BLOCKED.value,
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


# ###################################################################################
# (2) NORMALIZACAO E REDIRECTS
# ###################################################################################

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
    clean_user_id = str(user_id or "").strip()
    clean_full_name = str(full_name or "").strip()
    clean_primary_phone = str(primary_phone or "").strip()
    clean_email = str(email or "").strip().lower()
    clean_entity_id = str(entity_id or "").strip()
    clean_account_status = str(account_status or "").strip().lower()
    clean_profile_id = str(profile_id or "").strip()

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


# ###################################################################################
# (3) VALIDACOES DE PERFIL E DUPLICIDADE
# ###################################################################################

def _resolve_selected_profile_v1(
    *,
    session: Session,
    repository: UserAdminRepository,
    clean_profile_id: str,
    errors: list[str],
) -> Profile | None:
    if not clean_profile_id:
        return None

    if not clean_profile_id.isdigit():
        errors.append("Perfil selecionado inválido.")
        return None

    profile = repository.get_profile_by_id(
        session=session,
        profile_id=int(clean_profile_id),
    )

    profile_error = ensure_profile_allowed_v1(profile)

    if profile_error:
        errors.append(profile_error)
        return None

    return profile


def _validate_duplicate_fields_v1(
    *,
    session: Session,
    repository: UserAdminRepository,
    user_id: int,
    member_id: int,
    email: str,
    errors: list[str],
) -> None:
    duplicate_member_id = repository.find_duplicate_member_id_by_email(
        session=session,
        email=email,
        excluded_member_id=member_id,
    )

    if duplicate_member_id is not None:
        errors.append("Já existe um membro com este email.")

    duplicate_user_id = repository.find_duplicate_user_id_by_email(
        session=session,
        login_email=email,
        excluded_user_id=user_id,
    )

    if duplicate_user_id is not None:
        errors.append("Já existe um utilizador com este email de login.")


# ###################################################################################
# (4) USE CASE PRINCIPAL
# ###################################################################################

def execute_update_user(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateUserInput | None = None,
    user_id: str = "",
    full_name: str = "",
    primary_phone: str = "",
    email: str = "",
    entity_id: str = "",
    account_status: str = "",
    profile_id: str = "",
) -> UserActionOutcome:
    normalized_payload = payload or normalize_update_user_input_v1(
        user_id=user_id,
        full_name=full_name,
        primary_phone=primary_phone,
        email=email,
        entity_id=entity_id,
        account_status=account_status,
        profile_id=profile_id,
    )

    if normalized_payload.errors and not normalized_payload.clean_user_id.isdigit():
        return _redirect_v1(error=" ".join(normalized_payload.errors))

    parsed_user_id = int(normalized_payload.clean_user_id)
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    admin_error = ensure_actor_is_admin_v1(
        session=session,
        actor_user=actor_user,
    )

    if admin_error:
        return _redirect_v1(error=admin_error)

    entity_permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    user, member = repository.get_user_and_member(
        session=session,
        user_id=parsed_user_id,
    )

    if user is None:
        return _redirect_v1(error="Utilizador não encontrado.")

    if member is None:
        return _redirect_v1(error="Membro associado ao utilizador não encontrado.")

    scope_error = ensure_member_scope_v1(
        repository=repository,
        session=session,
        member_id=int(member.id),
        permissions=entity_permissions,
    )

    if scope_error:
        return _redirect_v1(error=scope_error)

    errors = list(normalized_payload.errors)

    selected_entity, entity_error = repository.resolve_edit_entity(
        session=session,
        email=normalized_payload.clean_email,
        explicit_entity_id=normalized_payload.clean_entity_id,
        member_id=int(member.id),
        permissions=entity_permissions,
    )

    if selected_entity is None and entity_error:
        errors.append(entity_error)

    selected_profile = _resolve_selected_profile_v1(
        session=session,
        repository=repository,
        clean_profile_id=normalized_payload.clean_profile_id,
        errors=errors,
    )

    _validate_duplicate_fields_v1(
        session=session,
        repository=repository,
        user_id=int(user.id),
        member_id=int(member.id),
        email=normalized_payload.clean_email,
        errors=errors,
    )

    if errors:
        return _redirect_v1(
            error=" ".join(errors),
            user_edit_id=str(parsed_user_id),
            anchor="#edit-user-card",
        )

    if selected_profile is None:
        selected_profile = get_or_create_entity_superuser_profile(session)

    if should_validate_last_admin_guard_v1(
        session=session,
        user=user,
        resulting_account_status=normalized_payload.clean_account_status,
        resulting_profile=selected_profile,
    ):
        can_change, admin_error = ensure_not_last_active_admin_for_member_v1(
            repository=repository,
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

    repository.apply_user_update(
        session=session,
        user=user,
        member=member,
        full_name=normalized_payload.clean_full_name,
        primary_phone=normalized_payload.clean_primary_phone,
        login_email=normalized_payload.clean_email,
        account_status=normalized_payload.clean_account_status,
        selected_entity=selected_entity,
        selected_profile=selected_profile,
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


execute_update_user_v1 = execute_update_user
