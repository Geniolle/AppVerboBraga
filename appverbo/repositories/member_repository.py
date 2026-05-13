
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.models import Member


def get_member_by_id(session: Session, member_id: int) -> Member | None:
    return session.get(Member, int(member_id))


def get_member_by_email_ci(session: Session, email: str) -> Member | None:
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return None

    return session.execute(
        select(Member).where(func.lower(Member.email) == clean_email)
    ).scalar_one_or_none()


def get_duplicate_member_id_by_email_ci(
    session: Session,
    email: str,
    excluded_member_id: int | None = None,
) -> int | None:
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return None

    stmt = select(Member.id).where(func.lower(Member.email) == clean_email)

    if excluded_member_id is not None:
        stmt = stmt.where(Member.id != int(excluded_member_id))

    duplicate_id = session.scalar(stmt.limit(1))
    return int(duplicate_id) if duplicate_id is not None else None
