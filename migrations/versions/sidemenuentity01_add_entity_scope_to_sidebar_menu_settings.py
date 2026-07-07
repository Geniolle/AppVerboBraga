from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "sidemenuentity01"
down_revision = "userlang01"
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


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return constraint_name in {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
    }


# ###################################################################################
# (2) UPGRADE
# ###################################################################################


def upgrade() -> None:
    if not _has_table("sidebar_menu_settings") or not _has_table("entities"):
        return

    bind = op.get_bind()

    if not _has_column("sidebar_menu_settings", "entity_id"):
        op.add_column(
            "sidebar_menu_settings",
            sa.Column(
                "entity_id",
                sa.Integer(),
                sa.ForeignKey("entities.id"),
                nullable=True,
            ),
        )

    if _has_unique_constraint(
        "sidebar_menu_settings", "uq_sidebar_menu_settings_menu_key"
    ):
        op.drop_constraint(
            "uq_sidebar_menu_settings_menu_key",
            "sidebar_menu_settings",
            type_="unique",
        )

    active_entity_ids = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT id FROM entities WHERE is_active = true ORDER BY id")
        ).all()
    ]

    for entity_id in active_entity_ids:
        bind.execute(
            sa.text(
                """
                INSERT INTO sidebar_menu_settings
                    (entity_id, menu_key, menu_label, is_active, is_deleted, menu_config)
                SELECT :entity_id, menu_key, menu_label, is_active, is_deleted, menu_config
                FROM sidebar_menu_settings
                WHERE entity_id IS NULL
                """
            ),
            {"entity_id": entity_id},
        )

    bind.execute(sa.text("DELETE FROM sidebar_menu_settings WHERE entity_id IS NULL"))

    op.alter_column("sidebar_menu_settings", "entity_id", nullable=False)

    if not _has_unique_constraint(
        "sidebar_menu_settings", "uq_sidebar_menu_settings_entity_menu_key"
    ):
        op.create_unique_constraint(
            "uq_sidebar_menu_settings_entity_menu_key",
            "sidebar_menu_settings",
            ["entity_id", "menu_key"],
        )


# ###################################################################################
# (3) DOWNGRADE
# ###################################################################################


def downgrade() -> None:
    if not _has_table("sidebar_menu_settings"):
        return

    if _has_unique_constraint(
        "sidebar_menu_settings", "uq_sidebar_menu_settings_entity_menu_key"
    ):
        op.drop_constraint(
            "uq_sidebar_menu_settings_entity_menu_key",
            "sidebar_menu_settings",
            type_="unique",
        )

    if _has_column("sidebar_menu_settings", "entity_id"):
        op.drop_column("sidebar_menu_settings", "entity_id")

    if not _has_unique_constraint(
        "sidebar_menu_settings", "uq_sidebar_menu_settings_menu_key"
    ):
        op.create_unique_constraint(
            "uq_sidebar_menu_settings_menu_key",
            "sidebar_menu_settings",
            ["menu_key"],
        )
