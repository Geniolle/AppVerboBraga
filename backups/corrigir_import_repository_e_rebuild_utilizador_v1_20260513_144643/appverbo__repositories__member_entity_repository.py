
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus


def get_primary_member_entity_link(session: Session, member_id: int) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def get_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
) -> MemberEntity | None:
    return session.execute(
        select(MemberEntity)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.entity_id == int(entity_id),
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def upsert_active_member_entity_link(
    session: Session,
    member_id: int,
    entity_id: int,
    *,
    replace_primary: bool = False,
) -> MemberEntity:
    if replace_primary:
        link = get_primary_member_entity_link(session, member_id)
    else:
        link = get_member_entity_link(session, member_id, entity_id)

    if link is None:
        link = MemberEntity(
            member_id=int(member_id),
            entity_id=int(entity_id),
            status=MemberEntityStatus.ACTIVE.value,
            entry_date=date.today(),
        )
        session.add(link)
        return link

    link.entity_id = int(entity_id)
    link.status = MemberEntityStatus.ACTIVE.value

    if link.entry_date is None:
        link.entry_date = date.today()

    return link


def get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()

    if row is None:
        return None, "-"

    return int(row.id), str(row.name or "-")


def get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
    ).all()

    result: list[int] = []
    seen: set[int] = set()

    for raw_id in rows:
        if raw_id is None:
            continue

        entity_id = int(raw_id)

        if entity_id in seen:
            continue

        seen.add(entity_id)
        result.append(entity_id)

    return result


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
    _, entity_name = get_primary_entity_for_member(session, int(member_id))
    return "" if entity_name == "-" else entity_name
