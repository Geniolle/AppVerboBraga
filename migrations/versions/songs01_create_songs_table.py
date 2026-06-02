from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "songs01"
down_revision = "admindefs01"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {
        index["name"]
        for index in inspector.get_indexes(table_name)
    }


def upgrade() -> None:
    if not _has_table("songs"):
        op.create_table(
            "songs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("version", sa.String(length=255), nullable=False),
            sa.Column("youtube_url", sa.Text(), nullable=False),
            sa.Column("lyrics", sa.Text(), nullable=True),
            sa.Column(
                "lyrics_source",
                sa.String(length=40),
                nullable=False,
                server_default=sa.text("'manual'"),
            ),
            sa.Column(
                "lyrics_status",
                sa.String(length=40),
                nullable=False,
                server_default=sa.text("'rascunho'"),
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "lyrics_source IN ('manual', 'youtube_transcript', 'audio_transcription', 'imported')",
                name="ck_songs_lyrics_source",
            ),
            sa.CheckConstraint(
                "lyrics_status IN ('rascunho', 'revista', 'aprovada')",
                name="ck_songs_lyrics_status",
            ),
            sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index("songs", "ix_songs_entity_active"):
        op.create_index(
            "ix_songs_entity_active",
            "songs",
            ["entity_id", "is_active"],
            unique=False,
        )

    if not _has_index("songs", "ix_songs_entity_name"):
        op.create_index(
            "ix_songs_entity_name",
            "songs",
            ["entity_id", "name"],
            unique=False,
        )


def downgrade() -> None:
    if _has_table("songs"):
        if _has_index("songs", "ix_songs_entity_name"):
            op.drop_index("ix_songs_entity_name", table_name="songs")

        if _has_index("songs", "ix_songs_entity_active"):
            op.drop_index("ix_songs_entity_active", table_name="songs")

        op.drop_table("songs")
