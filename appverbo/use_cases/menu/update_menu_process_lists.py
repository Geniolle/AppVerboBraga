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
class UpdateMenuProcessListsInput:
    menu_key: str
    process_lists: list[dict[str, str]]
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_update_menu_process_lists_input_v1(
    *,
    menu_key: str,
    process_list_key: list[str],
    process_list_label: list[str],
    process_list_items_csv: list[str],
    process_list_source: list[str],
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> UpdateMenuProcessListsInput:
    rows_count = max(
        len(process_list_key or []),
        len(process_list_label or []),
        len(process_list_items_csv or []),
        len(process_list_source or []),
    )

    payload_lists: list[dict[str, str]] = []
    for row_index in range(rows_count):
        label = process_list_label[row_index] if row_index < len(process_list_label or []) else ""
        items_csv = process_list_items_csv[row_index] if row_index < len(process_list_items_csv or []) else ""
        source_key = process_list_source[row_index] if row_index < len(process_list_source or []) else ""

        if not str(label or "").strip() and not str(items_csv or "").strip():
            continue

        payload_lists.append(
            {
                "key": process_list_key[row_index] if row_index < len(process_list_key or []) else "",
                "label": label,
                "items_csv": items_csv,
                "source_key": source_key,
            }
        )

    return UpdateMenuProcessListsInput(
        menu_key=str(menu_key or "").strip().lower(),
        process_lists=payload_lists,
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_process_lists_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuProcessListsInput,
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
            settings_tab="lista",
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

    ok, error_message = repository.update_process_lists(
        session=session,
        menu_key=payload.menu_key,
        raw_lists=payload.process_lists,
        selected_entity_id=selected_entity_id,
    )
    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar as listas do processo.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Listas do processo atualizadas com sucesso.",
    )
