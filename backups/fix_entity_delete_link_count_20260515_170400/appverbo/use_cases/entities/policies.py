from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.core import ENTITY_PROFILE_SCOPE_OWNER
from appverbo.models import Entity
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import is_entity_within_permissions


# ###################################################################################
# (1) POLÍTICAS DE PERMISSÃO E ESCOPO
# ###################################################################################

def ensure_actor_can_manage_entities_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
) -> str:
    actor_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"] or "")

    if is_admin_user(session, actor_id, actor_login_email):
        return ""

    return "Apenas administradores podem gerir entidades."


def ensure_actor_can_create_entity_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Apenas a entidade Owner pode criar novas entidades."


def ensure_entity_in_scope_v1(
    *,
    entity_id: int,
    permissions: dict[str, Any],
    action_label: str,
) -> str:
    if is_entity_within_permissions(int(entity_id), permissions):
        return ""

    clean_action = str(action_label or "gerir").strip().lower() or "gerir"
    return f"Sem permissão para {clean_action} esta entidade."


def ensure_can_set_owner_scope_v1(
    *,
    repository: Any,
    session: Session,
    target_profile_scope: str,
    permissions: dict[str, Any],
    ignore_entity_id: int | None = None,
) -> str:
    clean_scope = str(target_profile_scope or "").strip().lower()

    if clean_scope != ENTITY_PROFILE_SCOPE_OWNER:
        return ""

    if not permissions.get("can_manage_all_entities"):
        return "Apenas a entidade Owner pode definir perfil Owner."

    existing_owner_id = repository.find_existing_owner_entity_id(
        session=session,
        ignore_entity_id=ignore_entity_id,
    )

    if existing_owner_id is None:
        return ""

    return "Já existe outra entidade com perfil Owner. Apenas uma é permitida."


# ###################################################################################
# (2) POLÍTICAS DE ELIMINAÇÃO
# ###################################################################################

def ensure_delete_only_inactive_entity_v1(entity: Entity) -> str:
    if not bool(entity.is_active):
        return ""

    return "Só é permitido eliminar entidades inativas."


def ensure_entity_can_be_deleted_v1(
    *,
    repository: Any,
    session: Session,
    entity_id: int,
) -> str:
    linked_users_count = repository.count_linked_users(
        session=session,
        entity_id=int(entity_id),
    )

    if int(linked_users_count) <= 0:
        return ""

    return (
        "Não pode eliminar entidade com utilizadores associados. "
        "Inative a entidade primeiro."
    )

