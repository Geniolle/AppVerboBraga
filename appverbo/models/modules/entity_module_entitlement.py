from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin


class EntityModuleEntitlement(Base, TimestampMixin):
    __tablename__ = "entity_module_entitlements"

    id: Mapped[int] = mapped_column(primary_key=True)

    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    module_key: Mapped[str] = mapped_column(ForeignKey("app_modules.module_key"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="inactive")
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    enabled_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    entity: Mapped["Entity"] = relationship("Entity")
    module: Mapped["AppModule"] = relationship("AppModule", back_populates="entitlements")
    enabled_by_user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        UniqueConstraint("entity_id", "module_key", name="uq_entity_module_entitlements_entity_module"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'expired')",
            name="ck_entity_module_entitlements_status",
        ),
    )
