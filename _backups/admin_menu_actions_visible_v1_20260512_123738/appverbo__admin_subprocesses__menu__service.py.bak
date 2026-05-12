from __future__ import annotations

from typing import Any, Iterable

from appverbo.admin_subprocesses.menu.state import AdminMenuState


# ###################################################################################
# (1) NORMALIZACAO E SEPARACAO DO SUBPROCESSO MENU
# ###################################################################################


INACTIVE_MENU_STATUS_VALUES = {
    "inativo",
    "inactive",
    "0",
    "false",
    "no",
    "nao",
    "não",
    "off",
}


def normalize_admin_menu_text(value: object) -> str:
    return str(value or "").strip()


def normalize_admin_menu_key(value: object) -> str:
    return normalize_admin_menu_text(value).lower()


def normalize_admin_menu_status(row: dict[str, Any]) -> str:
    raw_status = normalize_admin_menu_key(row.get("status"))
    raw_is_active = row.get("is_active")

    if raw_is_active is False or raw_status in INACTIVE_MENU_STATUS_VALUES:
        return "inativo"

    return "ativo"


def split_admin_menu_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active_rows: list[dict[str, Any]] = []
    inactive_rows: list[dict[str, Any]] = []

    for raw_row in rows:
        row = dict(raw_row)
        normalized_status = normalize_admin_menu_status(row)
        row["status"] = normalized_status
        row["status_label"] = "Ativo" if normalized_status == "ativo" else "Inativo"

        if normalized_status == "ativo":
            active_rows.append(row)
        else:
            inactive_rows.append(row)

    return active_rows, inactive_rows


# ###################################################################################
# (2) CONSTRUCAO DO ESTADO DE VIEW DO MENU
# ###################################################################################


def build_admin_menu_state(
    *,
    rows: Iterable[dict[str, Any]],
    section_options: Iterable[tuple[str, str]] = (),
    can_manage_all_entities: bool = False,
    success: str = "",
    error: str = "",
    return_url: str = "/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card",
) -> AdminMenuState:
    active_rows, inactive_rows = split_admin_menu_rows(rows)

    normalized_section_options = tuple(
        (
            normalize_admin_menu_key(option_value),
            normalize_admin_menu_text(option_label),
        )
        for option_value, option_label in section_options
        if normalize_admin_menu_key(option_value) and normalize_admin_menu_text(option_label)
    )

    return AdminMenuState(
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        section_options=normalized_section_options,
        can_manage_all_entities=bool(can_manage_all_entities),
        success=normalize_admin_menu_text(success),
        error=normalize_admin_menu_text(error),
        return_url=normalize_admin_menu_text(return_url) or return_url,
    )
