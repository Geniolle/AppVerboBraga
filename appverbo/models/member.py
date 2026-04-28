from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin
from appverbo.models.enums import MemberEntityStatus, MemberStatus


class Member(Base, TimestampMixin):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)

    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(120))
    secondary_phone: Mapped[Optional[str]] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)

    address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    freguesia: Mapped[Optional[str]] = mapped_column(String(120))
    postal_code: Mapped[Optional[str]] = mapped_column(String(30))
    whatsapp_verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    whatsapp_notice_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whatsapp_last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    whatsapp_last_error: Mapped[Optional[str]] = mapped_column(Text)
    whatsapp_last_wa_id: Mapped[Optional[str]] = mapped_column(String(64))
    whatsapp_last_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    training_discipulado_verbo_vida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_ebvv: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_rhema: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_escola_ministerial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_escola_missoes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    training_outros: Mapped[Optional[str]] = mapped_column(String(255))
    profile_custom_fields: Mapped[Optional[str]] = mapped_column(Text)
    marital_status: Mapped[Optional[str]] = mapped_column(String(50))

    baptism_date: Mapped[Optional[date]] = mapped_column(Date)
    photo_url: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    spouse_name: Mapped[Optional[str]] = mapped_column(String(200))
    children: Mapped[Optional[str]] = mapped_column(Text)
    household: Mapped[Optional[str]] = mapped_column(Text)

    profession: Mapped[Optional[str]] = mapped_column(String(120))
    identification_document: Mapped[Optional[str]] = mapped_column(String(100))
    tax_number: Mapped[Optional[str]] = mapped_column(String(50))

    member_status: Mapped[str] = mapped_column(String(20), nullable=False, default=MemberStatus.ACTIVE.value)
    is_collaborator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_collaboration_date: Mapped[Optional[date]] = mapped_column(Date)

    entity_links: Mapped[List["MemberEntity"]] = relationship(back_populates="member")
    user_account: Mapped[Optional["User"]] = relationship(back_populates="member", uselist=False)

    __table_args__ = (
        CheckConstraint(
            "member_status IN ('active', 'inactive')",
            name="ck_members_member_status",
        ),
    )


class MemberEntity(Base, TimestampMixin):
    __tablename__ = "member_entities"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)

    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_date: Mapped[Optional[date]] = mapped_column(Date)
    exit_or_transfer_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MemberEntityStatus.ACTIVE.value
    )

    member: Mapped["Member"] = relationship(back_populates="entity_links")
    entity: Mapped["Entity"] = relationship(back_populates="member_links")
    department_memberships: Mapped[List["DepartmentMembership"]] = relationship(
        back_populates="member_entity"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'transferred')",
            name="ck_member_entities_status",
        ),
    )

