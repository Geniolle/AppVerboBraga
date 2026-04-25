from __future__ import annotations

from typing import Any

from appverbo.core import *  # noqa: F403,F401
from appverbo.services.permissions import get_user_entity_permissions

def get_session_user_id(request: Request) -> int | None:
    raw_user_id = request.session.get("user_id")
    if isinstance(raw_user_id, int):
        return raw_user_id
    if isinstance(raw_user_id, str) and raw_user_id.isdigit():
        return int(raw_user_id)
    return None

def get_session_entity_id(request: Request) -> int | None:
    raw_entity_id = request.session.get("entity_id")
    if isinstance(raw_entity_id, int):
        return raw_entity_id
    if isinstance(raw_entity_id, str) and raw_entity_id.isdigit():
        return int(raw_entity_id)
    return None

def set_session_entity_context(request: Request, entity_context: dict[str, Any] | None) -> None:
    if entity_context is None:
        request.session.pop("entity_id", None)
        request.session.pop("entity_name", None)
        request.session.pop("entity_logo_url", None)
        return

    request.session["entity_id"] = int(entity_context["id"])
    request.session["entity_name"] = str(entity_context.get("name") or "")
    request.session["entity_logo_url"] = str(entity_context.get("logo_url") or "")

def get_entity_context_for_user(
    session: Session,
    user_id: int,
    login_email: str,
    entity_id: int | None = None,
) -> dict[str, Any] | None:
    permissions = get_user_entity_permissions(
        session,
        user_id,
        login_email,
        entity_id,
    )
    can_manage_all_entities = bool(permissions["can_manage_all_entities"])

    if entity_id is not None:
        selected_entity = session.get(Entity, entity_id)
        if selected_entity is None or not selected_entity.is_active:
            return None

        if can_manage_all_entities:
            return {
                "id": int(selected_entity.id),
                "name": selected_entity.name or "",
                "logo_url": selected_entity.logo_url or "",
            }

        has_membership = session.execute(
            select(MemberEntity.id)
           .join(User, User.member_id == MemberEntity.member_id)
           .where(
                User.id == user_id,
                MemberEntity.entity_id == entity_id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
           .limit(1)
        ).scalar_one_or_none()
        if has_membership is None:
            return None

        return {
            "id": int(selected_entity.id),
            "name": selected_entity.name or "",
            "logo_url": selected_entity.logo_url or "",
        }

    linked_entity = session.execute(
        select(Entity.id, Entity.name, Entity.logo_url)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .join(User, User.member_id == MemberEntity.member_id)
       .where(
            User.id == user_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
       .order_by(MemberEntity.id.asc())
       .limit(1)
    ).one_or_none()
    if linked_entity is not None:
        return {
            "id": int(linked_entity.id),
            "name": linked_entity.name or "",
            "logo_url": linked_entity.logo_url or "",
        }

    if can_manage_all_entities:
        first_active_entity = session.execute(
            select(Entity.id, Entity.name, Entity.logo_url)
           .where(Entity.is_active.is_(True))
           .order_by(Entity.name.asc())
           .limit(1)
        ).one_or_none()
        if first_active_entity is not None:
            return {
                "id": int(first_active_entity.id),
                "name": first_active_entity.name or "",
                "logo_url": first_active_entity.logo_url or "",
            }

    return None

def get_current_user(request: Request, session: Session) -> dict[str, Any] | None:
    user_id = get_session_user_id(request)
    if user_id is None:
        return None

    row = session.execute(
        select(User.id, User.login_email, User.account_status, Member.full_name)
       .join(Member, Member.id == User.member_id)
       .where(User.id == user_id)
    ).one_or_none()

    if row is None or row.account_status != UserAccountStatus.ACTIVE.value:
        request.session.clear()
        return None

    selected_entity_context = get_entity_context_for_user(
        session,
        row.id,
        row.login_email,
        get_session_entity_id(request),
    )
    if selected_entity_context is None:
        selected_entity_context = get_entity_context_for_user(
            session,
            row.id,
            row.login_email,
            None,
        )
    set_session_entity_context(request, selected_entity_context)

    return {
        "id": row.id,
        "full_name": row.full_name,
        "login_email": row.login_email,
    }

__all__ = [
    "get_session_user_id",
    "get_session_entity_id",
    "set_session_entity_context",
    "get_entity_context_for_user",
    "get_current_user",
]
