from __future__ import annotations

from typing import Any

from appverbo.core import *  # noqa: F403,F401

def owner_entity_exists(session: Session) -> bool:
    # ###################################################################################
    # (1) CONSIDERAR APENAS OWNER ATIVA
    # ###################################################################################
    # Uma Owner inativa nao pode bloquear o fallback administrativo global.
    owner_id = session.scalar(
        select(Entity.id)
       .where(
            Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER,
            Entity.is_active.is_(True),
        )
       .limit(1)
    )
    return owner_id is not None

def user_has_owner_entity_membership(session: Session, user_id: int) -> bool:
    owner_link_id = session.scalar(
        select(MemberEntity.id)
       .join(Entity, Entity.id == MemberEntity.entity_id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER,
            Entity.is_active.is_(True),
        )
       .limit(1)
    )
    return owner_link_id is not None

def _get_user_linked_entity_ids(
    session: Session,
    user_id: int,
    *,
    require_active_entity: bool = True,
) -> list[int]:
    stmt = (
        select(MemberEntity.entity_id)
       .join(User, User.member_id == MemberEntity.member_id)
       .join(Entity, Entity.id == MemberEntity.entity_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
       .order_by(MemberEntity.id.asc())
    )
    if require_active_entity:
        stmt = stmt.where(Entity.is_active.is_(True))

    raw_ids = session.execute(stmt).scalars().all()
    ordered_unique_ids: list[int] = []
    seen_ids: set[int] = set()
    for raw_id in raw_ids:
        parsed_id = int(raw_id)
        if parsed_id in seen_ids:
            continue
        seen_ids.add(parsed_id)
        ordered_unique_ids.append(parsed_id)
    return ordered_unique_ids

def get_user_entity_permissions(
    session: Session,
    user_id: int,
    login_email: str,
    selected_entity_id: int | None = None,
) -> dict[str, Any]:
    from appverbo.services.auth import is_admin_user

    is_admin = is_admin_user(session, user_id, login_email)
    has_owner_membership = user_has_owner_entity_membership(session, user_id)
    has_bootstrap_owner_gap = is_admin and not owner_entity_exists(session)

    # Owner é gestora da estrutura do tenant, não administradora global dos dados das entidades Legado.
    # can_manage_tenant_structure = pode criar/gerir estrutura (entidades, admins iniciais),
    # mas NÃO autoriza leitura de dados operacionais das entidades Legado.
    can_manage_tenant_structure = is_admin and (has_owner_membership or has_bootstrap_owner_gap)
    can_create_legacy_entities = can_manage_tenant_structure
    can_create_legacy_admin_users = can_manage_tenant_structure

    linked_entity_ids = _get_user_linked_entity_ids(
        session,
        user_id,
        require_active_entity=True,
    )
    linked_entity_ids_set = set(linked_entity_ids)

    resolved_selected_entity_id: int | None = None
    if selected_entity_id is not None:
        selected_entity = session.get(Entity, selected_entity_id)
        if selected_entity is not None and selected_entity.is_active:
            if can_manage_tenant_structure or selected_entity_id in linked_entity_ids_set:
                resolved_selected_entity_id = int(selected_entity_id)
    if resolved_selected_entity_id is None and linked_entity_ids:
        resolved_selected_entity_id = linked_entity_ids[0]
    if resolved_selected_entity_id is None and can_manage_tenant_structure:
        first_active_entity_id = session.scalar(
            select(Entity.id)
           .where(Entity.is_active.is_(True))
           .order_by(Entity.name.asc())
           .limit(1)
        )
        if first_active_entity_id is not None:
            resolved_selected_entity_id = int(first_active_entity_id)

    # allowed_structure_entity_ids: escopo estrutural do tenant.
    # Gestora do tenant vê todas as entidades para administração estrutural.
    # Entidades Legado veem apenas a própria entidade.
    if can_manage_tenant_structure:
        allowed_structure_entity_ids = {
            int(raw_id) for raw_id in session.execute(select(Entity.id)).scalars().all()
        }
    elif resolved_selected_entity_id is not None:
        allowed_structure_entity_ids = {resolved_selected_entity_id}
    else:
        allowed_structure_entity_ids = set()

    # allowed_data_entity_ids: escopo de dados operacionais.
    # Determinado pelas entidades onde o utilizador tem vínculo ativo,
    # independentemente de ser gestora do tenant.
    # A gestora do tenant NÃO acede automaticamente a dados operacionais das entidades Legado.
    if linked_entity_ids_set:
        allowed_data_entity_ids: set[int] = linked_entity_ids_set
    elif resolved_selected_entity_id is not None:
        # Fallback para bootstrap gap ou utilizadores sem vínculo ativo
        allowed_data_entity_ids = {resolved_selected_entity_id}
    else:
        allowed_data_entity_ids = set()

    return {
        "is_admin": bool(is_admin),
        "has_owner_membership": bool(has_owner_membership),
        "can_manage_tenant_structure": bool(can_manage_tenant_structure),
        "can_create_legacy_entities": bool(can_create_legacy_entities),
        "can_create_legacy_admin_users": bool(can_create_legacy_admin_users),
        "selected_entity_id": resolved_selected_entity_id,
        "allowed_data_entity_ids": allowed_data_entity_ids,
        "allowed_structure_entity_ids": allowed_structure_entity_ids,
        # Aliases deprecated — mantidos para compatibilidade enquanto migração não é completa
        "can_manage_all_entities": bool(can_manage_tenant_structure),
        "allowed_entity_ids": allowed_structure_entity_ids,
    }

def is_entity_within_permissions(entity_id: int, permissions: dict[str, Any]) -> bool:
    if permissions.get("can_manage_tenant_structure") or permissions.get("can_manage_all_entities"):
        return True
    allowed_ids = permissions.get("allowed_structure_entity_ids") or permissions.get("allowed_entity_ids") or set()
    return int(entity_id) in allowed_ids

__all__ = [
    "owner_entity_exists",
    "user_has_owner_entity_membership",
    "_get_user_linked_entity_ids",
    "get_user_entity_permissions",
    "is_entity_within_permissions",
]
