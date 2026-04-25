from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.models import Profile


def get_profile_by_id(session: Session, profile_id: int) -> Profile | None:
    return session.get(Profile, int(profile_id))

