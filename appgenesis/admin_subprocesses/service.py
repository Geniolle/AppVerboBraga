
from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .models import AdminFieldConfig, AdminSubprocessConfig, AdminSubprocessState


INACTIVE_STATUS_VALUES = {
    "inativo",
    "inactive",
    "0",
    "false",
    "no",
    "nao",
    "não",
    "off",
}

ADMIN_SUBPROCESS_ENTITY_CONTEXT_FIELD_KEY = "entity_number"
ADMIN_SUBPROCESS_ENTITY_CONTEXT_GRID_CLASS = "admin-subprocess-grid-entity-context-v1"


def normalize_admin_subprocess_text(value: object) -> str:
    return str(value or "").strip()


def normalize_admin_subprocess_key(value: object) -> str:
    return normalize_admin_subprocess_text(value).lower()


def normalize_admin_subprocess_status(row: dict[str, Any], config: AdminSubprocessConfig) -> str:
    raw_status = normalize_admin_subprocess_key(row.get(config.status_field))
    raw_is_active = row.get("is_active")

    if raw_is_active is False:
        return config.inactive_value

    if raw_status in INACTIVE_STATUS_VALUES:
        return config.inactive_value

    return config.active_value


def is_admin_subprocess_row_active(row: dict[str, Any], config: AdminSubprocessConfig) -> bool:
    return normalize_admin_subprocess_status(row, config) == config.active_value


def split_admin_subprocess_rows(
    rows: Iterable[dict[str, Any]],
    config: AdminSubprocessConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    inactive_rows: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)

        if is_admin_subprocess_row_active(row, config):
            active_rows.append(row)
        else:
            inactive_rows.append(row)

    return active_rows, inactive_rows


def find_admin_subprocess_row(
    rows: Iterable[dict[str, Any]],
    config: AdminSubprocessConfig,
    edit_key: str,
) -> dict[str, Any] | None:
    clean_edit_key = normalize_admin_subprocess_key(edit_key)

    if not clean_edit_key:
        return None

    for raw_row in rows:
        row = dict(raw_row)
        current_key = normalize_admin_subprocess_key(row.get(config.identity_field))

        if current_key == clean_edit_key:
            return row

    return None


# ###################################################################################
# (2) CAMPOS E CONFIGURACAO DE CONTEXTO DE ENTIDADE
# ###################################################################################


def _normalize_admin_subprocess_entity_number(entity_context: dict[str, Any] | None) -> str:
    safe_context = entity_context or {}
    for raw_key in ("selected_entity_number", "entity_number", "current_entity_number"):
        clean_value = str(safe_context.get(raw_key) or "").strip()
        if clean_value:
            return clean_value
    return ""


def _status_option_label(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"active", "ativo"}:
        return "Ativo"
    if clean_value in {"inactive", "inativo"}:
        return "Inativo"
    if not clean_value:
        return ""
    return clean_value.replace("_", " ").title()


def _build_admin_subprocess_status_field_v1(config: AdminSubprocessConfig) -> AdminFieldConfig:
    return AdminFieldConfig(
        key=config.status_field,
        label="Estado",
        input_name=config.status_field,
        field_type="select",
        required=True,
        options=(
            (config.active_value, _status_option_label(config.active_value)),
            (config.inactive_value, _status_option_label(config.inactive_value)),
        ),
    )


def _build_admin_subprocess_entity_field_v1(
    config: AdminSubprocessConfig,
    *,
    entity_number_display: str,
) -> AdminFieldConfig:
    return AdminFieldConfig(
        key=ADMIN_SUBPROCESS_ENTITY_CONTEXT_FIELD_KEY,
        label="Entidade",
        input_name=f"{config.key}_entity_number_display",
        field_type="readonly",
        required=False,
        default_value=entity_number_display,
    )


