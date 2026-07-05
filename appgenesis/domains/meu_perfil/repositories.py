from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models import Member, User


def find_member_for_user(session: Session, user_id: int) -> Member | None:
    return session.execute(
        select(Member).join(User, User.member_id == Member.id).where(User.id == user_id)
    ).scalar_one_or_none()
