from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.models import Member, MemberStatus, User, UserAccountStatus


# ###################################################################################
# (1) HASH E TEMPORARIOS DE PASSWORD
# ###################################################################################

def _hash_password_v1(raw_password: str) -> str:
    iterations = 390000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def _build_temporary_password_hash_v1() -> str:
    return _hash_password_v1(secrets.token_urlsafe(24))


def _normalize_user_account_status_v1(raw_status: Any) -> str:
    clean_status = str(raw_status or "").strip().lower()
    valid_statuses = {
        UserAccountStatus.PENDING.value,
        UserAccountStatus.ACTIVE.value,
        UserAccountStatus.INACTIVE.value,
        UserAccountStatus.BLOCKED.value,
    }

    if clean_status not in valid_statuses:
        return UserAccountStatus.PENDING.value

    return clean_status


# ###################################################################################
# (2) SINCRONIZACAO DE STATUS MEMBER <-> USER
# ###################################################################################

def member_status_for_user_account_status_v1(raw_status: Any) -> str:
    normalized_status = _normalize_user_account_status_v1(raw_status)

    if normalized_status in {
        UserAccountStatus.ACTIVE.value,
        UserAccountStatus.PENDING.value,
    }:
        return MemberStatus.ACTIVE.value

    return MemberStatus.INACTIVE.value


# ###################################################################################
# (3) HELPER CENTRAL DE GARANTIA DE USER POR MEMBER
# ###################################################################################

def ensure_user_for_member_v1(
    session: Session,
    member: Member,
    *,
    status: str = UserAccountStatus.PENDING.value,
    created_by_user_id: int | None = None,
    password: str | None = None,
    user_id: int | None = None,
) -> User:
    member_id = getattr(member, "id", None)
    if member_id is None:
        session.flush()
        member_id = getattr(member, "id", None)

    if member_id is None:
        raise ValueError("Membro precisa estar persistido antes de garantir a conta.")

    clean_email = str(member.email or "").strip().lower()
    if not clean_email:
        raise ValueError("Email do membro é obrigatório para garantir a conta.")

    member.email = clean_email

    requested_status = _normalize_user_account_status_v1(status)
    member_status = member_status_for_user_account_status_v1(requested_status)

    user = session.execute(
        select(User).where(User.member_id == int(member_id))
    ).scalar_one_or_none()

    if user is None:
        user = session.execute(
            select(User).where(func.lower(User.login_email) == clean_email)
        ).scalar_one_or_none()

        if user is not None and int(user.member_id) != int(member_id):
            raise ValueError("Email já está associado a outro utilizador.")

    password_value = str(password or "").strip()
    password_hash = _hash_password_v1(password_value) if password_value else _build_temporary_password_hash_v1()

    if user is None:
        user_kwargs: dict[str, Any] = {
            "member_id": int(member_id),
            "login_email": clean_email,
            "password_hash": password_hash,
            "account_status": requested_status,
        }

        if isinstance(user_id, int) and user_id > 0:
            user_kwargs["id"] = int(user_id)

        if isinstance(created_by_user_id, int) and created_by_user_id > 0:
            user_kwargs["created_by_user_id"] = int(created_by_user_id)

        user = User(**user_kwargs)
        session.add(user)
        session.flush()

    user.login_email = clean_email
    user.password_hash = password_hash if password_value else (
        user.password_hash if str(user.password_hash or "").strip() else password_hash
    )
    user.account_status = requested_status
    member.member_status = member_status
    member.is_collaborator = True

    if user.created_by_user_id is None and isinstance(created_by_user_id, int) and created_by_user_id > 0:
        user.created_by_user_id = int(created_by_user_id)

    return user


ensure_user_for_member = ensure_user_for_member_v1
member_status_for_user_account_status = member_status_for_user_account_status_v1


__all__ = [
    "ensure_user_for_member_v1",
    "ensure_user_for_member",
    "member_status_for_user_account_status_v1",
    "member_status_for_user_account_status",
]
