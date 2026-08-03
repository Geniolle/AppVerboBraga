from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "admindefscope01"
down_revision = "authview02"
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


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {
        index["name"]
        for index in inspector.get_indexes(table_name)
    }


def _has_foreign_key(table_name: str, foreign_key_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return foreign_key_name in {
        foreign_key.get("name")
        for foreign_key in inspector.get_foreign_keys(table_name)
    }


# ###################################################################################
# (2) UPGRADE
# ###################################################################################


def upgrade() -> None:
    if not _has_table("admin_definitions"):
        return

    if not _has_column("admin_definitions", "entity_id"):
        op.add_column(
            "admin_definitions",
            sa.Column("entity_id", sa.Integer(), nullable=True),
        )

    if not _has_foreign_key("admin_definitions", "fk_admin_definitions_entity_id_entities"):
        op.create_foreign_key(
            "fk_admin_definitions_entity_id_entities",
            "admin_definitions",
            "entities",
            ["entity_id"],
            ["id"],
        )

    if not _has_index("admin_definitions", "ix_admin_definitions_entity_id"):
        op.create_index(
            "ix_admin_definitions_entity_id",
            "admin_definitions",
            ["entity_id"],
            unique=False,
        )

    if not _has_index("admin_definitions", "ix_admin_definitions_entity_process_subprocess"):
        op.create_index(
            "ix_admin_definitions_entity_process_subprocess",
            "admin_definitions",
            ["entity_id", "process_name", "subprocess_name"],
            unique=False,
        )


# ###################################################################################
# (3) DOWNGRADE
# ###################################################################################


def downgrade() -> None:
    if not _has_table("admin_definitions"):
        return

    if _has_index("admin_definitions", "ix_admin_definitions_entity_process_subprocess"):
        op.drop_index(
            "ix_admin_definitions_entity_process_subprocess",
            table_name="admin_definitions",
        )

    if _has_index("admin_definitions", "ix_admin_definitions_entity_id"):
        op.drop_index(
            "ix_admin_definitions_entity_id",
            table_name="admin_definitions",
        )

    if _has_foreign_key("admin_definitions", "fk_admin_definitions_entity_id_entities"):
        op.drop_constraint(
            "fk_admin_definitions_entity_id_entities",
            "admin_definitions",
            type_="foreignkey",
        )

    if _has_column("admin_definitions", "entity_id"):
        op.drop_column("admin_definitions", "entity_id")
