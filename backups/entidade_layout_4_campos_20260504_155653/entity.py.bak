from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin


class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_number: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    acronym: Mapped[Optional[str]] = mapped_column(String(30))
    tax_id: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    responsible_name: Mapped[Optional[str]] = mapped_column(String(200))
    door_number: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    freguesia: Mapped[Optional[str]] = mapped_column(String(120))
    postal_code: Mapped[Optional[str]] = mapped_column(String(30))
    country: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    profile_scope: Mapped[str] = mapped_column(String(20), nullable=False, default="legado")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    member_links: Mapped[List["MemberEntity"]] = relationship(back_populates="entity")
    departments: Mapped[List["Department"]] = relationship(back_populates="entity")
    roles: Mapped[List["Role"]] = relationship(back_populates="entity")

    __table_args__ = (
        CheckConstraint(
            "profile_scope IN ('owner', 'legado')",
            name="ck_entities_profile_scope",
        ),
    )

