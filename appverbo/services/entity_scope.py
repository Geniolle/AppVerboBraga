from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity


ENTITY_SCOPE_DEFAULT_LABEL_V1 = "Default"


# ###################################################################################
# (1) NORMALIZACAO DO ESCOPO DE ENTIDADE
# ###################################################################################


def coerce_entity_scope_id_v1(value: object) -> int | None:
    clean_value = str(value or "").strip()

    if not clean_value.isdigit():
        return None

    parsed_value = int(clean_value)
    if parsed_value <= 0:
        return None

    return parsed_value


def resolve_selected_entity_scope_id_v1(context: dict[str, Any] | None = None) -> int | None:
    clean_context = context or {}
    return coerce_entity_scope_id_v1(
        clean_context.get("selected_entity_id") or clean_context.get("entity_id")
    )


def is_record_visible_for_selected_entity_v1(
    *,
    record_entity_id: object,
    selected_entity_id: object,
) -> bool:
    parsed_record_entity_id = coerce_entity_scope_id_v1(record_entity_id)
    parsed_selected_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

    if parsed_record_entity_id is None:
        return True

    if parsed_selected_entity_id is None:
        return False

    return parsed_record_entity_id == parsed_selected_entity_id


# ###################################################################################
# (2) LABELS REUTILIZAVEIS DO ESCOPO
# ###################################################################################


def build_entity_scope_name_map_v1(
    session: Session,
    entity_ids: set[int] | list[int] | tuple[int, ...],
) -> dict[int, str]:
    normalized_entity_ids = sorted(
        {
            parsed_entity_id
            for parsed_entity_id in (
                coerce_entity_scope_id_v1(raw_entity_id)
                for raw_entity_id in entity_ids
            )
            if parsed_entity_id is not None
        }
    )

    if not normalized_entity_ids:
        return {}

    rows = session.execute(
        select(Entity.id, Entity.name).where(Entity.id.in_(normalized_entity_ids))
    ).all()

    return {
        int(row.id): str(row.name or "").strip() or f"Entidade {int(row.id)}"
        for row in rows
        if row.id is not None
    }


def build_entity_scope_label_v1(
    session: Session,
    entity_id: object,
) -> str:
    parsed_entity_id = coerce_entity_scope_id_v1(entity_id)

    if parsed_entity_id is None:
        return ENTITY_SCOPE_DEFAULT_LABEL_V1

    entity_name_by_id = build_entity_scope_name_map_v1(session, [parsed_entity_id])
    return entity_name_by_id.get(parsed_entity_id, f"Entidade {parsed_entity_id}")


def build_entity_scope_internal_number_map_v1(
    session: Session,
    entity_ids: set[int] | list[int] | tuple[int, ...],
) -> dict[int, str]:
    normalized_entity_ids = sorted(
        {
            parsed_entity_id
            for parsed_entity_id in (
                coerce_entity_scope_id_v1(raw_entity_id)
                for raw_entity_id in entity_ids
            )
            if parsed_entity_id is not None
        }
    )

    if not normalized_entity_ids:
        return {}

    rows = session.execute(
        select(Entity.id, Entity.internal_number).where(Entity.id.in_(normalized_entity_ids))
    ).all()

    internal_number_by_id: dict[int, str] = {}

    for row in rows:
        if row.id is None:
            continue

        parsed_entity_id = int(row.id)
        clean_internal_number = str(row.internal_number or "").strip()
        internal_number_by_id[parsed_entity_id] = clean_internal_number or str(parsed_entity_id)

    return internal_number_by_id


def build_entity_scope_display_v1(
    session: Session,
    entity_id: object,
) -> dict[str, str]:
    parsed_entity_id = coerce_entity_scope_id_v1(entity_id)

    if parsed_entity_id is None:
        return {
            "entity_name": "",
            "entity_internal_number": "",
        }

    entity_name = build_entity_scope_label_v1(session, parsed_entity_id)
    entity_internal_number = build_entity_scope_internal_number_map_v1(
        session,
        [parsed_entity_id],
    ).get(parsed_entity_id, str(parsed_entity_id))

    return {
        "entity_name": entity_name,
        "entity_internal_number": entity_internal_number,
    }


def load_entity_profile_scope_v1(
    session: Session,
    entity_id: object,
) -> str:
    parsed_entity_id = coerce_entity_scope_id_v1(entity_id)

    if parsed_entity_id is None:
        return ""

    raw_scope = session.execute(
        select(Entity.profile_scope)
        .where(Entity.id == parsed_entity_id)
        .limit(1)
    ).scalar_one_or_none()

    clean_scope = str(raw_scope or "").strip().lower()

    if clean_scope in {"owner", "legado"}:
        return clean_scope

    return ""
