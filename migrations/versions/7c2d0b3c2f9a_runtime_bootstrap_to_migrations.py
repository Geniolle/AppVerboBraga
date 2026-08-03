"""move runtime bootstrap schema changes to migrations

Revision ID: 7c2d0b3c2f9a
Revises: 460731d67a56
Create Date: 2026-04-24 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = "7c2d0b3c2f9a"
down_revision: Union[str, Sequence[str], None] = "460731d67a56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return column in {item["name"] for item in inspector.get_columns(table)}


def _has_index(inspector: sa.Inspector, table: str, index_name: str) -> bool:
    return index_name in {item["name"] for item in inspector.get_indexes(table)}


def _ensure_entities_table_updates() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if "entities" not in table_names:
        return

    columns_to_add: list[sa.Column] = []
    if not _has_column(inspector, "entities", "internal_number"):
        columns_to_add.append(sa.Column("internal_number", sa.Integer(), nullable=True))
    if not _has_column(inspector, "entities", "tax_id"):
        columns_to_add.append(sa.Column("tax_id", sa.String(length=40), nullable=True))
    if not _has_column(inspector, "entities", "email"):
        columns_to_add.append(sa.Column("email", sa.String(length=150), nullable=True))
    if not _has_column(inspector, "entities", "responsible_name"):
        columns_to_add.append(sa.Column("responsible_name", sa.String(length=200), nullable=True))
    if not _has_column(inspector, "entities", "door_number"):
        columns_to_add.append(sa.Column("door_number", sa.String(length=30), nullable=True))
    if not _has_column(inspector, "entities", "address"):
        columns_to_add.append(sa.Column("address", sa.String(length=255), nullable=True))
    if not _has_column(inspector, "entities", "freguesia"):
        columns_to_add.append(sa.Column("freguesia", sa.String(length=120), nullable=True))
    if not _has_column(inspector, "entities", "postal_code"):
        columns_to_add.append(sa.Column("postal_code", sa.String(length=30), nullable=True))
    if not _has_column(inspector, "entities", "country"):
        columns_to_add.append(sa.Column("country", sa.String(length=120), nullable=True))
    if not _has_column(inspector, "entities", "phone"):
        columns_to_add.append(sa.Column("phone", sa.String(length=30), nullable=True))
    if not _has_column(inspector, "entities", "logo_url"):
        columns_to_add.append(sa.Column("logo_url", sa.Text(), nullable=True))
    if not _has_column(inspector, "entities", "profile_scope"):
        columns_to_add.append(
            sa.Column(
                "profile_scope",
                sa.String(length=20),
                nullable=False,
                server_default="legado",
            )
        )

    for column in columns_to_add:
        op.add_column("entities", column)

    inspector = inspect(bind)
    if not _has_index(inspector, "entities", "uq_entities_internal_number"):
        op.create_index(
            "uq_entities_internal_number",
            "entities",
            ["internal_number"],
            unique=True,
        )

    if bind.dialect.name == "postgresql":
        op.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_single_owner_scope "
                "ON entities (profile_scope) WHERE profile_scope = 'owner'"
            )
        )
    elif bind.dialect.name == "sqlite":
        op.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_single_owner_scope "
                "ON entities (profile_scope) WHERE profile_scope = 'owner'"
            )
        )


def _ensure_members_table_updates() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if "members" not in table_names:
        return

    columns_to_add: list[sa.Column] = []
    if not _has_column(inspector, "members", "freguesia"):
        columns_to_add.append(sa.Column("freguesia", sa.String(length=120), nullable=True))
    if not _has_column(inspector, "members", "whatsapp_verification_status"):
        columns_to_add.append(
            sa.Column(
                "whatsapp_verification_status",
                sa.String(length=20),
                nullable=False,
                server_default="unknown",
            )
        )
    if not _has_column(inspector, "members", "whatsapp_notice_opt_in"):
        columns_to_add.append(
            sa.Column(
                "whatsapp_notice_opt_in",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
    if not _has_column(inspector, "members", "whatsapp_last_check_at"):
        columns_to_add.append(sa.Column("whatsapp_last_check_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column(inspector, "members", "whatsapp_last_error"):
        columns_to_add.append(sa.Column("whatsapp_last_error", sa.Text(), nullable=True))
    if not _has_column(inspector, "members", "whatsapp_last_wa_id"):
        columns_to_add.append(sa.Column("whatsapp_last_wa_id", sa.String(length=64), nullable=True))
    if not _has_column(inspector, "members", "whatsapp_last_message_id"):
        columns_to_add.append(sa.Column("whatsapp_last_message_id", sa.String(length=128), nullable=True))
    if not _has_column(inspector, "members", "training_discipulado_verbo_vida"):
        columns_to_add.append(
            sa.Column(
                "training_discipulado_verbo_vida",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
    if not _has_column(inspector, "members", "training_ebvv"):
        columns_to_add.append(sa.Column("training_ebvv", sa.Boolean(), nullable=False, server_default=sa.false()))
    if not _has_column(inspector, "members", "training_rhema"):
        columns_to_add.append(sa.Column("training_rhema", sa.Boolean(), nullable=False, server_default=sa.false()))
    if not _has_column(inspector, "members", "training_escola_ministerial"):
        columns_to_add.append(
            sa.Column(
                "training_escola_ministerial",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
    if not _has_column(inspector, "members", "training_escola_missoes"):
        columns_to_add.append(
            sa.Column(
                "training_escola_missoes",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
    if not _has_column(inspector, "members", "training_outros"):
        columns_to_add.append(sa.Column("training_outros", sa.String(length=255), nullable=True))
    if not _has_column(inspector, "members", "profile_custom_fields"):
        columns_to_add.append(sa.Column("profile_custom_fields", sa.Text(), nullable=True))

    for column in columns_to_add:
        op.add_column("members", column)


def _ensure_sidebar_menu_settings_table() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if "sidebar_menu_settings" not in table_names:
        op.create_table(
            "sidebar_menu_settings",
            sa.Column("menu_key", sa.String(length=50), nullable=False),
            sa.Column("menu_label", sa.String(length=120), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("menu_config", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("menu_key"),
        )
        return

    if not _has_column(inspector, "sidebar_menu_settings", "menu_config"):
        op.add_column("sidebar_menu_settings", sa.Column("menu_config", sa.Text(), nullable=True))


def _ensure_global_profiles_data() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if "profiles" not in table_names:
        return

    rows = bind.execute(
        text("SELECT id, name, description, is_active FROM profiles")
    ).mappings().all()
    existing_by_name = {
        str(row["name"] or "").strip().lower(): row for row in rows
    }
    defaults = (
        ("ADMIN", "Perfil administrativo global."),
        ("SUPER USER", "Perfil com permissoes elevadas."),
        ("USER", "Perfil base de utilizador."),
    )
    for profile_name, profile_description in defaults:
        normalized = profile_name.strip().lower()
        row = existing_by_name.get(normalized)
        if row is None:
            bind.execute(
                text(
                    "INSERT INTO profiles (name, description, is_active) "
                    "VALUES (:name, :description, :is_active)"
                ),
                {"name": profile_name, "description": profile_description, "is_active": True},
            )
            continue
        bind.execute(
            text(
                "UPDATE profiles SET is_active = :is_active, description = COALESCE(NULLIF(description, ''), :description) "
                "WHERE id = :id"
            ),
            {"id": int(row["id"]), "is_active": True, "description": profile_description},
        )


def upgrade() -> None:
    _ensure_entities_table_updates()
    _ensure_members_table_updates()
    _ensure_sidebar_menu_settings_table()
    _ensure_global_profiles_data()


def downgrade() -> None:
    # Conservative downgrade for safety: do not drop migrated columns/tables automatically.
    pass

