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
from appverbo.use_cases.menu.update_menu_visibility import (
    execute_update_menu_visibility_v1,
    normalize_update_menu_visibility_input_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################


@dataclass(frozen=True)
class UpdateMenuInput:
    menu_key: str
    menu_label: str
    menu_status: str
    menu_visibility_scope: str
    menu_sidebar_section: str
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_update_menu_input_v1(
    *,
    menu_key: str,
    menu_label: str,
    menu_status: str = "ativo",
    menu_visibility_scope: str = "all",
    menu_sidebar_section: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#settings-menu-edit-card",
    subprocess_return_url: str = "",
) -> UpdateMenuInput:
    return UpdateMenuInput(
        menu_key=str(menu_key or "").strip().lower(),
        menu_label=str(menu_label or "").strip(),
        menu_status=str(menu_status or "").strip().lower() or "ativo",
        menu_visibility_scope=str(menu_visibility_scope or "").strip().lower() or "all",
        menu_sidebar_section=str(menu_sidebar_section or "").strip().lower(),
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#settings-menu-edit-card").strip() or "#settings-menu-edit-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: UpdateMenuInput,
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
            settings_tab="geral",
        )

    policy_error = ensure_actor_can_manage_menu_v1(
        session=session,
        actor_user=actor_user,
    )
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

    ok, error_message = repository.update_menu_label(
        session=session,
        menu_key=payload.menu_key,
        menu_label=payload.menu_label,
        visibility_scope_mode=payload.menu_visibility_scope,
        menu_sidebar_section=payload.menu_sidebar_section,
        selected_entity_id=selected_entity_id,
    )

    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível atualizar o menu.",
        )

    visibility_ok, visibility_error = execute_update_menu_visibility_v1(
        session=session,
        payload=normalize_update_menu_visibility_input_v1(
            menu_key=payload.menu_key,
            menu_status=payload.menu_status,
        ),
    )

    if not visibility_ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=visibility_error,
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Menu atualizado com sucesso.",
    )
