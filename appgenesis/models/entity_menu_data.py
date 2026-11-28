from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from appgenesis.models.base import Base


class EntityMenuData(Base):
    """Dados de cada entidade dentro de um menu compartilhado (migration entmenudata01).

    Existe para o metadata refletir a tabela: sem ele, `alembic --autogenerate` propoe DROP TABLE.
    O acesso continua em `appgenesis/services/entity_menu_data.py`.
    """

    __tablename__ = "entity_menu_data"

    entity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    menu_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    data_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    data: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
