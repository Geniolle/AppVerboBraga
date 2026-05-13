from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus


def get_active_member_entity_links(session: Session, member_id: int) -> list[MemberEntity]:
    return list(
        session.execute(
            select(MemberEntity).where(
                MemberEntity.member_id == int(member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        ).scalars().all()
    )


def get_primary_entity_name(session: Session, member_id: int) -> str:
    row = session.execute(
        select(Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return str(row or "")

