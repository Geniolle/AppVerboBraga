from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.models import Entity


def get_entity_by_id(session: Session, entity_id: int) -> Entity | None:
    return session.get(Entity, int(entity_id))


def get_entity_by_name_ci(session: Session, entity_name: str) -> Entity | None:
    clean_name = (entity_name or "").strip().lower()
    if not clean_name:
        return None
    return session.execute(
        select(Entity).where(func.lower(Entity.name) == clean_name)
    ).scalar_one_or_none()


def get_active_entities(session: Session) -> list[Entity]:
    return list(
        session.execute(
            select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
        ).scalars().all()
    )

