from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.config.settings import settings
from appverbo.menu_settings import get_owner_entity_scope_id_v1
from appverbo.models import Entity
from appverbo.services.entity_scope import (
    coerce_entity_scope_id_v1,
)


# ###################################################################################
# (1) NORMALIZACAO DO ESCOPO DA ENTIDADE SELECIONADA
# ###################################################################################


def _normalize_entity_profile_scope_v1(value: Any) -> str:
    clean_value = str(value or "").strip().lower()

    if clean_value in {
        settings.ENTITY_PROFILE_SCOPE_OWNER,
        settings.ENTITY_PROFILE_SCOPE_LEGADO,
    }:
        return clean_value

    return ""


def _load_selected_entity_profile_scope_v1(
    *,
    session: Session,
    selected_entity_id: object,
) -> str:
    parsed_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

    if parsed_entity_id is None:
        return ""

    raw_scope = session.execute(
        select(Entity.profile_scope)
        .where(Entity.id == parsed_entity_id)
        .limit(1)
    ).scalar_one_or_none()

    return _normalize_entity_profile_scope_v1(raw_scope)


def _build_entity_internal_number_label_v1(
    *,
    session: Session,
    entity_id: object,
) -> str:
    parsed_entity_id = coerce_entity_scope_id_v1(entity_id)

    if parsed_entity_id is None:
        return ""

    raw_internal_number = session.execute(
        select(Entity.internal_number)
        .where(Entity.id == parsed_entity_id)
        .limit(1)
    ).scalar_one_or_none()

    if raw_internal_number is None:
        return str(parsed_entity_id)

    return str(raw_internal_number).strip()


# ###################################################################################
# (2) REGRAS DE ACESSO A CAMPOS ADICIONAIS DO MENU
# ###################################################################################


def build_menu_additional_fields_access_v1(
    *,
    session: Session,
    selected_entity_id: object,
    can_manage_all_entities: bool,
) -> dict[str, Any]:
    owner_entity_id = get_owner_entity_scope_id_v1(session)
    parsed_selected_entity_id = coerce_entity_scope_id_v1(selected_entity_id)
    selected_entity_scope = _load_selected_entity_profile_scope_v1(
        session=session,
        selected_entity_id=parsed_selected_entity_id,
    )

    if not selected_entity_scope and can_manage_all_entities and owner_entity_id is not None:
        parsed_selected_entity_id = owner_entity_id
        selected_entity_scope = settings.ENTITY_PROFILE_SCOPE_OWNER

    process_owner_fields_enabled = bool(
        can_manage_all_entities
        and selected_entity_scope == settings.ENTITY_PROFILE_SCOPE_OWNER
    )

    legacy_visualization_enabled = bool(
        settings.LEGACY_CAN_VIEW_OWNER_PROCESS_ADDITIONAL_FIELDS
    )

    can_view = False
    can_edit = False
    source_entity_id: int | None = None

    if selected_entity_scope == settings.ENTITY_PROFILE_SCOPE_OWNER:
        can_view = True
        can_edit = process_owner_fields_enabled
        source_entity_id = parsed_selected_entity_id or owner_entity_id
    elif selected_entity_scope == settings.ENTITY_PROFILE_SCOPE_LEGADO:
        can_view = bool(legacy_visualization_enabled and owner_entity_id is not None)
        can_edit = False
        source_entity_id = owner_entity_id if can_view else None

    return {
        "selected_entity_id": parsed_selected_entity_id,
        "selected_entity_scope": selected_entity_scope,
        "selected_entity_label": _build_entity_internal_number_label_v1(
            session=session,
            entity_id=parsed_selected_entity_id,
        ),
        "owner_entity_id": owner_entity_id,
        "process_owner_fields_enabled": process_owner_fields_enabled,
        "can_view": can_view,
        "can_edit": can_edit,
        "is_readonly": bool(can_view and not can_edit),
        "source_entity_id": source_entity_id,
        "source_entity_label": _build_entity_internal_number_label_v1(
            session=session,
            entity_id=source_entity_id,
        ),
        "legacy_visualization_enabled": legacy_visualization_enabled,
        "edit_entity_id": (
            source_entity_id
            if can_edit
            else None
        ),
    }


__all__ = [
    "build_menu_additional_fields_access_v1",
]
