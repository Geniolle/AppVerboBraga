from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin
from appverbo.models.enums import UserAccountStatus


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, unique=True)
    login_email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserAccountStatus.PENDING.value
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    member: Mapped["Member"] = relationship(back_populates="user_account")
    profiles: Mapped[List["UserProfile"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('pending', 'active', 'inactive', 'blocked')",
            name="ck_users_account_status",
        ),
    )

