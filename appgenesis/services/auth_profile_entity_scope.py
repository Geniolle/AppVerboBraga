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
    session_options: list[tuple[str, str]] | None = None,
    menu_options: list[tuple[str, str]] | None = None,
    menu_option_groups: list[tuple[str, str]] | None = None,
    tab_options: list[tuple[str, str]] | None = None,
    tab_option_groups: list[tuple[str, str]] | None = None,
    authorization_profile_options: list[tuple[str, str]] | None = None,
) -> AdminSubprocessConfig:
    entity_number_display = str((entity_context or {}).get("selected_entity_number") or "")

    adjusted_fields: list[AdminFieldConfig] = []
    for field in config.fields:
        if field.key == AUTH_PROFILE_ENTITY_NUMBER_FIELD_KEY:
            adjusted_fields.append(replace(field, default_value=entity_number_display))
            continue
        if field.key == "authorization_profiles":
            adjusted_fields.append(replace(field, options=tuple(authorization_profile_options or ())))
            continue
        if field.key == "session_origin":
            adjusted_fields.append(replace(field, options=tuple(session_options or ())))
            continue
        if field.key == "tab_origin":
            adjusted_fields.append(
                replace(
                    field,
                    options=tuple(tab_options or ()),
                    option_groups=tuple(tab_option_groups or ()),
                    depends_on_input="auth_profile_menu_origin",
                )
            )
            continue
        if field.key == "menu_origin":
            adjusted_fields.append(
                replace(
                    field,
                    options=tuple(menu_options or ()),
                    option_groups=tuple(menu_option_groups or ()),
                    depends_on_input="auth_profile_session_origin",
                )
            )
            continue
        adjusted_fields.append(field)

    return replace(config, fields=tuple(adjusted_fields))


########################################################################################
# (3) SISTEMA (visibility_scope_mode): so o owner escolhe; as outras entidades criam Legado
########################################################################################

# Campos SISTEMA (visibility_scope_mode) de todos os processos.
VISIBILITY_SCOPE_INPUTS_V1 = (
    "auth_profile_visibility_scope_mode",
    "section_visibility_scope_mode",
    "menu_visibility_scope",
    "functions_visibility_scope_mode",
)


def get_entity_profile_scope_v1(session: Session, entity_id: int | None) -> str:
    if entity_id is None:
        return ENTITY_PROFILE_SCOPE_LEGADO
    scope = session.execute(
        select(Entity.profile_scope).where(Entity.id == entity_id).limit(1)
    ).scalar()
    return str(scope or ENTITY_PROFILE_SCOPE_LEGADO).strip().lower()


def resolve_visibility_scope_for_entity_v1(submitted_scope: Any, entity_profile_scope: str) -> str:
    # Entidade owner: escolhe livremente. Outras entidades: sempre Legado (criam so para si).
    if str(entity_profile_scope or "").strip().lower() == "owner":
        return str(submitted_scope or "").strip().lower() or "owner"
    return ENTITY_PROFILE_SCOPE_LEGADO


def lock_visibility_scope_field_v1(
    config: AdminSubprocessConfig, entity_profile_scope: str
) -> AdminSubprocessConfig:
    if str(entity_profile_scope or "").strip().lower() == "owner":
        return config
    adjusted_fields: list[AdminFieldConfig] = []
    for field in config.fields:
        if field.input_name in VISIBILITY_SCOPE_INPUTS_V1:
            adjusted_fields.append(
                replace(
                    field,
                    options=(("legado", "Legado"),),
                    default_value="legado",
                    locked=True,
                )
            )
            continue
        adjusted_fields.append(field)
    return replace(config, fields=tuple(adjusted_fields))


__all__ = [
    "AUTH_PROFILE_ENTITY_NUMBER_FIELD_KEY",
    "get_entity_profile_scope_v1",
    "lock_visibility_scope_field_v1",
    "resolve_visibility_scope_for_entity_v1",
    "build_auth_profile_config_for_context_v1",
    "build_auth_profile_entity_context_v1",
]
