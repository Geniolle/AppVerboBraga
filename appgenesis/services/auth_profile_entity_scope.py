from __future__ import annotations

from dataclasses import replace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.admin_subprocesses.models import AdminFieldConfig, AdminSubprocessConfig
from appgenesis.core import ENTITY_PROFILE_SCOPE_LEGADO
from appgenesis.models import Entity

AUTH_PROFILE_ENTITY_NUMBER_FIELD_KEY = "entity_number"


########################################################################################
# (1) CONTEXTO DA ENTIDADE ATIVA PARA PERFIL DE AUTORIZACAO
########################################################################################


def build_auth_profile_entity_context_v1(
    session: Session,
    *,
    selected_entity_id: Any,
    permissions: dict[str, Any] | None = None,
) -> dict:
    selected_entity = None
    if selected_entity_id:
        selected_entity = session.execute(
            select(
                Entity.id,
                Entity.name,
                Entity.entity_number,
                Entity.profile_scope,
            )
            .where(Entity.id == selected_entity_id, Entity.is_active.is_(True))
            .limit(1)
        ).first()

    selected_entity_number = (
        str(selected_entity.entity_number) if selected_entity and selected_entity.entity_number else ""
    )
    selected_entity_scope = (
        selected_entity.profile_scope if selected_entity else ENTITY_PROFILE_SCOPE_LEGADO
    ) or ENTITY_PROFILE_SCOPE_LEGADO

    return {
        "selected_entity_id": int(selected_entity.id) if selected_entity is not None else None,
        "selected_entity_name": (
            str(selected_entity.name or "").strip() if selected_entity is not None else ""
        ),
        "selected_entity_number": selected_entity_number,
        "selected_entity_scope": selected_entity_scope,
    }


########################################################################################
# (2) CONFIGURACAO DE FORMULARIO (injeta o Nº da entidade no campo read-only)
########################################################################################


def build_auth_profile_config_for_context_v1(
    config: AdminSubprocessConfig,
    entity_context: dict,
) -> AdminSubprocessConfig:
    entity_number_display = str((entity_context or {}).get("selected_entity_number") or "")

    adjusted_fields: list[AdminFieldConfig] = []
    for field in config.fields:
        if field.key == AUTH_PROFILE_ENTITY_NUMBER_FIELD_KEY:
            adjusted_fields.append(replace(field, default_value=entity_number_display))
            continue
        adjusted_fields.append(field)

    return replace(config, fields=tuple(adjusted_fields))


__all__ = [
    "AUTH_PROFILE_ENTITY_NUMBER_FIELD_KEY",
    "build_auth_profile_config_for_context_v1",
    "build_auth_profile_entity_context_v1",
]
