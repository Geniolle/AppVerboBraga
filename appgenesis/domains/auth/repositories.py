from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models import Entity, MemberEntity, MemberEntityStatus


def resolve_invite_entity_for_member(
    session: Session,
    member_id: int,
    requested_entity_id: int | None,
) -> tuple[int | None, str]:
    entity_rows = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
        .order_by(MemberEntity.id.asc())
    ).all()
    if not entity_rows:
        return None, "-"

    if isinstance(requested_entity_id, int) and requested_entity_id > 0:
        for row in entity_rows:
            if int(row.id) == requested_entity_id:
                return int(row.id), str(row.name or "-")

    first_row = entity_rows[0]
    return int(first_row.id), str(first_row.name or "-")
