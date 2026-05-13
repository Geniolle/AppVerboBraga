from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity, MemberEntity, MemberEntityStatus
from appverbo.repositories.member_entity_repository import get_primary_entity_for_member


def extract_email_domain_v1(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()

    if "@" not in clean_email:
        return ""

    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _allowed_entity_ids_v1(permissions: dict[str, Any]) -> set[int]:
    return {
        int(raw_id)
        for raw_id in (permissions.get("allowed_entity_ids") or set())
        if str(raw_id).strip().isdigit()
    }


def resolve_selected_entity_fallback_v1(
    session: Session,
    selected_entity_id: int | None,
    permissions: dict[str, Any],
) -> Entity | None:
    parsed_entity_id: int | None = None

    if selected_entity_id is not None:
        try:
            parsed_entity_id = int(selected_entity_id)
        except (TypeError, ValueError):
            parsed_entity_id = None

    if parsed_entity_id is not None and parsed_entity_id > 0:
        if not permissions.get("can_manage_all_entities"):
            allowed_ids = _allowed_entity_ids_v1(permissions)
            if parsed_entity_id not in allowed_ids:
                return None

        selected_entity = session.execute(
            select(Entity).where(
                Entity.id == parsed_entity_id,
                Entity.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if selected_entity is not None:
            return selected_entity

    stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
        if not allowed_ids:
            return None
        stmt = stmt.where(Entity.id.in_(allowed_ids))

    return session.execute(stmt.limit(1)).scalar_one_or_none()


def resolve_entity_from_user_email_v1(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
    selected_entity_id: int | None = None,
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()

    if clean_email and "@" in clean_email:
        stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

        if not permissions.get("can_manage_all_entities"):
            allowed_ids = sorted(_allowed_entity_ids_v1(permissions))
            if allowed_ids:
                stmt = stmt.where(Entity.id.in_(allowed_ids))
            else:
                return None, "Sem entidades disponíveis para este utilizador."

        entities = list(session.execute(stmt).scalars().all())

        exact_matches = [
            entity
            for entity in entities
            if (entity.email or "").strip().lower() == clean_email
        ]

        if len(exact_matches) == 1:
            return exact_matches[0], ""

        if len(exact_matches) > 1:
            return None, "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades."

        email_domain = extract_email_domain_v1(clean_email)

        if email_domain:
            domain_matches = [
                entity
                for entity in entities
                if extract_email_domain_v1(entity.email or "") == email_domain
            ]

            if len(domain_matches) == 1:
                return domain_matches[0], ""

            if len(domain_matches) > 1:
                return None, "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades."

    fallback_entity = resolve_selected_entity_fallback_v1(
        session=session,
        selected_entity_id=selected_entity_id,
        permissions=permissions,
    )

    if fallback_entity is not None:
        return fallback_entity, ""

    return None, "Não foi possível determinar uma entidade ativa para este convite."


def resolve_edit_entity_v1(
    session: Session,
    *,
    email: str,
    clean_entity_id: str,
    member_id: int,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    selected_entity, error = resolve_entity_from_user_email_v1(
        session=session,
        user_email=email,
        permissions=permissions,
        selected_entity_id=None,
    )

    if selected_entity is not None:
        return selected_entity, ""

    if clean_entity_id.strip().isdigit():
        explicit_entity = session.get(Entity, int(clean_entity_id))

        if explicit_entity is not None:
            can_use = bool(permissions.get("can_manage_all_entities"))

            if not can_use:
                can_use = int(explicit_entity.id) in _allowed_entity_ids_v1(permissions)

            if can_use:
                return explicit_entity, ""

    current_entity_stmt = (
        select(Entity)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(MemberEntity.member_id == int(member_id))
        .order_by(MemberEntity.id.asc())
    )

    if not permissions.get("can_manage_all_entities"):
        allowed_ids = sorted(_allowed_entity_ids_v1(permissions))

        if allowed_ids:
            current_entity_stmt = current_entity_stmt.where(Entity.id.in_(allowed_ids))
        else:
            current_entity_stmt = current_entity_stmt.where(Entity.id == -1)

    current_entity = session.execute(current_entity_stmt.limit(1)).scalar_one_or_none()

    if current_entity is not None:
        return current_entity, ""

    current_entity_id, _ = get_primary_entity_for_member(session, member_id)

    if current_entity_id is not None:
        entity = session.get(Entity, current_entity_id)
        if entity is not None:
            return entity, ""

    return None, error


def execute_resolve_user_entity_v1(
    *,
    session: Session,
    member_id: int,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, Any]:
    stmt = (
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == int(member_id),
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.desc())
    )

    if allowed_entity_ids is not None:
        if allowed_entity_ids:
            stmt = stmt.where(Entity.id.in_(sorted(allowed_entity_ids)))
        else:
            return {"entity_id": None, "entity_name": ""}

    row = session.execute(stmt.limit(1)).one_or_none()

    if row is None:
        return {"entity_id": None, "entity_name": ""}

    return {"entity_id": int(row.id), "entity_name": str(row.name or "")}
