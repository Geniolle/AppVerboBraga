from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.menu.outcome import (
    MenuActionOutcome,
    build_menu_return_url_with_message_v1,
    build_menu_settings_redirect_url_v1,
)
from appverbo.use_cases.menu.policies import (
    ensure_actor_can_manage_menu_v1,
    ensure_actor_is_owner_for_menu_v1,
    ensure_menu_exists_v1,
    ensure_menu_in_scope_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################


@dataclass(frozen=True)
class UpdateMenuProcessFieldsInput:
    menu_key: str
    visible_fields: list[str]
    visible_headers: list[str]
    redirect_menu: str
    redirect_target: str


def normalize_update_menu_process_fields_input_v1(
    *,
    menu_key: str,
    visible_fields: list[str],
    visible_headers: list[str],
    visible_rows_json: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
) -> UpdateMenuProcessFieldsInput:
    clean_menu_key = str(menu_key or "").strip().lower()

    normalized_visible_fields: list[str] = []
    normalized_visible_headers: list[str] = []
    seen_fields: set[str] = set()

    parsed_visible_rows: list[dict[str, Any]] = []
    clean_rows_json = str(visible_rows_json or "").strip()

    if clean_rows_json:
        try:
            raw_rows = json.loads(clean_rows_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            raw_rows = []

        if isinstance(raw_rows, list):
            parsed_visible_rows = [row for row in raw_rows if isinstance(row, dict)]

    for raw_row in parsed_visible_rows:
        field_key = str(
            raw_row.get("field_key")
            or raw_row.get("fieldKey")
            or raw_row.get("key")
            or ""
        ).strip().lower()
        header_key = str(
            raw_row.get("header_key")
            or raw_row.get("headerKey")
            or raw_row.get("header")
            or ""
        ).strip().lower()

        if not field_key or field_key in seen_fields:
            continue

        seen_fields.add(field_key)
        normalized_visible_fields.append(field_key)
        normalized_visible_headers.append(header_key)

    if not normalized_visible_fields:
        for row_index, raw_field in enumerate(list(visible_fields or [])):
            field_key = str(raw_field or "").strip().lower()

            if not field_key or field_key in seen_fields:
                continue

            header_key = ""
            if row_index < len(visible_headers or []):
                header_key = str((visible_headers or [])[row_index] or "").strip().lower()

            seen_fields.add(field_key)
            normalized_visible_fields.append(field_key)
            normalized_visible_headers.append(header_key)

    return UpdateMenuProcessFieldsInput(
        menu_key=clean_menu_key,
        visible_fields=normalized_visible_fields,
        visible_headers=normalized_visible_headers,
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_process_fields_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuProcessFieldsInput,
) -> MenuActionOutcome:
    repository = MenuAdminRepository(MENU_CONFIG)
    return_url = build_menu_settings_redirect_url_v1(
        redirect_menu=payload.redirect_menu,
        redirect_target=payload.redirect_target,
        settings_edit_key=payload.menu_key,
        settings_action="edit",
        settings_tab="campos-config",
    )

    policy_error = ensure_actor_can_manage_menu_v1(session=session, actor_user=actor_user)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        )

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"] or ""),
        selected_entity_id,
    )
    policy_error = ensure_actor_is_owner_for_menu_v1(permissions=permissions)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        )

    policy_error = ensure_menu_in_scope_v1(permissions=permissions)
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        )

    policy_error = ensure_menu_exists_v1(
        repository=repository,
        session=session,
        menu_key=payload.menu_key,
    )
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        )

    ok, error_message = repository.update_process_fields(
        session=session,
        menu_key=payload.menu_key,
        visible_fields=payload.visible_fields,
        visible_headers=payload.visible_headers,
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar os campos do processo.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Configuração dos campos atualizada com sucesso.",
    )
