from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "entitycity01"
down_revision = "sidemenuentity01"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    if not _has_column("entities", "city"):
        op.add_column(
            "entities",
            sa.Column("city", sa.String(length=120), nullable=True),
        )


def downgrade() -> None:
    if _has_column("entities", "city"):
        op.drop_column("entities", "city")
