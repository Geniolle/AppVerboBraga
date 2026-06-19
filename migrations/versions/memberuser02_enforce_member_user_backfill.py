"""Ensure every existing member has a pending user account.

Revision ID: memberuser02
Revises: memberuser01
Create Date: 2026-06-19 12:00:00.000000
"""

from __future__ import annotations

import base64
import hashlib
import secrets

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func, select


revision = "memberuser02"
down_revision = "memberuser01"
branch_labels = None
depends_on = None


members = sa.table(
    "members",
    sa.column("id", sa.Integer),
    sa.column("email", sa.String),
)

users = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("member_id", sa.Integer),
    sa.column("login_email", sa.String),
    sa.column("password_hash", sa.Text),
    sa.column("account_status", sa.String),
    sa.column("created_by_user_id", sa.Integer),
)


# ###################################################################################
# (1) PASSWORD TEMPORARIA SEGURA
# ###################################################################################

def _build_temporary_password_hash() -> str:
    raw_password = secrets.token_urlsafe(24)
    iterations = 390000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


# ###################################################################################
# (2) VALIDACAO DE EMAILS
# ###################################################################################

def _find_duplicate_emails(
    connection: sa.engine.Connection,
    table: sa.TableClause,
    column_name: str,
) -> list[tuple[str, int]]:
    column = table.c[column_name]
    rows = connection.execute(
        select(
            func.lower(func.trim(column)).label("email_key"),
            func.count().label("total"),
        )
        .where(column.is_not(None))
        .where(func.trim(column) != "")
        .group_by(func.lower(func.trim(column)))
        .having(func.count() > 1)
        .order_by(func.lower(func.trim(column)))
    ).all()
    return [
        (str(row.email_key or "").strip(), int(row.total or 0))
        for row in rows
        if str(row.email_key or "").strip()
    ]


def _raise_for_duplicate_emails(connection: sa.engine.Connection) -> None:
    duplicate_member_emails = _find_duplicate_emails(connection, members, "email")
    if duplicate_member_emails:
        details = ", ".join(
            f"{email} ({total})" for email, total in duplicate_member_emails
        )
        raise RuntimeError(
            "Não foi possível executar o backfill: existem emails duplicados em members: "
            f"{details}."
        )

    duplicate_user_emails = _find_duplicate_emails(connection, users, "login_email")
    if duplicate_user_emails:
        details = ", ".join(
            f"{email} ({total})" for email, total in duplicate_user_emails
        )
        raise RuntimeError(
            "Não foi possível executar o backfill: existem emails duplicados em users: "
            f"{details}."
        )


def _load_user_email_map(connection: sa.engine.Connection) -> dict[str, int]:
    rows = connection.execute(
        select(users.c.member_id, users.c.login_email)
        .where(users.c.login_email.is_not(None))
        .where(func.trim(users.c.login_email) != "")
    ).all()
    return {
        str(row.login_email).strip().lower(): int(row.member_id)
        for row in rows
        if str(row.login_email or "").strip()
    }


# ###################################################################################
# (3) BACKFILL DE MEMBERS SEM USERS
# ###################################################################################

def upgrade() -> None:
    connection = op.get_bind()
    _raise_for_duplicate_emails(connection)
    user_email_map = _load_user_email_map(connection)

    missing_members = connection.execute(
        select(members.c.id, members.c.email)
        .select_from(members.outerjoin(users, users.c.member_id == members.c.id))
        .where(users.c.id.is_(None))
        .order_by(members.c.id.asc())
    ).all()

    for member in missing_members:
        member_id = int(member.id)
        clean_email = str(member.email or "").strip().lower()

        if not clean_email or "@" not in clean_email:
            raise RuntimeError(
                "Não foi possível executar o backfill: o membro "
                f"{member_id} não tem um email válido."
            )

        existing_member_id = user_email_map.get(clean_email)
        if existing_member_id is not None and existing_member_id != member_id:
            raise RuntimeError(
                "Não foi possível executar o backfill: o email "
                f"'{clean_email}' já pertence ao utilizador do membro "
                f"{existing_member_id}."
            )

        connection.execute(
            users.insert().values(
                member_id=member_id,
                login_email=clean_email,
                password_hash=_build_temporary_password_hash(),
                account_status="pending",
                created_by_user_id=None,
            )
        )
        user_email_map[clean_email] = member_id
        print(
            "BACKFILL_MEMBER_USER_V2 "
            f"member_id={member_id} email={clean_email} account_status=pending",
            flush=True,
        )


def downgrade() -> None:
    raise RuntimeError("Esta migration de backfill não é reversível com segurança.")
