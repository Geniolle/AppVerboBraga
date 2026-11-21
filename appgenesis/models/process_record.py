from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from appgenesis.models.base import Base


class ProcessRecord(Base):
    """Registo de um processo de lista (ex.: Agenda), partilhado por entidade.

    Multi-tenant: cada linha pertence a uma entidade; todas as consultas filtram por entity_id.
    values_json guarda o mapa {campo: valor} com as mesmas chaves dos campos do processo.
    """

    __tablename__ = "process_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    menu_key: Mapped[str] = mapped_column(String(80), nullable=False)
    record_id: Mapped[str] = mapped_column(String(32), nullable=False)
    section_key: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default=text("''"))
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="ativo", server_default=text("'ativo'"))
    values_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default=text("'{}'"))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("entity_id", "menu_key", "record_id", name="uq_process_records_entity_menu_record"),
        Index("ix_process_records_entity_menu", "entity_id", "menu_key"),
    )
