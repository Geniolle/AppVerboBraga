from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "sidemenucompat01"
down_revision = "fc2cca3e78f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sidebar_menu_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("menu_key", sa.String(length=80), nullable=False),
        sa.Column("menu_label", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("menu_config", sa.Text(), nullable=True),
        sa.UniqueConstraint("menu_key", name="uq_sidebar_menu_settings_menu_key"),
    )


def downgrade() -> None:
    op.drop_table("sidebar_menu_settings")
