from __future__ import annotations

from dataclasses import replace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.admin_subprocesses.models import AdminFieldConfig, AdminSubprocessConfig
from appgenesis.core import ENTITY_PROFILE_SCOPE_LEGADO, ENTITY_PROFILE_SCOPE_OWNER
from appgenesis.models import Entity

AUTH_PROFILE_ENTITY_SCOPE_FIELD_KEY = "entity_scope"
AUTH_PROFILE_ENTITY_SCOPE_INPUT_NAME = "auth_profile_entity_scope"
AUTH_PROFILE_ENTITY_SCOPE_STORAGE_KEY = "__entity_scope_mode"
AUTH_PROFILE_ENTITY_SCOPE_LABEL_STORAGE_KEY = "__entity_scope_label"
AUTH_PROFILE_ENTITY_SCOPE_ENTITY = "entity"
AUTH_PROFILE_ENTITY_SCOPE_SYSTEM = "system"
AUTH_PROFILE_ENTITY_SCOPE_ENTITY_LABEL = "Entidade atual"
AUTH_PROFILE_ENTITY_SCOPE_SYSTEM_LABEL = "Todo o sistema"


# ###################################################################################
# (1) NORMALIZACAO DO ESCOPO DE ENTIDADE
# ###################################################################################
def normalize_auth_profile_entity_scope_v1(
    raw_value: Any,
    *,
    fallback: str = AUTH_PROFILE_ENTITY_SCOPE_ENTITY,
) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {
        AUTH_PROFILE_ENTITY_SCOPE_ENTITY,
        AUTH_PROFILE_ENTITY_SCOPE_SYSTEM,
    }:
        return clean_value
    return fallback


def resolve_auth_profile_entity_scope_from_values_v1(
    values: dict[str, Any] | None,
) -> str:
    if not isinstance(values, dict):
        return AUTH_PROFILE_ENTITY_SCOPE_ENTITY

    explicit_scope = normalize_auth_profile_entity_scope_v1(
        values.get(AUTH_PROFILE_ENTITY_SCOPE_STORAGE_KEY),
        fallback="",
    )
    if explicit_scope:
        return explicit_scope

    if str(values.get("__numero_entidade") or "").strip():
        return AUTH_PROFILE_ENTITY_SCOPE_ENTITY

    return AUTH_PROFILE_ENTITY_SCOPE_SYSTEM


