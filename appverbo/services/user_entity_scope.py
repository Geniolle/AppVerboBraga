from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, User
from appverbo.models.enums import MemberEntityStatus
from appverbo.services.user_system import normalize_user_system_type_v1


# ###################################################################################
# (1) HELPERS DE ENTIDADES ATIVAS POR ESCOPO
# ###################################################################################
def _normalize_allowed_entity_ids_v1(
    allowed_entity_ids: set[int] | list[int] | tuple[int, ...] | None,
) -> list[int]:
    if allowed_entity_ids is None:
        return []
    ordered_ids = sorted(
        {
            int(raw_id)
            for raw_id in allowed_entity_ids
            if str(raw_id).strip().isdigit()
        }
    )
    return ordered_ids


def _get_active_entities_for_scope_v1(
    session: Session,
    *,
    allowed_entity_ids: set[int] | list[int] | tuple[int, ...] | None = None,
    require_entity_number: bool = False,
) -> list[dict[str, Any]]:
    query = select(Entity.id, Entity.name, Entity.entity_number).where(Entity.is_active.is_(True))
    if require_entity_number:
        query = query.where(Entity.entity_number.is_not(None))

    if allowed_entity_ids is not None:
        scoped_entity_ids = _normalize_allowed_entity_ids_v1(allowed_entity_ids)
        if not scoped_entity_ids:
            return []
        query = query.where(Entity.id.in_(scoped_entity_ids))

    rows = session.execute(
        query.order_by(
            Entity.entity_number.is_(None),
            Entity.entity_number.asc(),
            Entity.id.asc(),
        )
    ).all()
    return [
        {
            "id": int(row.id),
            "name": str(row.name or ""),
            "entity_number": row.entity_number,
        }
        for row in rows
    ]


# ###################################################################################
# (2) CAPACIDADES DO ATOR E ENTIDADE PRINCIPAL
# ###################################################################################
def can_select_user_entity_v1(system_type: str | None) -> bool:
    """Owner pode escolher qualquer entidade; legado/default ficam na entidade própria."""
    return normalize_user_system_type_v1(system_type) == "owner"


def get_actor_system_type_v1(session: Session, actor_user_id: int) -> str:
    """Devolve o system_type do utilizador logado (normalizado)."""
    raw = session.scalar(
        select(User.system_type).where(User.id == actor_user_id).limit(1)
    )
    return normalize_user_system_type_v1(raw)


def get_actor_primary_entity_v1(session: Session, actor_user_id: int) -> dict[str, Any] | None:
    """Devolve a primeira entidade ativa associada ao utilizador logado."""
    row = session.execute(
        select(Entity.id, Entity.name, Entity.entity_number)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .join(User, User.member_id == MemberEntity.member_id)
        .where(
            User.id == actor_user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()
    if row is None:
        return None
    return {
        "id": int(row.id),
        "name": str(row.name or ""),
        "entity_number": row.entity_number,
    }


# ###################################################################################
# (3) LISTAS DE ENTIDADES PARA FORMULARIOS DE UTILIZADOR
# ###################################################################################
def get_entities_for_user_form_v1(session: Session, actor_system_type: str) -> list[dict[str, Any]]:
    """
    Owner: devolve todas as entidades ativas para o dropdown do formulário.
    Outros: devolve lista vazia (frontend usa readonly com entidade do ator).
    """
    if normalize_user_system_type_v1(actor_system_type) != "owner":
        return []
    return _get_active_entities_for_scope_v1(session)


def get_entities_for_user_edit_form_v1(
    session: Session,
    permissions: dict[str, Any],
) -> list[dict[str, Any]]:
    if permissions.get("can_manage_tenant_structure", permissions.get("can_manage_all_entities", False)):
        return _get_active_entities_for_scope_v1(
            session,
            require_entity_number=True,
        )
    return _get_active_entities_for_scope_v1(
        session,
        allowed_entity_ids=permissions.get("allowed_entity_ids") or set(),
        require_entity_number=True,
    )


__all__ = [
    "can_select_user_entity_v1",
    "get_actor_system_type_v1",
    "get_actor_primary_entity_v1",
    "get_entities_for_user_form_v1",
    "get_entities_for_user_edit_form_v1",
]
