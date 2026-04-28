from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "membercountry01"
down_revision = "sidemenucompat01"
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
    if not _has_column("members", "country"):
        op.add_column(
            "members",
            sa.Column("country", sa.String(length=120), nullable=True),
        )


def downgrade() -> None:
    if _has_column("members", "country"):
        op.drop_column("members", "country")
