from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import status
from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
    SidebarSectionAdminRepository,
)
from appverbo.admin_subprocesses.sessoes.common import build_sessoes_admin_return_url_v2
from appverbo.admin_subprocesses.sessoes.configuracao import SESSOES_CONFIG
from appverbo.services.entity_scope import load_entity_profile_scope_v1
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.sessoes.outcome import SessionActionOutcome
from appverbo.use_cases.sessoes.policies import (
    ensure_actor_can_manage_sessions_v1,
    ensure_actor_is_owner_for_sessions_v1,
    ensure_session_in_scope_v1,
    ensure_session_row_action_allowed_v1,
)


SESSION_RETURN_URL_FALLBACK_V1 = (
    build_sessoes_admin_return_url_v2(
        admin_tab="sessoes",
        target="admin-sidebar-sections-card",
    )
)


# ###################################################################################
# (1) NORMALIZADORES DE PAYLOAD
# ###################################################################################

def _build_settings_redirect_url_v1(
    *,
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
) -> str:
    params: list[tuple[str, str]] = []

    if error_message:
        params.append(("settings_error", error_message))

    if success_message:
        params.append(("settings_success", success_message))

    if redirect_menu:
        params.append(("menu", redirect_menu))

    if redirect_target:
        params.append(("target", redirect_target.lstrip("#")))

    if settings_edit_key:
        params.append(("settings_edit_key", settings_edit_key))

    if settings_action:
        params.append(("settings_action", settings_action))

    if settings_tab:
        params.append(("settings_tab", settings_tab))

    return f"/users/new?{urlencode(params)}"


def normalize_save_session_input_v1(
    *,
    section_mode: str,
    original_section_key: str,
    section_label: str,
    section_visibility_scope_mode: str,
    section_status: str,
    section_status_override: str,
    sidebar_section_return_url: str,
) -> dict[str, str]:
    return {
        "section_mode": str(section_mode or "").strip().lower() or "create",
        "original_section_key": str(original_section_key or "").strip(),
        "section_label": str(section_label or "").strip(),
        "section_visibility_scope_mode": str(section_visibility_scope_mode or "").strip(),
        "section_status": str(section_status_override or section_status or "").strip(),
        "sidebar_section_return_url": str(sidebar_section_return_url or "").strip(),
    }


def normalize_bulk_sessions_input_v1(
    *,
    section_key: list[str],
    section_label: list[str],
    section_visibility_scope_mode: list[str],
    section_status: list[str],
) -> list[dict[str, str]]:
    rows_count = max(
        len(section_key),
        len(section_label),
        len(section_visibility_scope_mode),
        len(section_status),
    )
    payload_rows: list[dict[str, str]] = []

    for row_index in range(rows_count):
        payload_rows.append(
            {
                "key": section_key[row_index] if row_index < len(section_key) else "",
                "label": section_label[row_index] if row_index < len(section_label) else "",
                "visibility_scope_mode": (
                    section_visibility_scope_mode[row_index]
                    if row_index < len(section_visibility_scope_mode)
                    else ""
                ),
                "status": (
                    section_status[row_index]
                    if row_index < len(section_status)
                    else "ativo"
                ),
            }
        )

    return payload_rows


# ###################################################################################
# (2) URLS DE RETORNO E MENSAGENS
# ###################################################################################

def sanitize_sidebar_section_return_url_v1(return_url: object) -> str:
    raw_url = str(return_url or "").strip() or SESSION_RETURN_URL_FALLBACK_V1

    if raw_url.startswith(("http://", "https://", "//")):
        raw_url = SESSION_RETURN_URL_FALLBACK_V1

    if not raw_url.startswith("/users/new"):
        raw_url = SESSION_RETURN_URL_FALLBACK_V1

    parts = urlsplit(raw_url)
    blocked_params = {
        "settings_edit_key",
        "settings_action",
        "settings_tab",
        "sidebar_section_edit_key",
        "sidebar_section_return_url",
        "dynamic_process_section",
        "appverbo_after_save",
        "success",
        "error",
    }

    clean_params: list[tuple[str, str]] = []
    found_menu = False
    found_admin_tab = False
    found_sidebar_tab = False
    found_target = False
    session_target_keys = {
        "admin-sidebar-sections-card",
        "admin-sidebar-sections-form-card",
        "admin-sidebar-sections-card-create",
        "admin-sidebar-sections-card-inactive",
    }
    target_value = "admin-sidebar-sections-card"

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in blocked_params:
            continue

        if key == "menu":
            found_menu = True
            clean_params.append(("menu", "sessoes"))
            continue

        if key == "admin_tab":
            found_admin_tab = True
            clean_params.append(("admin_tab", "sessoes"))
            continue

        if key == "sidebar_sections_tab":
            found_sidebar_tab = True
            clean_params.append(("sidebar_sections_tab", "sessoes"))
            continue

        if key == "target":
            found_target = True
            clean_target_value = str(value or "").strip().lstrip("#")
            if clean_target_value in session_target_keys:
                target_value = clean_target_value
            clean_params.append(("target", target_value))
            continue

        clean_params.append((key, value))

    if not found_menu:
        clean_params.append(("menu", "sessoes"))

    if not found_admin_tab:
        clean_params.append(("admin_tab", "sessoes"))

    if not found_sidebar_tab:
        clean_params.append(("sidebar_sections_tab", "sessoes"))

    if not found_target:
        clean_params.append(("target", target_value))

    clean_fragment = str(parts.fragment or "").strip().lstrip("#")
    if clean_fragment not in session_target_keys:
        clean_fragment = target_value

    return urlunsplit(
        (
            "",
            "",
            "/users/new",
            urlencode(clean_params),
            clean_fragment,
        )
    )


