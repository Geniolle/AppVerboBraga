"""add system_type to users and drop profiles tables

Revision ID: systemtype01
Revises: entitynum01
Create Date: 2026-06-20 00:00:00.000000

Decisao de arquitetura:
- system_type fica em users.system_type (nao em member_entities) porque o perfil
  global era sempre por utilizador (user_profiles.user_id), nao por vinculo de entidade.
- Mapeamento de dados antigos:
    - profiles com nome admin / administrador / super user -> owner
    - profiles com nome user ou sem perfil               -> default
- Tabelas profiles e user_profiles sao removidas completamente apos a migracao.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text


revision: str = "systemtype01"
down_revision: Union[str, Sequence[str], None] = "entitynum01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def upgrade() -> None:
    # 1. Adicionar coluna system_type a users (default = 'default')
    op.add_column(
        "users",
        sa.Column("system_type", sa.String(20), nullable=False, server_default="default"),
    )

    # 2. Migrar dados: utilizadores com perfil admin/super user -> owner
    if _table_exists("user_profiles") and _table_exists("profiles"):
        bind = op.get_bind()
        bind.execute(
            text("""
                UPDATE users
                SET system_type = 'owner'
                WHERE id IN (
                    SELECT up.user_id
                    FROM user_profiles up
                    JOIN profiles p ON p.id = up.profile_id
                    WHERE up.is_active = TRUE
                      AND lower(trim(p.name)) IN ('admin', 'administrador', 'super user')
                )
            """)
        )

    # 3. Remover tabela user_profiles (FK para users e profiles)
    if _table_exists("user_profiles"):
        op.drop_table("user_profiles")

    # 4. Remover tabela profiles
    if _table_exists("profiles"):
        op.drop_table("profiles")


def downgrade() -> None:
    # Re-criar profiles
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # Re-criar user_profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # Remover system_type
    op.drop_column("users", "system_type")
