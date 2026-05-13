
from __future__ import annotations

from sqlalchemy import func, select, update
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


def get_duplicate_user_id_by_email_ci(
    session: Session,
    login_email: str,
    excluded_user_id: int | None = None,
) -> int | None:
    clean_email = (login_email or "").strip().lower()
    if not clean_email:
        return None

    stmt = select(User.id).where(func.lower(User.login_email) == clean_email)

    if excluded_user_id is not None:
        stmt = stmt.where(User.id != int(excluded_user_id))

    duplicate_id = session.scalar(stmt.limit(1))
    return int(duplicate_id) if duplicate_id is not None else None


def null_created_by_for_deleted_user(session: Session, user_id: int) -> None:
    session.execute(
        update(User)
        .where(User.created_by_user_id == int(user_id))
        .values(created_by_user_id=None)
    )
