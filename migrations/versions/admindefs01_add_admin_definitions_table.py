from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "admindefs01"
down_revision = "meuperfilkey01"
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
    if not _has_table("admin_definitions"):
        op.create_table(
            "admin_definitions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("parameter_name", sa.String(length=160), nullable=False),
            sa.Column("parameter_type", sa.String(length=30), nullable=False),
            sa.Column("initial_value", sa.Text(), nullable=False, server_default=sa.text("''")),
            sa.Column("process_name", sa.String(length=120), nullable=False),
            sa.Column("subprocess_name", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_index("admin_definitions", "ix_admin_definitions_status"):
        op.create_index(
            "ix_admin_definitions_status",
            "admin_definitions",
            ["status"],
            unique=False,
        )

    if not _has_index("admin_definitions", "ix_admin_definitions_process_subprocess"):
        op.create_index(
            "ix_admin_definitions_process_subprocess",
            "admin_definitions",
            ["process_name", "subprocess_name"],
            unique=False,
        )


def downgrade() -> None:
    if _has_table("admin_definitions"):
        if _has_index("admin_definitions", "ix_admin_definitions_process_subprocess"):
            op.drop_index("ix_admin_definitions_process_subprocess", table_name="admin_definitions")

        if _has_index("admin_definitions", "ix_admin_definitions_status"):
            op.drop_index("ix_admin_definitions_status", table_name="admin_definitions")

        op.drop_table("admin_definitions")
