from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appverbo.models.base import Base, TimestampMixin


class Song(Base, TimestampMixin):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_url: Mapped[str] = mapped_column(Text, nullable=False)
    lyrics: Mapped[Optional[str]] = mapped_column(Text)
    lyrics_source: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="manual",
        server_default=text("'manual'"),
    )
    lyrics_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="rascunho",
        server_default=text("'rascunho'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    entity: Mapped["Entity"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "lyrics_source IN ('manual', 'youtube_transcript', 'audio_transcription', 'imported')",
            name="ck_songs_lyrics_source",
        ),
        CheckConstraint(
            "lyrics_status IN ('rascunho', 'revista', 'aprovada')",
            name="ck_songs_lyrics_status",
        ),
        Index("ix_songs_entity_active", "entity_id", "is_active"),
        Index("ix_songs_entity_name", "entity_id", "name"),
    )
