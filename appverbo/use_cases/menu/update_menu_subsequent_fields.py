from __future__ import annotations

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
    sanitize_menu_return_url_v1,
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
class UpdateMenuSubsequentFieldsInput:
    menu_key: str
    subsequent_fields: list[dict[str, str]]
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_update_menu_subsequent_fields_input_v1(
    *,
    menu_key: str,
    subsequent_field_key: list[str],
    subsequent_trigger_field: list[str],
    subsequent_field: list[str],
    subsequent_operator: list[str],
    subsequent_trigger_value: list[str],
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> UpdateMenuSubsequentFieldsInput:
    rows_count = max(
        len(subsequent_field_key or []),
        len(subsequent_trigger_field or []),
        len(subsequent_field or []),
        len(subsequent_operator or []),
        len(subsequent_trigger_value or []),
    )

    payload_fields: list[dict[str, str]] = []
    for row_index in range(rows_count):
        if row_index >= len(subsequent_trigger_field or []) or row_index >= len(subsequent_field or []):
            continue

        payload_fields.append(
            {
                "key": subsequent_field_key[row_index] if row_index < len(subsequent_field_key or []) else "",
                "trigger_field": subsequent_trigger_field[row_index] if row_index < len(subsequent_trigger_field or []) else "",
                "field_key": subsequent_field[row_index] if row_index < len(subsequent_field or []) else "",
                "operator": subsequent_operator[row_index] if row_index < len(subsequent_operator or []) else "",
                "trigger_value": subsequent_trigger_value[row_index] if row_index < len(subsequent_trigger_value or []) else "",
            }
        )

    return UpdateMenuSubsequentFieldsInput(
        menu_key=str(menu_key or "").strip().lower(),
        subsequent_fields=payload_fields,
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_subsequent_fields_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuSubsequentFieldsInput,
) -> MenuActionOutcome:
    repository = MenuAdminRepository(MENU_CONFIG)
    if payload.subprocess_return_url:
        return_url = sanitize_menu_return_url_v1(
            payload.subprocess_return_url,
            default_target=payload.redirect_target or "#settings-menu-edit-card",
        )
    else:
        return_url = build_menu_settings_redirect_url_v1(
            redirect_menu=payload.redirect_menu,
            redirect_target=payload.redirect_target,
            settings_edit_key=payload.menu_key,
            settings_action="edit",
            settings_tab="campos-subsequentes",
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
        selected_entity_id=selected_entity_id,
    )
    if policy_error:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=policy_error,
        )

    ok, error_message = repository.update_subsequent_fields(
        session=session,
        menu_key=payload.menu_key,
        raw_fields=payload.subsequent_fields,
        selected_entity_id=selected_entity_id,
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar os campos subsequentes.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Campos subsequentes atualizados com sucesso.",
    )
