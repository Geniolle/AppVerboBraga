from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus, Profile, User, UserAccountStatus
from appverbo.repositories.member_entity_repository import get_active_entity_ids_for_member
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions


def allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def member_is_within_permissions_v1(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True

    allowed_ids = sorted(allowed_entity_ids_v1(permissions))

    if not allowed_ids:
        return False

    scoped_link_id = session.scalar(
        select(MemberEntity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_ids),
        )
        .limit(1)
    )

    return scoped_link_id is not None


def is_admin_profile_v1(profile: Profile | None) -> bool:
    if profile is None:
        return False

    clean_name = (profile.name or "").strip().lower()

    return clean_name in {"admin", "administrador"}


def _has_other_active_admin_for_entity_v1(
    session: Session,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    rows = session.execute(
        select(User.id, User.login_email)
        .join(MemberEntity, MemberEntity.member_id == User.member_id)
        .where(
            MemberEntity.entity_id == int(entity_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            User.id != int(excluded_user_id),
            User.account_status == UserAccountStatus.ACTIVE.value,
        )
        .order_by(User.id.asc())
    ).all()

    for row in rows:
        if is_admin_user(session, int(row.id), str(row.login_email or "")):
            return True

    return False


def ensure_not_last_active_admin_for_member_v1(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = get_active_entity_ids_for_member(session, int(member_id))

    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if _has_other_active_admin_for_entity_v1(session, entity_id, excluded_user_id):
            continue

        entity_name = session.scalar(
            select(Entity.name).where(Entity.id == int(entity_id)).limit(1)
        )
        display_name = str(entity_name or f"ID {entity_id}")

        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{display_name}' ficaria sem Admin ativo."
            ),
        )

    return True, ""


def execute_get_user_permissions_v1(
    *,
    session: Session,
    actor_user_id: int,
    actor_login_email: str,
    selected_entity_id: int | None,
) -> dict[str, Any]:
    return get_user_entity_permissions(
        session,
        int(actor_user_id),
        str(actor_login_email),
        selected_entity_id,
    )
