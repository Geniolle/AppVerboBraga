from __future__ import annotations

from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from appverbo.models.base import Base, TimestampMixin


class ProcessViewAuthorizationRule(Base, TimestampMixin):
    __tablename__ = "process_view_authorization_rules"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_process_view_authorization_rules_status",
        ),
        CheckConstraint(
            "visibility_scope_mode IN ('all', 'entity')",
            name="ck_process_view_authorization_rules_visibility_scope_mode",
        ),
        Index(
            "ix_process_view_authorization_rules_entity_status",
            "entity_id",
            "status",
        ),
        Index(
            "ix_process_view_authorization_rules_profile_status",
            "profile_name",
            "status",
        ),
        Index(
            "ix_process_view_authorization_rules_process_targets",
            "process_key",
            "subprocess_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("entities.id"))

    profile_name: Mapped[str] = mapped_column(String(100), nullable=False)
    process_key: Mapped[Optional[str]] = mapped_column(String(120))
    process_label: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="",
        server_default=text("''"),
    )
    subprocess_key: Mapped[Optional[str]] = mapped_column(String(120))
    subprocess_label: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="",
        server_default=text("''"),
    )
    department_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="",
        server_default=text("''"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )

    visibility_scope_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="entity",
        server_default=text("'entity'"),
    )

    legacy_record_id: Mapped[Optional[str]] = mapped_column(String(40))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
