from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from appverbo.models.base import Base


class SidebarMenuSetting(Base):
    __tablename__ = "sidebar_menu_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    menu_key: Mapped[str] = mapped_column(String(80), nullable=False)
    menu_label: Mapped[str] = mapped_column(String(120), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    menu_config: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("menu_key", name="uq_sidebar_menu_settings_menu_key"),
    )
