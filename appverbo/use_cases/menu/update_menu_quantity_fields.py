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
class UpdateMenuQuantityFieldsInput:
    menu_key: str
    quantity_rules: list[dict[str, str]]
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_update_menu_quantity_fields_input_v1(
    *,
    menu_key: str,
    quantity_rule_key: list[str],
    quantity_rule_label: list[str],
    quantity_field_key: list[str],
    quantity_repeated_field_keys_json: list[str],
    quantity_header_key: list[str],
    quantity_max_items: list[str],
    quantity_item_label: list[str],
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> UpdateMenuQuantityFieldsInput:
    rows_count = max(
        len(quantity_rule_key or []),
        len(quantity_rule_label or []),
        len(quantity_field_key or []),
        len(quantity_repeated_field_keys_json or []),
        len(quantity_header_key or []),
        len(quantity_max_items or []),
        len(quantity_item_label or []),
    )

    payload_rules: list[dict[str, str]] = []
    for row_index in range(rows_count):
        payload_rules.append(
            {
                "key": quantity_rule_key[row_index] if row_index < len(quantity_rule_key or []) else "",
                "label": quantity_rule_label[row_index] if row_index < len(quantity_rule_label or []) else "",
                "quantity_field_key": quantity_field_key[row_index] if row_index < len(quantity_field_key or []) else "",
                "repeated_field_keys": quantity_repeated_field_keys_json[row_index] if row_index < len(quantity_repeated_field_keys_json or []) else "",
                "header_key": quantity_header_key[row_index] if row_index < len(quantity_header_key or []) else "",
                "max_items": quantity_max_items[row_index] if row_index < len(quantity_max_items or []) else "",
                "item_label": quantity_item_label[row_index] if row_index < len(quantity_item_label or []) else "",
            }
        )

    return UpdateMenuQuantityFieldsInput(
        menu_key=str(menu_key or "").strip().lower(),
        quantity_rules=payload_rules,
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_quantity_fields_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuQuantityFieldsInput,
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
            settings_tab="campos-quantidade",
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

    ok, error_message = repository.update_quantity_fields(
        session=session,
        menu_key=payload.menu_key,
        raw_fields=payload.quantity_rules,
        selected_entity_id=selected_entity_id,
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar os campos de quantidade.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Campos de quantidade atualizados com sucesso.",
    )
