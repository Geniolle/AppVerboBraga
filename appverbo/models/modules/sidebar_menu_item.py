from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin


class SidebarMenuItem(Base, TimestampMixin):
    __tablename__ = "sidebar_menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    module_key: Mapped[str] = mapped_column(ForeignKey("app_modules.module_key"), nullable=False)

    group_key: Mapped[str] = mapped_column(String(80), nullable=False)
    item_key: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)

    route_path: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    requires_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    module: Mapped["AppModule"] = relationship("AppModule", back_populates="sidebar_items")

    __table_args__ = (
        UniqueConstraint("module_key", "item_key", name="uq_sidebar_menu_items_module_item"),
        CheckConstraint("length(trim(group_key)) > 0", name="ck_sidebar_menu_items_group_key_not_empty"),
        CheckConstraint("length(trim(item_key)) > 0", name="ck_sidebar_menu_items_item_key_not_empty"),
        CheckConstraint("length(trim(label)) > 0", name="ck_sidebar_menu_items_label_not_empty"),
        CheckConstraint("length(trim(route_path)) > 0", name="ck_sidebar_menu_items_route_path_not_empty"),
    )
