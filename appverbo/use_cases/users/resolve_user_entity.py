from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus


def execute_resolve_user_entity_v1(
    *,
    session: Session,
    member_id: int,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    stmt = (
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.desc())
    )

    if allowed_entity_ids is not None:
        if allowed_entity_ids:
            stmt = stmt.where(Entity.id.in_(sorted(allowed_entity_ids)))
        else:
            return {"entity_id": None, "entity_name": ""}

    row = session.execute(stmt.limit(1)).one_or_none()
    if row is None:
        return {"entity_id": None, "entity_name": ""}

    return {"entity_id": int(row.id), "entity_name": str(row.name or "")}


__all__ = ["execute_resolve_user_entity_v1"]

