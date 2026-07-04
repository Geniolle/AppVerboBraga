from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appgenesis.models import Member, MemberStatus, User, UserAccountStatus
from appgenesis.services.passwords import hash_password


# ###################################################################################
# (1) PASSWORD TEMPORARIA
# ###################################################################################

def _build_temporary_password_hash_v1() -> str:
    return hash_password(secrets.token_urlsafe(24))


# ###################################################################################
# (2) SINCRONIZACAO DE STATUS MEMBER <-> USER
# ###################################################################################

def _normalize_user_account_status_v1(raw_status: Any) -> str:
    clean_status = str(raw_status or "").strip().lower()
    valid_statuses = {
        UserAccountStatus.PENDING.value,
        UserAccountStatus.ACTIVE.value,
        UserAccountStatus.INACTIVE.value,
        UserAccountStatus.BLOCKED.value,
    }

    if clean_status not in valid_statuses:
        raise ValueError(f"Estado de conta invalido: {raw_status!r}.")

    return clean_status


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

def ensure_user_for_member(
    session: Session,
    member: Member,
    *,
    status: str = UserAccountStatus.PENDING.value,
    created_by_user_id: int | None = None,
    password: str | None = None,
) -> User:
    member_id = getattr(member, "id", None)
    if member_id is None:
        session.flush()
        member_id = getattr(member, "id", None)

    if member_id is None:
        raise ValueError("Membro precisa estar persistido antes de garantir a conta.")

    clean_email = str(member.email or "").strip().lower()
    if not clean_email:
        raise ValueError("Email do membro e obrigatorio para garantir a conta.")

    member.email = clean_email

    requested_status = _normalize_user_account_status_v1(status)
    member_status = member_status_for_user_account_status_v1(requested_status)

    user_by_member = session.execute(
        select(User).where(User.member_id == int(member_id))
    ).scalar_one_or_none()

    users_by_email = session.execute(
        select(User).where(func.lower(User.login_email) == clean_email)
    ).scalars().all()
    if len(users_by_email) > 1:
        raise ValueError(f"Email duplicado em utilizadores: {clean_email}.")

    user_by_email = users_by_email[0] if users_by_email else None
    if user_by_email is not None and int(user_by_email.member_id) != int(member_id):
        raise ValueError("Email ja esta associado a outro utilizador.")

    if (
        user_by_member is not None
        and user_by_email is not None
        and int(user_by_member.id) != int(user_by_email.id)
    ):
        raise ValueError("Membro e email estao associados a utilizadores diferentes.")

    user = user_by_member or user_by_email
    user_was_created = user is None
    password_value = "" if password is None else str(password)

    if user_was_created:
        password_hash = (
            hash_password(password_value)
            if password_value
            else _build_temporary_password_hash_v1()
        )
        user_kwargs: dict[str, Any] = {
            "member_id": int(member_id),
            "login_email": clean_email,
            "password_hash": password_hash,
            "account_status": requested_status,
        }

        if isinstance(created_by_user_id, int) and created_by_user_id > 0:
            user_kwargs["created_by_user_id"] = int(created_by_user_id)

        user = User(**user_kwargs)
        session.add(user)
        session.flush()

    user.login_email = clean_email
    if password_value and not user_was_created:
        user.password_hash = hash_password(password_value)
    elif not str(user.password_hash or "").strip():
        user.password_hash = _build_temporary_password_hash_v1()
    user.account_status = requested_status
    member.member_status = member_status
    member.is_collaborator = True

    if (
        user.created_by_user_id is None
        and isinstance(created_by_user_id, int)
        and created_by_user_id > 0
    ):
        user.created_by_user_id = int(created_by_user_id)

    session.flush()
    return user


ensure_user_for_member_v1 = ensure_user_for_member
member_status_for_user_account_status = member_status_for_user_account_status_v1


__all__ = [
    "ensure_user_for_member_v1",
    "ensure_user_for_member",
    "member_status_for_user_account_status_v1",
    "member_status_for_user_account_status",
]
