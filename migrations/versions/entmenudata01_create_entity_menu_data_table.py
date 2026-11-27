"""create entity_menu_data table (dados por entidade dentro de um menu)

Revision ID: entmenudata01
Revises: procrec01
Create Date: 2026-11-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "entmenudata01"
down_revision = "procrec01"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # Producao ja tem a tabela (criada manualmente em 2026-11-27); IF NOT EXISTS / checagem evitam conflito.
    if _has_table("entity_menu_data"):
        return
    op.execute(
        """
        CREATE TABLE entity_menu_data (
            entity_id INTEGER NOT NULL,
            menu_key VARCHAR(80) NOT NULL,
            data_key VARCHAR(80) NOT NULL,
            data TEXT,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (entity_id, menu_key, data_key)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS entity_menu_data")