def build_admin_subprocess_config_for_entity_context_v1(
    config: AdminSubprocessConfig,
    entity_context: dict[str, Any] | None = None,
) -> AdminSubprocessConfig:
    if not config.uses_entity_context:
        return config

    entity_number_display = _normalize_admin_subprocess_entity_number(entity_context)
    status_field_key = str(config.status_field or "").strip().lower()

    other_fields: list[AdminFieldConfig] = []
    status_field: AdminFieldConfig | None = None
    entity_field: AdminFieldConfig | None = None
    seen_keys: set[str] = set()

    for field in config.fields:
        field_key = str(field.key or "").strip().lower()
        if not field_key or field_key in seen_keys:
            continue

        if field_key == status_field_key:
            status_field = field
            seen_keys.add(field_key)
            continue

        if field_key == ADMIN_SUBPROCESS_ENTITY_CONTEXT_FIELD_KEY:
            entity_field = replace(
                field,
                label="Entidade",
                input_name=f"{config.key}_entity_number_display",
                field_type="readonly",
                required=False,
                default_value=entity_number_display,
            )
            seen_keys.add(field_key)
            continue

        other_fields.append(field)
        seen_keys.add(field_key)

    if status_field is None:
        status_field = _build_admin_subprocess_status_field_v1(config)
    else:
        status_field = replace(status_field)

    if entity_field is None:
        entity_field = _build_admin_subprocess_entity_field_v1(
            config,
            entity_number_display=entity_number_display,
        )

    adjusted_fields = tuple([*other_fields, status_field, entity_field])
    updated_grid_class = config.form_grid_css_class or ADMIN_SUBPROCESS_ENTITY_CONTEXT_GRID_CLASS

    return replace(
        config,
        fields=adjusted_fields,
        form_grid_css_class=updated_grid_class,
    )


def build_admin_subprocess_state(
    *,
    config: AdminSubprocessConfig,
    rows: Iterable[dict[str, Any]],
    edit_key: str = "",
    success: str = "",
    error: str = "",
    menu_key: str = "administrativo",
    menu_scope: str = "",
    return_url: str = "",
    sidebar_menu_settings: list[dict[str, Any]] | None = None,
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None = None,
    active_entity_id: int | None = None,
    entity_context: dict[str, Any] | None = None,
) -> AdminSubprocessState:
    row_list = [dict(row) for row in rows]
    active_rows, inactive_rows = split_admin_subprocess_rows(row_list, config)
    edit_data = find_admin_subprocess_row(row_list, config, edit_key)
    effective_menu_scope = menu_scope or config.menu_scope or "administrativo"
    config_for_context = build_admin_subprocess_config_for_entity_context_v1(config, entity_context)
    edit_values: dict[str, Any] = {}

    if edit_data:
        raw_values = edit_data.get("values")
        if isinstance(raw_values, dict):
            edit_values = dict(raw_values)
        normalized_edit_values = edit_data.get("edit_values")
        if isinstance(normalized_edit_values, dict):
            edit_values.update(normalized_edit_values)

    resolved_dynamic_fields: list[dict[str, Any]] = []
    if config_for_context.uses_dynamic_fields and sidebar_menu_settings is not None:
        from appgenesis.services.process_tabs import resolve_subprocess_section_fields_v1
        resolved_dynamic_fields = resolve_subprocess_section_fields_v1(
            config_for_context.dynamic_fields_menu_key,
            config_for_context.dynamic_fields_section_header_key,
            sidebar_menu_settings,
            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
            menu_process_history_map=menu_process_history_map,
            active_entity_id=active_entity_id,
            current_field_values=edit_values,
        )

    return AdminSubprocessState(
        config=config_for_context,
        mode="edit" if edit_data else "create",
        edit_key=edit_key,
        edit_data=edit_data,
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        success=success,
        error=error,
        menu_key=menu_key,
        menu_scope=effective_menu_scope,
        return_url=return_url,
        resolved_dynamic_fields=resolved_dynamic_fields,
        edit_values=edit_values,
    )
