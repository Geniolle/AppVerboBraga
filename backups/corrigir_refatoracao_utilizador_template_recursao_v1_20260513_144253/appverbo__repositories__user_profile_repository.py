
from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from appverbo.models import UserProfile


def replace_user_profile(
    session: Session,
    user_id: int,
    profile_id: int,
    *,
    is_active: bool = True,
) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
    session.add(
        UserProfile(
            user_id=int(user_id),
            profile_id=int(profile_id),
            is_active=bool(is_active),
        )
    )


def delete_user_profiles(session: Session, user_id: int) -> None:
    session.execute(delete(UserProfile).where(UserProfile.user_id == int(user_id)))
