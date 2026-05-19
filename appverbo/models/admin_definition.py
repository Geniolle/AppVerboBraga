from __future__ import annotations

from sqlalchemy import Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from appverbo.models.base import Base, TimestampMixin


class AdminDefinition(Base, TimestampMixin):
    __tablename__ = "admin_definitions"
    __table_args__ = (
        Index("ix_admin_definitions_status", "status"),
        Index("ix_admin_definitions_process_subprocess", "process_name", "subprocess_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parameter_name: Mapped[str] = mapped_column(String(160), nullable=False)
    parameter_type: Mapped[str] = mapped_column(String(30), nullable=False)
    initial_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )
    process_name: Mapped[str] = mapped_column(String(120), nullable=False)
    subprocess_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
