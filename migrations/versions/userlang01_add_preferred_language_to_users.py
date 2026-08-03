from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "userlang01"
down_revision = "systemtype01"
branch_labels = None
depends_on = None

ALLOWED_LANGUAGES = ("pt", "en", "es", "fr")


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _has_check_constraint(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return constraint_name in {
        constraint["name"]
        for constraint in inspector.get_check_constraints(table_name)
        if constraint.get("name")
    }


def upgrade() -> None:
    if not _has_column("users", "preferred_language"):
        op.add_column(
            "users",
            sa.Column(
                "preferred_language",
                sa.String(length=5),
                nullable=True,
                server_default=sa.text("'pt'"),
            ),
        )

    allowed_list = ", ".join(f"'{language}'" for language in ALLOWED_LANGUAGES)
    op.execute(
        sa.text(
            f"""
            UPDATE users
            SET preferred_language = CASE
                WHEN preferred_language IS NULL OR btrim(preferred_language) = '' THEN 'pt'
                WHEN lower(btrim(preferred_language)) IN ({allowed_list}) THEN lower(btrim(preferred_language))
                ELSE 'pt'
            END
            """
        )
    )

    if not _has_check_constraint("users", "ck_users_preferred_language"):
        op.create_check_constraint(
            "ck_users_preferred_language",
            "users",
            "preferred_language IN ('pt', 'en', 'es', 'fr')",
        )

    op.alter_column(
        "users",
        "preferred_language",
        existing_type=sa.String(length=5),
        nullable=False,
        server_default=sa.text("'pt'"),
    )


def downgrade() -> None:
    if _has_check_constraint("users", "ck_users_preferred_language"):
        op.drop_constraint("ck_users_preferred_language", "users", type_="check")

    if _has_column("users", "preferred_language"):
        op.drop_column("users", "preferred_language")