def append_sidebar_section_message_v1(
    return_url: str,
    message_key: str,
    message: str,
) -> str:
    parts = urlsplit(return_url)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error", "settings_success", "settings_error"}
    ]

    clean_message_key = (
        "settings_success"
        if message_key == "success"
        else "settings_error"
        if message_key == "error"
        else message_key
    )
    params.append((clean_message_key, message))

    return urlunsplit(
        (
            "",
            "",
            parts.path or "/users/new",
            urlencode(params),
            parts.fragment or "admin-sidebar-sections-card",
        )
    )


def build_sidebar_section_redirect_v1(
    *,
    return_url: str,
    message_key: str,
    message: str,
) -> SessionActionOutcome:
    safe_return_url = sanitize_sidebar_section_return_url_v1(return_url)

    return SessionActionOutcome(
        redirect_url=append_sidebar_section_message_v1(
            safe_return_url,
            message_key,
            message,
        ),
        redirect_status_code=status.HTTP_303_SEE_OTHER,
    )


# ###################################################################################
# (3) USE CASE DE CRIAR/EDITAR SESSAO
# ###################################################################################

def execute_save_session_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: dict[str, str],
) -> SessionActionOutcome:
    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    safe_return_url = sanitize_sidebar_section_return_url_v1(
        payload.get("sidebar_section_return_url", "")
    )

    policy_error = ensure_actor_can_manage_sessions_v1(
        session=session,
        actor_user=actor_user,
    )

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"] or ""),
        selected_entity_id,
    )
    resolved_selected_entity_id = permissions.get("selected_entity_id")
    current_entity_scope = load_entity_profile_scope_v1(
        session,
        resolved_selected_entity_id,
    )

    if not current_entity_scope and permissions.get("can_manage_all_entities"):
        current_entity_scope = "owner"

    policy_error = ensure_session_in_scope_v1(
        permissions=permissions,
        selected_entity_id=resolved_selected_entity_id,
        current_entity_scope=current_entity_scope,
    )

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    if payload.get("section_mode", "create") == "edit":
        policy_error = ensure_session_row_action_allowed_v1(
            repository=repository,
            session=session,
            section_key=payload.get("original_section_key", ""),
            action="edit",
            selected_entity_id=resolved_selected_entity_id,
            current_entity_scope=current_entity_scope,
        )

        if policy_error:
            return build_sidebar_section_redirect_v1(
                return_url=safe_return_url,
                message_key="error",
                message=policy_error,
            )

    ok, error_message, _ = repository.save_session(
        session=session,
        mode=payload.get("section_mode", "create"),
        original_section_key=payload.get("original_section_key", ""),
        section_label=payload.get("section_label", ""),
        section_visibility_scope_mode=payload.get("section_visibility_scope_mode", "all"),
        section_status=payload.get("section_status", "ativo"),
        selected_entity_id=resolved_selected_entity_id,
        current_entity_scope=current_entity_scope,
    )

    if not ok:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=error_message or "Não foi possível gravar a sessão.",
        )

    success_message = (
        "Sessão atualizada com sucesso."
        if payload.get("section_mode", "create") == "edit"
        else "Sessão criada com sucesso."
    )

    return build_sidebar_section_redirect_v1(
        return_url=safe_return_url,
        message_key="success",
        message=success_message,
    )


# ###################################################################################
# (4) USE CASE DE COMPATIBILIDADE LEGADA
# ###################################################################################

def execute_bulk_save_sessions_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    redirect_menu: str,
    redirect_target: str,
    payload_sections: list[dict[str, str]],
) -> SessionActionOutcome:
    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)

    policy_error = ensure_actor_can_manage_sessions_v1(
        session=session,
        actor_user=actor_user,
    )

    if policy_error:
        return SessionActionOutcome(
            redirect_url=_build_settings_redirect_url_v1(
                error_message=policy_error,
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            redirect_status_code=status.HTTP_303_SEE_OTHER,
        )

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"] or ""),
        selected_entity_id,
    )

    policy_error = ensure_actor_is_owner_for_sessions_v1(permissions=permissions)

    if policy_error:
        return SessionActionOutcome(
            redirect_url=_build_settings_redirect_url_v1(
                error_message=policy_error,
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            redirect_status_code=status.HTTP_303_SEE_OTHER,
        )

    ok, error_message, _ = repository.persist_sidebar_sections(
        session=session,
        sections=payload_sections,
    )

    if not ok:
        return SessionActionOutcome(
            redirect_url=_build_settings_redirect_url_v1(
                error_message=error_message or "Não foi possível gravar as sessões do sidebar.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            redirect_status_code=status.HTTP_303_SEE_OTHER,
        )

    return SessionActionOutcome(
        redirect_url=_build_settings_redirect_url_v1(
            success_message="Sessões do sidebar e visibilidade dos menus atualizadas com sucesso.",
            redirect_menu=redirect_menu,
            redirect_target=redirect_target,
            settings_edit_key="administrativo",
            settings_action="edit",
            settings_tab="sessoes",
        ),
        redirect_status_code=status.HTTP_303_SEE_OTHER,
    )
