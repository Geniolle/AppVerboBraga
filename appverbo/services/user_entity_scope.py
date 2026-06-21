from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, User
from appverbo.models.enums import MemberEntityStatus
from appverbo.services.user_system import normalize_user_system_type_v1


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


def get_entities_for_user_form_v1(session: Session, actor_system_type: str) -> list[dict[str, Any]]:
    """
    Owner: devolve todas as entidades ativas para o dropdown do formulário.
    Outros: devolve lista vazia (frontend usa readonly com entidade do ator).
    """
    if normalize_user_system_type_v1(actor_system_type) != "owner":
        return []
    rows = session.execute(
        select(Entity.id, Entity.name, Entity.entity_number)
        .where(Entity.is_active.is_(True))
        .order_by(Entity.name.asc())
    ).all()
    return [
        {
            "id": int(row.id),
            "name": str(row.name or ""),
            "entity_number": row.entity_number,
        }
        for row in rows
    ]


__all__ = [
    "can_select_user_entity_v1",
    "get_actor_system_type_v1",
    "get_actor_primary_entity_v1",
    "get_entities_for_user_form_v1",
]
