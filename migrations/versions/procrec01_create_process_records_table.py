"""create process_records table (shared process list records per entity)

Revision ID: procrec01
Revises: entitycity01
Create Date: 2026-11-21
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "procrec01"
down_revision = "entitycity01"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("process_records"):
        return
    op.create_table(
        "process_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("menu_key", sa.String(length=80), nullable=False),
        sa.Column("record_id", sa.String(length=32), nullable=False),
        sa.Column("section_key", sa.String(length=80), nullable=False, server_default=sa.text("''")),
        sa.Column("state", sa.String(length=20), nullable=False, server_default=sa.text("'ativo'")),
        sa.Column("values_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entity_id", "menu_key", "record_id", name="uq_process_records_entity_menu_record"),
    )
    op.create_index("ix_process_records_entity_menu", "process_records", ["entity_id", "menu_key"])


def downgrade() -> None:
    if _has_table("process_records"):
        op.drop_index("ix_process_records_entity_menu", table_name="process_records")
        op.drop_table("process_records")
