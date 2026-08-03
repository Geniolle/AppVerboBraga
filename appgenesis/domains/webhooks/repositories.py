from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models import Member


def find_member_by_whatsapp_message_id(session: Session, message_id: str) -> Member | None:
    return session.execute(
        select(Member).where(Member.whatsapp_last_message_id == message_id)
    ).scalar_one_or_none()
