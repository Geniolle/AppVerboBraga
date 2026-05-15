from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.core import ADMIN_PROFILE_NAMES
from appverbo.models import Profile, User, UserAccountStatus
from appverbo.services.auth import is_admin_user, is_allowed_global_profile
from appverbo.services.user_status import is_user_account_status_inactive_v1


# ###################################################################################
# (1) NORMALIZADORES E VALIDACOES BASE
# ###################################################################################

def allowed_entity_ids_from_permissions_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def ensure_actor_is_admin_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
) -> str:
    actor_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"] or "")

    if is_admin_user(session, actor_id, actor_login_email):
        return ""

    return "Apenas administradores podem gerir utilizadores."


def ensure_member_scope_v1(
    *,
    repository: Any,
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    allowed_entity_ids = allowed_entity_ids_from_permissions_v1(permissions)

    if not allowed_entity_ids:
        return "Sem permissão para gerir utilizadores nesta entidade."

    member_is_scoped = repository.member_is_within_allowed_entities(
        session=session,
        member_id=int(member_id),
        allowed_entity_ids=allowed_entity_ids,
    )

    if member_is_scoped:
        return ""

    return "Sem permissão para gerir este utilizador."


def ensure_not_self_delete_v1(*, actor_user_id: int, target_user_id: int) -> str:
    if int(actor_user_id) != int(target_user_id):
        return ""

    return "Não é permitido eliminar o próprio utilizador ligado."


def ensure_target_user_is_inactive_v1(user: User) -> str:
    if is_user_account_status_inactive_v1(user.account_status):
        return ""

    current_status = str(user.account_status or "").strip().lower() or "-"

    return (
        "Só é permitido eliminar utilizadores com estado Inativo. "
        f"Estado atual: {current_status}."
    )


def ensure_profile_allowed_v1(profile: Profile | None) -> str:
    if profile is None:
        return "Perfil selecionado não existe."

    if is_allowed_global_profile(profile):
        return ""

    return "Perfil global inválido. Escolha ADMIN, SUPER USER ou USER."


def is_admin_profile_v1(profile: Profile | None) -> bool:
    if profile is None:
        return False

    profile_name = str(profile.name or "").strip().lower()

    if not profile_name:
        return False

    return profile_name in ADMIN_PROFILE_NAMES


# ###################################################################################
# (2) PROTECOES DO ULTIMO ADMIN ATIVO
# ###################################################################################

def ensure_not_last_active_admin_for_member_v1(
    *,
    repository: Any,
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = repository.list_active_entity_ids_for_member(
        session=session,
        member_id=int(member_id),
    )

    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        has_other_admin = repository.has_other_active_admin_for_entity(
            session=session,
            entity_id=int(entity_id),
            excluded_user_id=int(excluded_user_id),
        )

        if has_other_admin:
            continue

        entity_name = repository.get_entity_name_by_id(
            session=session,
            entity_id=int(entity_id),
        )

        clean_entity_name = str(entity_name or f"ID {entity_id}")

        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{clean_entity_name}' ficaria sem Admin ativo."
            ),
        )

    return True, ""


def should_validate_last_admin_guard_v1(
    *,
    session: Session,
    user: User,
    resulting_account_status: str,
    resulting_profile: Profile | None,
) -> bool:
    current_is_active_admin = (
        str(user.account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
        and is_admin_user(session, int(user.id), str(user.login_email or ""))
    )

    resulting_is_active_admin = (
        str(resulting_account_status or "").strip().lower() == UserAccountStatus.ACTIVE.value
        and is_admin_profile_v1(resulting_profile)
    )

    return current_is_active_admin and not resulting_is_active_admin
