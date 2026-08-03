from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "authview02"
down_revision = "authview01"
branch_labels = None
depends_on = None


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if _has_index("entities", "uq_entities_internal_number"):
        op.drop_index("uq_entities_internal_number", table_name="entities")

    if _has_index("entities", "uq_entities_single_owner_scope"):
        op.drop_index("uq_entities_single_owner_scope", table_name="entities")


def downgrade() -> None:
    if not _has_index("entities", "uq_entities_single_owner_scope"):
        op.create_index(
            "uq_entities_single_owner_scope",
            "entities",
            ["profile_scope"],
            unique=True,
            postgresql_where=sa.text("((profile_scope)::text = 'owner'::text)"),
        )

    if not _has_index("entities", "uq_entities_internal_number"):
        op.create_index(
            "uq_entities_internal_number",
            "entities",
            ["internal_number"],
            unique=True,
            postgresql_where=sa.text("(internal_number IS NOT NULL)"),
        )
