from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from appverbo.models import Profile, UserProfile


def get_active_profile_ids_by_user(session: Session, user_id: int) -> list[int]:
    return [
        int(raw_id)
        for raw_id in session.execute(
            select(UserProfile.profile_id).where(
                UserProfile.user_id == int(user_id),
                UserProfile.is_active.is_(True),
            )
        )
        .scalars()
        .all()
        if raw_id is not None
    ]


def get_active_profile_names_by_user(session: Session, user_id: int) -> list[str]:
    rows = session.execute(
        select(Profile.name)
        .join(UserProfile, UserProfile.profile_id == Profile.id)
        .where(
            UserProfile.user_id == int(user_id),
            UserProfile.is_active.is_(True),
        )
        .order_by(Profile.name.asc())
    ).scalars().all()

    return [str(name or "").strip() for name in rows if str(name or "").strip()]


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
