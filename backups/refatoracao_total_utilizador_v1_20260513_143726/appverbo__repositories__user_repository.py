from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.models import User


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, int(user_id))


def get_user_by_email_ci(session: Session, login_email: str) -> User | None:
    clean_email = (login_email or "").strip().lower()
    if not clean_email:
        return None
    return session.execute(
        select(User).where(func.lower(User.login_email) == clean_email)
    ).scalar_one_or_none()

