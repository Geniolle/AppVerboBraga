from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Member


def get_member_by_id(session: Session, member_id: int) -> Member | None:
    return session.get(Member, int(member_id))


def get_member_by_email_ci(session: Session, email: str) -> Member | None:
    clean_email = str(email or "").strip().lower()
    if not clean_email:
        return None
    return session.execute(
        select(Member).where(Member.email.ilike(clean_email))
    ).scalar_one_or_none()

