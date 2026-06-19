from __future__ import annotations

from unittest.mock import patch

import sqlalchemy as sa

from migrations.versions import memberuser03_add_member_user_backfill as migration


def _build_migration_database() -> tuple[sa.Engine, sa.Table, sa.Table]:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata = sa.MetaData()
    members = sa.Table(
        "members",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("member_status", sa.String(20), nullable=False),
    )
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("member_id", sa.Integer, nullable=False, unique=True),
        sa.Column("login_email", sa.String(150), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("account_status", sa.String(20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer),
    )
    metadata.create_all(engine)
    return engine, members, users


def test_member_user_backfill_creates_pending_user() -> None:
    engine, members, users = _build_migration_database()

    with engine.begin() as connection:
        connection.execute(
            members.insert().values(
                id=10,
                email="MEMBRO@example.com",
                member_status="inactive",
            )
        )
        with patch.object(migration.op, "get_bind", return_value=connection):
            migration.upgrade()

        row = connection.execute(sa.select(users)).one()

        assert row.member_id == 10
        assert row.login_email == "membro@example.com"
        assert row.account_status == "pending"
        assert row.password_hash.startswith("pbkdf2_sha256$")


def test_member_user_backfill_fails_clearly_for_duplicate_email() -> None:
    engine, members, _ = _build_migration_database()

    with engine.begin() as connection:
        connection.execute(
            members.insert(),
            [
                {"id": 1, "email": "duplicado@example.com", "member_status": "active"},
                {"id": 2, "email": "DUPLICADO@example.com", "member_status": "active"},
            ],
        )

        try:
            with patch.object(migration.op, "get_bind", return_value=connection):
                migration.upgrade()
        except RuntimeError as exc:
            assert "emails duplicados em members" in str(exc)
            assert "duplicado@example.com" in str(exc)
        else:
            raise AssertionError("A migration deveria falhar para emails duplicados.")


def test_member_user_backfill_fails_for_existing_user_email_from_other_member() -> None:
    engine, members, users = _build_migration_database()

    with engine.begin() as connection:
        connection.execute(
            members.insert(),
            [
                {"id": 7, "email": "ocupado@example.com", "member_status": "active"},
                {"id": 8, "email": "livre@example.com", "member_status": "active"},
            ],
        )
        connection.execute(
            users.insert().values(
                member_id=8,
                login_email="ocupado@example.com",
                password_hash="pbkdf2_sha256$390000$c2FsdA==$ZGlnZXN0",
                account_status="active",
                created_by_user_id=None,
            )
        )

        try:
            with patch.object(migration.op, "get_bind", return_value=connection):
                migration.upgrade()
        except RuntimeError as exc:
            assert "ja pertence ao utilizador do membro 8" in str(exc)
            assert "ocupado@example.com" in str(exc)
        else:
            raise AssertionError("A migration deveria falhar para login_email ja ocupado.")
