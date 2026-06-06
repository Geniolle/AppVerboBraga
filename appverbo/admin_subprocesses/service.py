
from __future__ import annotations

from typing import Any, Iterable

from .models import AdminSubprocessConfig, AdminSubprocessState


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
    edit_data: dict[str, Any] | None = None,
    create_data: dict[str, Any] | None = None,
    success: str = "",
    error: str = "",
    return_url: str = "",
    field_options: dict[str, tuple[tuple[str, str], ...]] | None = None,
) -> AdminSubprocessState:
    row_list = [dict(row) for row in rows]
    active_rows, inactive_rows = split_admin_subprocess_rows(row_list, config)
    resolved_edit_data = None

    if isinstance(edit_data, dict) and edit_data:
        resolved_edit_data = dict(edit_data)
    else:
        resolved_edit_data = find_admin_subprocess_row(row_list, config, edit_key)

    return AdminSubprocessState(
        config=config,
        mode="edit" if resolved_edit_data else "create",
        edit_key=edit_key,
        edit_data=resolved_edit_data,
        create_data=dict(create_data or {}),
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        success=success,
        error=error,
        return_url=return_url,
        field_options=dict(field_options or {}),
    )
