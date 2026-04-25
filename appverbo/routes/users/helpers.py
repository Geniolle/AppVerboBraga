from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.core import *  # noqa: F403,F401
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

def _extract_email_domain(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()
    if "@" not in clean_email:
        return ""
    _, domain = clean_email.split("@", 1)
    return domain.strip()

def _resolve_entity_from_user_email(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return None, "Email inválido para determinar entidade."

    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
    if not permissions.get("can_manage_all_entities"):
        allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
        if not allowed_entity_ids:
            return None, "Sem entidades disponíveis para este utilizador."
        query = query.where(Entity.id.in_(allowed_entity_ids))

    scoped_entities = list(session.execute(query).scalars().all())
    if not scoped_entities:
        return None, "Sem entidades ativas disponíveis para atribuição."

    exact_matches = [
        entity
        for entity in scoped_entities
        if (entity.email or "").strip().lower() == clean_email
    ]
    if len(exact_matches) == 1:
        return exact_matches[0], ""
    if len(exact_matches) > 1:
        return (
            None,
            "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades.",
        )

    email_domain = _extract_email_domain(clean_email)
    if email_domain:
        domain_matches = [
            entity
            for entity in scoped_entities
            if _extract_email_domain((entity.email or "").strip().lower()) == email_domain
        ]
        if len(domain_matches) == 1:
            return domain_matches[0], ""
        if len(domain_matches) > 1:
            return (
                None,
                "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades.",
            )

    if not permissions.get("can_manage_all_entities") and len(scoped_entities) == 1:
        return scoped_entities[0], ""

    return (
        None,
        "Não foi possível determinar a entidade pelo email. "
        "Verifique o email da entidade (domínio) ou ajuste os dados.",
    )

def _get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    entity_row = session.execute(
        select(Entity.id, Entity.name)
       .join(MemberEntity, MemberEntity.entity_id == Entity.id)
       .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
       .order_by(MemberEntity.id.asc())
       .limit(1)
    ).one_or_none()
    if entity_row is None:
        return None, "-"
    return int(entity_row.id), str(entity_row.name or "-")

def _get_primary_entity_name_for_member(session: Session, member_id: int) -> str:
    _, entity_name = _get_primary_entity_for_member(session, member_id)
    return entity_name

def _member_is_within_permissions(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
) -> bool:
    if permissions.get("can_manage_all_entities"):
        return True
    allowed_entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
    if not allowed_entity_ids:
        return False
    scoped_link_id = session.scalar(
        select(MemberEntity.id)
       .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            MemberEntity.entity_id.in_(allowed_entity_ids),
        )
       .limit(1)
    )
    return scoped_link_id is not None

def _is_admin_profile(profile: Profile | None) -> bool:
    if profile is None:
        return False
    profile_name = (profile.name or "").strip().lower()
    if not profile_name:
        return False
    return profile_name in ADMIN_PROFILE_NAMES

def _get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
       .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
       .order_by(MemberEntity.id.asc())
    ).all()
    entity_ids: list[int] = []
    seen: set[int] = set()
    for entity_id in rows:
        if not isinstance(entity_id, int):
            continue
        if entity_id in seen:
            continue
        seen.add(entity_id)
        entity_ids.append(entity_id)
    return entity_ids

def _has_other_active_admin_for_entity(
    session: Session,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    candidate_rows = session.execute(
        select(User.id, User.login_email)
       .join(MemberEntity, MemberEntity.member_id == User.member_id)
       .where(
            MemberEntity.entity_id == entity_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            User.id != excluded_user_id,
            User.account_status == UserAccountStatus.ACTIVE.value,
        )
       .order_by(User.id.asc())
    ).all()
    for row in candidate_rows:
        candidate_user_id = int(row.id)
        candidate_email = str(row.login_email or "")
        if is_admin_user(session, candidate_user_id, candidate_email):
            return True
    return False

def _ensure_not_last_active_admin_for_member(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    entity_ids = _get_active_entity_ids_for_member(session, member_id)
    if not entity_ids:
        return True, ""

    for entity_id in entity_ids:
        if _has_other_active_admin_for_entity(session, entity_id, excluded_user_id):
            continue
        entity_name = session.scalar(
            select(Entity.name).where(Entity.id == entity_id).limit(1)
        )
        clean_entity_name = str(entity_name or f"ID {entity_id}")
        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{clean_entity_name}' ficaria sem Admin ativo."
            ),
        )
    return True, ""
