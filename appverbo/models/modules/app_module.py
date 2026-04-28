from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin


class AppModule(Base, TimestampMixin):
    __tablename__ = "app_modules"

    id: Mapped[int] = mapped_column(primary_key=True)

    module_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    module_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    menu_group: Mapped[str] = mapped_column(String(80), nullable=False, default="igreja")
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    entitlements: Mapped[list["EntityModuleEntitlement"]] = relationship(
        "EntityModuleEntitlement",
        back_populates="module",
        cascade="all, delete-orphan",
    )

    sidebar_items: Mapped[list["SidebarMenuItem"]] = relationship(
        "SidebarMenuItem",
        back_populates="module",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("module_key", name="uq_app_modules_module_key"),
        CheckConstraint("length(trim(module_key)) > 0", name="ck_app_modules_module_key_not_empty"),
        CheckConstraint("length(trim(module_name)) > 0", name="ck_app_modules_module_name_not_empty"),
    )
