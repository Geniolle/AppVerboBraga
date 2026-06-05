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
