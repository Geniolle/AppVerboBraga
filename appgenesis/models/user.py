from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appgenesis.models.base import Base, TimestampMixin
from appgenesis.models.enums import UserAccountStatus


def _resolve_user_profile_model_v1():
    from appgenesis.models.profile import UserProfile

    return UserProfile


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, unique=True)
    login_email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserAccountStatus.PENDING.value
    )
    system_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="default", server_default="default"
    )
    preferred_language: Mapped[str] = mapped_column(
        String(5), nullable=False, default="pt", server_default="pt"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    member: Mapped["Member"] = relationship(back_populates="user_account")
    profiles: Mapped[List["UserProfile"]] = relationship(
        _resolve_user_profile_model_v1,
        back_populates="user",
    )

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('pending', 'active', 'inactive', 'blocked')",
            name="ck_users_account_status",
        ),
        CheckConstraint(
            "preferred_language IN ('pt', 'en', 'es', 'fr')",
            name="ck_users_preferred_language",
        ),
    )