# ###################################################################################
# (2) CONTEXTO DA ENTIDADE ATIVA PARA PERFIL DE AUTORIZACAO
# ###################################################################################
def build_auth_profile_entity_context_v1(
    session: Session,
    *,
    selected_entity_id: int | None,
    permissions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_permissions = permissions or {}
    selected_entity = None

    if selected_entity_id is not None:
        selected_entity = session.execute(
            select(
                Entity.id,
                Entity.name,
                Entity.entity_number,
                Entity.profile_scope,
            )
            .where(Entity.id == selected_entity_id, Entity.is_active.is_(True))
            .limit(1)
        ).one_or_none()

    selected_entity_number = ""
    selected_entity_scope = ENTITY_PROFILE_SCOPE_LEGADO
    if selected_entity is not None and selected_entity.entity_number is not None:
        selected_entity_number = str(selected_entity.entity_number)
    if selected_entity is not None:
        selected_entity_scope = str(
            selected_entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO
        ).strip().lower() or ENTITY_PROFILE_SCOPE_LEGADO

    can_manage_tenant_structure = bool(
        safe_permissions.get(
            "can_manage_tenant_structure",
            safe_permissions.get("can_manage_all_entities", False),
        )
    )
    allowed_entity_ids = safe_permissions.get("allowed_structure_entity_ids") or safe_permissions.get(
        "allowed_entity_ids"
    ) or set()
    has_selected_entity_access = bool(
        selected_entity is not None
        and (
            can_manage_tenant_structure
            or int(selected_entity.id) in {int(raw_id) for raw_id in allowed_entity_ids}
        )
    )
    allow_system_scope = bool(
        has_selected_entity_access and selected_entity_scope == ENTITY_PROFILE_SCOPE_OWNER
    )

    field_options: list[tuple[str, str]] = [
        (
            AUTH_PROFILE_ENTITY_SCOPE_ENTITY,
            AUTH_PROFILE_ENTITY_SCOPE_ENTITY_LABEL,
        )
    ]
    if allow_system_scope:
        field_options.append(
            (
                AUTH_PROFILE_ENTITY_SCOPE_SYSTEM,
                AUTH_PROFILE_ENTITY_SCOPE_SYSTEM_LABEL,
            )
        )

    return {
        "selected_entity_id": int(selected_entity.id) if selected_entity is not None else None,
        "selected_entity_name": str(selected_entity.name or "").strip()
        if selected_entity is not None
        else "",
        "selected_entity_number": selected_entity_number,
        "selected_entity_scope": selected_entity_scope,
        "allow_system_scope": allow_system_scope,
        "allowed_modes": {
            AUTH_PROFILE_ENTITY_SCOPE_ENTITY,
            *(
                [AUTH_PROFILE_ENTITY_SCOPE_SYSTEM]
                if allow_system_scope
                else []
            ),
        },
        "field_options": tuple(field_options),
    }


# ###################################################################################
# (3) LABELS E CONFIGURACAO DE FORMULARIO
# ###################################################################################
def resolve_auth_profile_entity_scope_label_v1(scope_mode: str) -> str:
    resolved_scope_mode = normalize_auth_profile_entity_scope_v1(scope_mode)
    if resolved_scope_mode == AUTH_PROFILE_ENTITY_SCOPE_SYSTEM:
        return AUTH_PROFILE_ENTITY_SCOPE_SYSTEM_LABEL
    return AUTH_PROFILE_ENTITY_SCOPE_ENTITY_LABEL


def build_auth_profile_config_for_context_v1(
    config: AdminSubprocessConfig,
    entity_context: dict[str, Any],
    *,
    current_scope_mode: str = "",
) -> AdminSubprocessConfig:
    current_value = normalize_auth_profile_entity_scope_v1(
        current_scope_mode,
        fallback=AUTH_PROFILE_ENTITY_SCOPE_ENTITY,
    )
    field_options = list(entity_context.get("field_options") or [])
    if (
        current_value == AUTH_PROFILE_ENTITY_SCOPE_SYSTEM
        and all(option_value != AUTH_PROFILE_ENTITY_SCOPE_SYSTEM for option_value, _ in field_options)
    ):
        field_options.append(
            (
                AUTH_PROFILE_ENTITY_SCOPE_SYSTEM,
                AUTH_PROFILE_ENTITY_SCOPE_SYSTEM_LABEL,
            )
        )

    adjusted_fields: list[AdminFieldConfig] = []
    for field in config.fields:
        if field.key == AUTH_PROFILE_ENTITY_SCOPE_FIELD_KEY:
            adjusted_fields.append(
                replace(
                    field,
                    options=tuple(field_options),
                )
            )
            continue
        adjusted_fields.append(field)

    return replace(config, fields=tuple(adjusted_fields))


__all__ = [
    "AUTH_PROFILE_ENTITY_SCOPE_ENTITY",
    "AUTH_PROFILE_ENTITY_SCOPE_ENTITY_LABEL",
    "AUTH_PROFILE_ENTITY_SCOPE_FIELD_KEY",
    "AUTH_PROFILE_ENTITY_SCOPE_INPUT_NAME",
    "AUTH_PROFILE_ENTITY_SCOPE_LABEL_STORAGE_KEY",
    "AUTH_PROFILE_ENTITY_SCOPE_STORAGE_KEY",
    "AUTH_PROFILE_ENTITY_SCOPE_SYSTEM",
    "AUTH_PROFILE_ENTITY_SCOPE_SYSTEM_LABEL",
    "build_auth_profile_config_for_context_v1",
    "build_auth_profile_entity_context_v1",
    "normalize_auth_profile_entity_scope_v1",
    "resolve_auth_profile_entity_scope_from_values_v1",
    "resolve_auth_profile_entity_scope_label_v1",
]
