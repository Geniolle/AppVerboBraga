from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "profilescope01"
down_revision = "authview03"
branch_labels = None
depends_on = None


# ###################################################################################
# (1) HELPERS DE INSPECAO
# ###################################################################################


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


# ###################################################################################
# (2) UPGRADE
# ###################################################################################


def upgrade() -> None:
    if not _has_table("profiles"):
        return

    if not _has_column("profiles", "entity_id"):
        op.add_column(
            "profiles",
            sa.Column(
                "entity_id",
                sa.Integer(),
                sa.ForeignKey("entities.id"),
                nullable=True,
            ),
        )

    if not _has_column("profiles", "visibility_scope_mode"):
        op.add_column(
            "profiles",
            sa.Column(
                "visibility_scope_mode",
                sa.String(20),
                nullable=False,
                server_default="entity",
            ),
        )


# ###################################################################################
# (3) DOWNGRADE
# ###################################################################################


def downgrade() -> None:
    if not _has_table("profiles"):
        return

    if _has_column("profiles", "visibility_scope_mode"):
        op.drop_column("profiles", "visibility_scope_mode")

    if _has_column("profiles", "entity_id"):
        op.drop_column("profiles", "entity_id")
