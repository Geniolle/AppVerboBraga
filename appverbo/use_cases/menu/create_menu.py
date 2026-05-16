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
    ensure_menu_in_scope_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################


@dataclass(frozen=True)
class CreateMenuInput:
    menu_label: str
    menu_visibility_scope: str
    menu_section: str
    redirect_menu: str
    redirect_target: str
    subprocess_return_url: str


def normalize_create_menu_input_v1(
    *,
    menu_label: str,
    menu_visibility_scope: str = "all",
    menu_section: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-menu-card",
    subprocess_return_url: str = "",
) -> CreateMenuInput:
    return CreateMenuInput(
        menu_label=str(menu_label or "").strip(),
        menu_visibility_scope=str(menu_visibility_scope or "").strip().lower() or "all",
        menu_section=str(menu_section or "").strip().lower(),
        redirect_menu=str(redirect_menu or "administrativo").strip() or "administrativo",
        redirect_target=str(redirect_target or "#admin-menu-card").strip() or "#admin-menu-card",
        subprocess_return_url=str(subprocess_return_url or "").strip(),
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_create_menu_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: CreateMenuInput,
) -> MenuActionOutcome:
    repository = MenuAdminRepository(MENU_CONFIG)

    if payload.subprocess_return_url:
        return_url = sanitize_menu_return_url_v1(
            payload.subprocess_return_url,
            default_target="#admin-menu-card",
        )
    else:
        return_url = build_menu_settings_redirect_url_v1(
            redirect_menu=payload.redirect_menu,
            redirect_target=payload.redirect_target,
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

    ok, error_message, _ = repository.create_menu(
        session=session,
        menu_label=payload.menu_label,
        visibility_scope_mode=payload.menu_visibility_scope,
        menu_section=payload.menu_section,
    )

    if not ok:
        return build_menu_return_url_with_message_v1(
            return_url=return_url,
            message_key="error",
            message=error_message or "Não foi possível criar o menu.",
        )

    return build_menu_return_url_with_message_v1(
        return_url=return_url,
        message_key="success",
        message="Menu criado com sucesso.",
    )
