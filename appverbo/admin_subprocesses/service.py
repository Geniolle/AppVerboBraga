
from __future__ import annotations

from typing import Any, Iterable

from .models import AdminSubprocessConfig, AdminSubprocessState
from appverbo.services.process_tabs import resolve_subprocess_section_fields_v1


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
) -> AdminSubprocessState:
    row_list = [dict(row) for row in rows]
    active_rows, inactive_rows = split_admin_subprocess_rows(row_list, config)
    edit_data = find_admin_subprocess_row(row_list, config, edit_key)
    effective_menu_scope = menu_scope or config.menu_scope or "administrativo"

    resolved_dynamic_fields: list[dict[str, Any]] = []
    if config.uses_dynamic_fields and sidebar_menu_settings is not None:
        resolved_dynamic_fields = resolve_subprocess_section_fields_v1(
            config.dynamic_fields_menu_key,
            config.dynamic_fields_section_header_key,
            sidebar_menu_settings,
        )

    edit_values: dict[str, Any] = {}
    if edit_data and resolved_dynamic_fields:
        raw_values = edit_data.get("values")
        if isinstance(raw_values, dict):
            edit_values = dict(raw_values)

    return AdminSubprocessState(
        config=config,
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
