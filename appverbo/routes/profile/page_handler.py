from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_START
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config, ENTIDADE_CONFIG, UTILIZADOR_CONFIG
from appverbo.admin_subprocesses.repositories.auth_profile_repository import AuthorizationProfileAdminRepository
from appverbo.admin_subprocesses.repositories.objeto_autorizacao_repository import ObjetoAutorizacaoAdminRepository
from appverbo.admin_subprocesses.service import build_admin_subprocess_state
from appverbo.admin_subprocesses.models import AdminSubprocessState
from appverbo.services.process_tabs import resolve_process_tabs_v1
# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_END
from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    MENU_MEU_PERFIL_KEY,
    normalize_sidebar_sections,
    delete_sidebar_menu_setting,
    get_sidebar_menu_settings,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_additional_fields,
    update_sidebar_menu_label,
    update_sidebar_menu_process_fields,
)
from appverbo.services import *  # noqa: F403,F401
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)

from appverbo.routes.profile.router import router

# APPVERBO_DEBUG_SESSOES_FLOW_V1_START
import logging as _logging_page
import os as _os_page

_SESSOES_PAGE_LOGGER = _logging_page.getLogger(__name__)


def _debug_sessoes_page_enabled_v1(request=None) -> bool:
    if _os_page.environ.get("APPVERBO_DEBUG_SESSOES_FLOW") == "1":
        return True
    if request is not None:
        try:
            if dict(request.query_params).get("debug_sessoes") == "1":
                return True
        except Exception:
            pass
    return False


def _log_sessoes_page_v1(event: str, **payload) -> None:
    parts = " | ".join(f"{k}={v!r}" for k, v in payload.items())
    _SESSOES_PAGE_LOGGER.info("[SESSOES_FLOW] %s | %s", event, parts)

# APPVERBO_DEBUG_SESSOES_FLOW_V1_END


ESTRUTURAS_MENU_KEY_V1 = "sessoes"
ESTRUTURAS_MENU_TARGETS_V1 = {
    "#admin-account-create-card",
    "#admin-account-status-card",
    "#settings-card",
    "#settings-menu-edit-card",
    "#menu-subprocess-card",
    "#menu-subprocess-card-active",
    "#menu-subprocess-card-inactive",
}
ESTRUTURAS_SESSOES_TARGETS_V1 = {
    "#admin-sidebar-sections-card",
    "#admin-sidebar-sections-form-card",
}


def _normalize_card_target_v1(raw_target: str) -> str:
    clean_target = str(raw_target or "").strip()
    if not clean_target:
        return ""
    return clean_target if clean_target.startswith("#") else f"#{clean_target.lstrip('#')}"


def _normalize_authorization_profile_target_v1(raw_target: str) -> str:
    clean_target = _normalize_card_target_v1(raw_target).lower()
    if not clean_target:
        return ""

    target_alias_map = {
        "#auth-profile": "#auth-profile-card",
        "#auth-profile-card": "#auth-profile-card",
        "#auth-profile-active-card": "#auth-profile-card",
        "#auth-profile-inactive-card": "#auth-profile-card",
        "#auth-profile-form-card": "#auth-profile-card",
        "#auth-objeto": "#auth-objeto-card",
        "#auth-objeto-card": "#auth-objeto-card",
        "#auth-objeto-active-card": "#auth-objeto-card",
        "#auth-objeto-inactive-card": "#auth-objeto-card",
        "#auth-objeto-form-card": "#auth-objeto-card",
    }
    return target_alias_map.get(clean_target, "")


def _normalize_tab_target_for_match_v1(raw_target: str, *, menu_key: str = "") -> str:
    clean_target = _normalize_card_target_v1(raw_target).lower()
    if not clean_target:
        return ""

    if resolve_menu_key_alias(menu_key) == "perfil_de_autorizacao":
        normalized_auth_target = _normalize_authorization_profile_target_v1(clean_target)
        if normalized_auth_target:
            return normalized_auth_target

    if clean_target.endswith("-active"):
        return clean_target[:-7]
    if clean_target.endswith("-inactive"):
        return clean_target[:-9]
    if clean_target.endswith("-form-card"):
        return f"{clean_target[:-10]}-card"
    return clean_target


def _targets_match_for_menu_v1(menu_key: str, left_target: str, right_target: str) -> bool:
    return _normalize_tab_target_for_match_v1(
        left_target,
        menu_key=menu_key,
    ) == _normalize_tab_target_for_match_v1(
        right_target,
        menu_key=menu_key,
    )


def _resolve_active_tab_index_v1(
    *,
    menu_key: str,
    initial_menu_tabs: list[dict[str, Any]],
    initial_menu_target: str,
    initial_dynamic_process_section: str = "",
) -> int:
    if not initial_menu_tabs:
        return 0

    for idx, tab in enumerate(initial_menu_tabs):
        tab_section = str(tab.get("dynamic_process_section", "") or "")
        if _targets_match_for_menu_v1(menu_key, tab.get("target", ""), initial_menu_target):
            if not tab_section or tab_section == initial_dynamic_process_section:
                return idx

    if initial_dynamic_process_section:
        for idx, tab in enumerate(initial_menu_tabs):
            tab_section = str(tab.get("dynamic_process_section", "") or "")
            if tab_section == initial_dynamic_process_section:
                return idx

    return 0


def _resolve_estruturas_navigation_context_v1(
    *,
    resolved_menu: str,
    resolved_admin_tab: str,
    settings_edit_key: str,
    target: str,
    sidebar_section_edit_key: str,
) -> tuple[str, str]:
    clean_menu = resolve_menu_key_alias(resolved_menu)
    clean_admin_tab = str(resolved_admin_tab or "").strip().lower()
    if clean_admin_tab in {"menu", "definicoes"}:
        clean_admin_tab = "contas"

    clean_target = _normalize_card_target_v1(target)
    is_sessoes_context = (
        bool(str(sidebar_section_edit_key or "").strip())
        or clean_admin_tab == "sessoes"
        or clean_target in ESTRUTURAS_SESSOES_TARGETS_V1
    )
    is_menu_context = (
        bool(str(settings_edit_key or "").strip())
        or clean_admin_tab == "contas"
        or clean_target in ESTRUTURAS_MENU_TARGETS_V1
    )

    if clean_menu == ESTRUTURAS_MENU_KEY_V1:
        return clean_menu, "contas" if is_menu_context else "sessoes"

    if clean_menu == "administrativo" and (is_sessoes_context or is_menu_context):
        return ESTRUTURAS_MENU_KEY_V1, "sessoes" if is_sessoes_context else "contas"

    return clean_menu, clean_admin_tab


def _resolve_first_dynamic_section_key(menu_row: dict[str, Any] | None) -> str:
    if not isinstance(menu_row, dict):
        return "__empty__"
    raw_rows = menu_row.get("process_visible_field_rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return "__empty__"

    section_order: list[str] = []
    seen_sections: set[str] = set()
    first_field_key = ""
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        if not field_key:
            continue
        if not first_field_key:
            first_field_key = field_key
        header_key = str(raw_row.get("header_key") or "").strip().lower()
        section_key = header_key or "__geral__"
        if section_key in seen_sections:
            continue
        seen_sections.add(section_key)
        section_order.append(section_key)

    if not section_order:
        return "__empty__"
    if len(section_order) == 1 and section_order[0] == "__geral__":
        return f"field:{first_field_key}" if first_field_key else "__empty__"
    return section_order[0]


def _resolve_initial_menu_target(
    resolved_menu: str,
    resolved_profile_tab: str,
    resolved_admin_tab: str,
    settings_edit_key: str,
    can_manage_tenant_structure: bool,
    sidebar_menu_settings: list[dict[str, Any]],
    query_edit_params: dict[str, str] | None = None,
) -> tuple[str, str]:
    clean_menu_key = resolve_menu_key_alias(resolved_menu)
    clean_query_edit_params = query_edit_params or {}
    settings_by_key = {
        str(raw_row.get("key") or "").strip().lower(): raw_row
        for raw_row in sidebar_menu_settings
        if isinstance(raw_row, dict) and str(raw_row.get("key") or "").strip()
    }

    if clean_menu_key == "empresa":
        return "#empresa-card", ""
    if clean_menu_key == "home":
        return "#home-summary-card", ""
    if clean_menu_key == "perfil":
        if resolved_profile_tab == "morada":
            return "#perfil-morada-card", ""
        if resolved_profile_tab == "treinamento":
            return "#dados-treinamento-card", ""
        return "#perfil-pessoal-card", ""
    if clean_menu_key == "administrativo":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "contas":
            return "#menu-subprocess-card-active", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == ESTRUTURAS_MENU_KEY_V1:
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "contas":
            return "#menu-subprocess-card-active", ""
        return "#admin-sidebar-sections-card", ""
    if clean_menu_key == "configuracao":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        return "#admin-account-status-card", ""
    if clean_menu_key == MENU_MEU_PERFIL_KEY:
        return "#perfil-pessoal-card", ""
    if clean_menu_key == "perfil_de_autorizacao":
        clean_auth_objeto_edit_key = str(
            clean_query_edit_params.get("auth_objeto_edit_key") or ""
        ).strip()
        if clean_auth_objeto_edit_key:
            return "#auth-objeto-form-card", ""

        clean_auth_profile_edit_key = str(
            clean_query_edit_params.get("auth_profile_edit_key") or ""
        ).strip()
        if clean_auth_profile_edit_key:
            return "#auth-profile-form-card", ""

    matched_menu_row = settings_by_key.get(clean_menu_key)
    if matched_menu_row is not None:
        native_default_target = _normalize_card_target_v1(
            matched_menu_row.get("admin_subprocess_default_target")
        )
        native_edit_target = _normalize_card_target_v1(
            matched_menu_row.get("admin_subprocess_edit_target")
        )
        native_edit_param = str(
            matched_menu_row.get("admin_subprocess_edit_param") or ""
        ).strip()
        active_edit_value = str(clean_query_edit_params.get(native_edit_param) or "").strip()

        if native_default_target:
            if native_edit_target and active_edit_value:
                return native_edit_target, ""
            return native_default_target, ""
        return "#dynamic-process-card", _resolve_first_dynamic_section_key(matched_menu_row)
    return "", ""


def _find_sidebar_menu_setting_by_key_v1(
    sidebar_menu_settings: list[dict[str, Any]],
    menu_key: str,
) -> dict[str, Any] | None:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    for raw_row in sidebar_menu_settings:
        if not isinstance(raw_row, dict):
            continue

        row_key = resolve_menu_key_alias(raw_row.get("key"))

        if row_key == clean_menu_key:
            return raw_row

    return None


def _resolve_dynamic_process_section_for_menu_v1(
    sidebar_menu_settings: list[dict[str, Any]],
    menu_key: str,
) -> str:
    menu_row = _find_sidebar_menu_setting_by_key_v1(sidebar_menu_settings, menu_key)

    if menu_row is None:
        return ""

    resolved_section = _resolve_first_dynamic_section_key(menu_row)

    if resolved_section == "__empty__":
        return ""

    return resolved_section


def _build_auth_profile_return_url_v1(
    *,
    sidebar_menu_settings: list[dict[str, Any]],
    dynamic_process_section: str = "",
    target: str = "",
) -> str:
    clean_target = _normalize_card_target_v1(target)
    if not clean_target or clean_target == "#auth-profile-active-card":
        clean_target = "#auth-profile-card"
    clean_dynamic_section = str(dynamic_process_section or "").strip()

    if not clean_dynamic_section:
        clean_dynamic_section = _resolve_dynamic_process_section_for_menu_v1(
            sidebar_menu_settings,
            "perfil_de_autorizacao",
        )

    query_params: dict[str, str] = {
        "menu": "perfil_de_autorizacao",
        "target": clean_target,
    }

    if clean_dynamic_section:
        query_params["dynamic_process_section"] = clean_dynamic_section

    return f"/users/new?{urlencode(query_params)}{clean_target}"


def _build_auth_objeto_return_url_v1(
    *,
    target: str = "",
) -> str:
    clean_target = _normalize_card_target_v1(target)
    if not clean_target or clean_target == "#auth-objeto-active-card":
        clean_target = "#auth-objeto-card"

    query_params: dict[str, str] = {
        "menu": "perfil_de_autorizacao",
        "target": clean_target,
    }

    return f"/users/new?{urlencode(query_params)}{clean_target}"


# APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START

def _normalize_sidebar_section_status_for_page_v22(raw_status: object, raw_is_active: object = None) -> str:
    if raw_is_active is False:
        return "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_is_active_for_page_v22(section: dict[str, Any]) -> bool:
    if not isinstance(section, dict):
        return True

    return _normalize_sidebar_section_status_for_page_v22(
        section.get("status"),
        section.get("is_active"),
    ) == "ativo"


def _resolve_sidebar_sections_from_page_data_v22(page_data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_sections = page_data.get("sidebar_section_options")

    if isinstance(raw_sections, list):
        return normalize_sidebar_sections(raw_sections)

    for menu_row in page_data.get("sidebar_menu_settings", []):
        if not isinstance(menu_row, dict):
            continue

        row_key = str(menu_row.get("key") or menu_row.get("menu_key") or "").strip().lower()

        if row_key != "administrativo":
            continue

        for possible_key in (
            MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
            "sidebar_sections",
            "sections",
            "admin_sidebar_sections",
        ):
            possible_sections = menu_row.get(possible_key)

            if isinstance(possible_sections, list):
                return normalize_sidebar_sections(possible_sections)

        menu_config = menu_row.get("menu_config")

        if isinstance(menu_config, dict):
            possible_sections = menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)

            if isinstance(possible_sections, list):
                return normalize_sidebar_sections(possible_sections)

    return []


def _split_sidebar_sections_for_page_v22(
    page_data: dict[str, Any],
    sidebar_section_edit_key: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    all_sections = _resolve_sidebar_sections_from_page_data_v22(page_data)

    active_sections = [
        section
        for section in all_sections
        if _sidebar_section_is_active_for_page_v22(section)
    ]

    inactive_sections = [
        section
        for section in all_sections
        if not _sidebar_section_is_active_for_page_v22(section)
    ]

    clean_edit_key = str(sidebar_section_edit_key or "").strip().lower()
    edit_data = None

    if clean_edit_key:
        for section in all_sections:
            section_key = str(section.get("key") or "").strip().lower()

            if section_key == clean_edit_key:
                edit_data = dict(section)
                break

    return active_sections, inactive_sections, edit_data

# APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END



@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    success: str | None = None,
    error: str | None = None,
    invite_link: str | None = None,
    entity_success: str | None = None,
    entity_error: str | None = None,
    profile_success: str | None = None,
    profile_error: str | None = None,
    settings_success: str | None = None,
    settings_error: str | None = None,
    profile_tab: str = "pessoal",
    menu: str = "home",
    admin_tab: str = "entidade",
    entity_edit_id: str = "",
    user_edit_id: str = "",
    entity_view: str = "",
    user_view: str = "",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
    target: str = "",
    profile_section: str = "",
    dynamic_process_section: str = "",
    section_key: str = "",
    sidebar_section_edit_key: str = "",
    auth_profile_edit_key: str = "",
    auth_objeto_edit_key: str = "",
    appverbo_after_save: str = "",
    debug_flicker: str | None = None,
) -> HTMLResponse:
    is_debug_flicker = (debug_flicker == "1") or (request.query_params.get("debug_flicker") == "1")
    _dbg_page = _debug_sessoes_page_enabled_v1(request)

    resolved_profile_tab = profile_tab.strip().lower()
    if resolved_profile_tab not in {"pessoal", "morada", "treinamento"}:
        resolved_profile_tab = "pessoal"
    resolved_menu = resolve_menu_key_alias(menu)
    if not resolved_menu:
        resolved_menu = "home"
    clean_settings_edit_key = resolve_menu_key_alias(settings_edit_key)
    clean_target_from_query = _normalize_card_target_v1(target)

    if _dbg_page and (resolved_menu == ESTRUTURAS_MENU_KEY_V1 or sidebar_section_edit_key):
        _log_sessoes_page_v1(
            "page:start",
            raw_menu=menu,
            resolved_menu=resolved_menu,
            raw_admin_tab=admin_tab,
            target=target,
            sidebar_section_edit_key=sidebar_section_edit_key,
            success=settings_success,
            error=settings_error,
            appverbo_after_save=appverbo_after_save,
        )

    resolved_menu, resolved_admin_tab = _resolve_estruturas_navigation_context_v1(
        resolved_menu=resolved_menu,
        resolved_admin_tab=admin_tab.strip().lower(),
        settings_edit_key=clean_settings_edit_key,
        target=clean_target_from_query,
        sidebar_section_edit_key=sidebar_section_edit_key,
    )

    if _dbg_page and (resolved_menu == ESTRUTURAS_MENU_KEY_V1 or sidebar_section_edit_key):
        _log_sessoes_page_v1(
            "page:navigation_context",
            resolved_menu=resolved_menu,
            resolved_admin_tab=resolved_admin_tab,
            target=clean_target_from_query,
            sidebar_section_edit_key=sidebar_section_edit_key,
        )
    if resolved_menu == ESTRUTURAS_MENU_KEY_V1:
        if resolved_admin_tab not in {"contas", "sessoes"}:
            resolved_admin_tab = "contas"
    else:
        if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}:
            resolved_admin_tab = "entidade"
        if resolved_admin_tab == "definicoes":
            resolved_admin_tab = "contas"
    parsed_entity_edit_id: int | None = None
    clean_entity_edit_id = entity_edit_id.strip()
    if clean_entity_edit_id.isdigit():
        parsed_entity_edit_id = int(clean_entity_edit_id)
    parsed_user_edit_id: int | None = None
    clean_user_edit_id = user_edit_id.strip()
    if clean_user_edit_id.isdigit():
        parsed_user_edit_id = int(clean_user_edit_id)
    readonly_truthy_values = {"1", "true", "sim", "yes", "on"}
    entity_readonly_mode = (
        entity_view.strip().lower() in readonly_truthy_values
        and parsed_entity_edit_id is not None
    )
    user_readonly_mode = (
        user_view.strip().lower() in readonly_truthy_values
        and parsed_user_edit_id is not None
    )
    clean_settings_action = settings_action.strip().lower()
    if clean_settings_action not in {"toggle", "edit", "delete", "create"}:
        clean_settings_action = "edit"
    clean_settings_tab = settings_tab.strip().lower()
    if clean_settings_tab not in {
        "geral",
        "campos-config",
        "campos-adicionais",
        "campos-quantidade",
        "lista",
        "campos-subsequentes",
        "sessoes-sidebar",
    }:
        clean_settings_tab = ""

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)
        current_user_is_admin = is_admin_user(
            session, current_user["id"], current_user["login_email"]
        )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        page_data = get_page_data(
            session,
            actor_user_id=current_user["id"],
            actor_login_email=current_user["login_email"],
            selected_entity_id=selected_entity_id,
        )
        visible_menu_keys = {
            str(raw_key or "").strip().lower()
            for raw_key in page_data.get("visible_sidebar_menu_keys", [])
            if str(raw_key or "").strip()
        }
        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_START
        # O menu "meu_perfil" e um processo especial que pode nao aparecer em
        # visible_sidebar_menu_keys, mas deve ser aceite quando vem no redirect
        # pos-save. Caso contrario, /users/new?menu=meu_perfil cai em Home.
        # Tambem permite menus nao visiveis se for retorno pos-save, para manter
        # o contexto de edicao.
        is_post_save_return = str(appverbo_after_save or "").strip() == "1"
        if (
            resolved_menu not in {"perfil", MENU_MEU_PERFIL_KEY}
            and resolved_menu not in visible_menu_keys
            and not is_post_save_return
        ):
            resolved_menu = "home"
        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_END

        # APPVERBO_SESSOES_POST_SAVE_GUARD_V1_START
        # Se é um retorno pós-save de Sessões, limpar sidebar_section_edit_key antes de
        # qualquer uso. Garante que o card de edição não reabre mesmo que a URL ainda
        # contenha o parâmetro por algum motivo.
        if (
            is_post_save_return
            and resolved_menu == ESTRUTURAS_MENU_KEY_V1
            and resolved_admin_tab == "sessoes"
        ):
            if _dbg_page:
                _log_sessoes_page_v1(
                    "page:post_save_guard",
                    sidebar_section_edit_key_antes=sidebar_section_edit_key,
                    acao="limpar_edit_key",
                )
            sidebar_section_edit_key = ""
        # APPVERBO_SESSOES_POST_SAVE_GUARD_V1_END

        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)
        next_entity_number = get_next_entity_number(session)
        entity_edit_data = get_entity_edit_data(
            session,
            parsed_entity_edit_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
        )
        user_edit_data = get_user_edit_data(
            session,
            parsed_user_edit_id,
            allowed_entity_ids=entity_permissions["allowed_entity_ids"],
        )

        selected_entity_number: int | None = None
        if selected_entity_id is not None:
            _sel_entity_num = session.execute(
                select(Entity.entity_number)
                .where(Entity.id == selected_entity_id)
                .limit(1)
            ).scalar_one_or_none()
            selected_entity_number = _sel_entity_num

        active_sidebar_sections_v22, inactive_sidebar_sections_v22, sidebar_section_edit_data_v22 = _split_sidebar_sections_for_page_v22(
            page_data,
            sidebar_section_edit_key,
        )

        # APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_START
        # Recalcula a separação diretamente da configuração normalizada.
        # Isto evita que o template receba a lista de ativos vazia quando houver fallback antigo.
        all_sidebar_sections_v26 = _resolve_sidebar_sections_from_page_data_v22(page_data)
        
        if all_sidebar_sections_v26:
            active_sidebar_sections_v22 = [
                section
                for section in all_sidebar_sections_v26
                if _sidebar_section_is_active_for_page_v22(section)
            ]
            inactive_sidebar_sections_v22 = [
                section
                for section in all_sidebar_sections_v26
                if not _sidebar_section_is_active_for_page_v22(section)
            ]
        
            clean_sidebar_section_edit_key_v26 = str(sidebar_section_edit_key or "").strip().lower()
        
            if clean_sidebar_section_edit_key_v26:
                sidebar_section_edit_data_v22 = next(
                    (
                        dict(section)
                        for section in all_sidebar_sections_v26
                        if str(section.get("key") or "").strip().lower() == clean_sidebar_section_edit_key_v26
                    ),
                    sidebar_section_edit_data_v22,
                )
        # APPVERBO_SESSOES_CORRIGIR_ATIVOS_SPLIT_BACKEND_V26_END
            settings_edit_data: dict[str, Any] | None = None
    if clean_settings_edit_key:
        for row in page_data.get("sidebar_menu_settings", []):
            row_key = str(row.get("key", "")).strip().lower()
            if row_key == clean_settings_edit_key:
                settings_edit_data = dict(row)
                break

    initial_target_query_edit_params_v1 = {
        "sidebar_section_edit_key": sidebar_section_edit_key,
        "auth_profile_edit_key": auth_profile_edit_key,
        "auth_objeto_edit_key": auth_objeto_edit_key,
    }

    initial_menu_target, initial_dynamic_process_section = _resolve_initial_menu_target(
        resolved_menu=resolved_menu,
        resolved_profile_tab=resolved_profile_tab,
        resolved_admin_tab=resolved_admin_tab,
        settings_edit_key=clean_settings_edit_key,
        can_manage_tenant_structure=bool(entity_permissions.get("can_manage_tenant_structure", entity_permissions.get("can_manage_all_entities", False))),
        sidebar_menu_settings=list(page_data.get("sidebar_menu_settings", [])),
        query_edit_params=initial_target_query_edit_params_v1,
    )

    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START
    clean_profile_section_from_query = str(profile_section or "").strip().lower()
    clean_dynamic_section_from_query = str(
        dynamic_process_section or section_key or ""
    ).strip()

    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

    if resolved_menu == MENU_MEU_PERFIL_KEY:
        initial_menu_target = "#perfil-pessoal-card"

    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if _dbg_page and resolved_menu == ESTRUTURAS_MENU_KEY_V1 and resolved_admin_tab == "sessoes":
        _log_sessoes_page_v1(
            "page:initial_target_before",
            initial_menu_target=initial_menu_target,
            sidebar_section_edit_key=sidebar_section_edit_key,
            appverbo_after_save=appverbo_after_save,
        )

    if resolved_menu == ESTRUTURAS_MENU_KEY_V1 and resolved_admin_tab == "sessoes":
        if str(sidebar_section_edit_key or "").strip():
            initial_menu_target = "#admin-sidebar-sections-form-card"
            if _dbg_page:
                _log_sessoes_page_v1(
                    "page:sessoes_target_decision",
                    sidebar_section_edit_key=sidebar_section_edit_key,
                    chosen_initial_menu_target="#admin-sidebar-sections-form-card",
                    motivo="edit_key_present",
                )
        else:
            initial_menu_target = "#admin-sidebar-sections-card"
            if _dbg_page:
                _log_sessoes_page_v1(
                    "page:sessoes_target_decision",
                    sidebar_section_edit_key=sidebar_section_edit_key,
                    chosen_initial_menu_target="#admin-sidebar-sections-card",
                    motivo="no_edit_key",
                )
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END


    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START
    admin_subprocess_state_v2 = None

    if current_user_is_admin:
        sessoes_subprocess_config_v2 = get_admin_subprocess_config("sessoes")

        if sessoes_subprocess_config_v2 is not None:
            all_sidebar_sections_for_subprocess_v2 = list(active_sidebar_sections_v22 or []) + list(inactive_sidebar_sections_v22 or [])
            clean_sidebar_section_edit_key_v2 = str(sidebar_section_edit_key or "").strip() if resolved_admin_tab == "sessoes" else ""

            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=sessoes_subprocess_config_v2,
                rows=all_sidebar_sections_for_subprocess_v2,
                edit_key=clean_sidebar_section_edit_key_v2,
                success=settings_success if resolved_admin_tab == "sessoes" else "",
                error=settings_error if resolved_admin_tab == "sessoes" else "",
                menu_key=ESTRUTURAS_MENU_KEY_V1,
                return_url="/users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card",
            )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END

    if _dbg_page and admin_subprocess_state_v2 is not None and resolved_admin_tab == "sessoes":
        _log_sessoes_page_v1(
            "page:admin_subprocess_state",
            is_editing=admin_subprocess_state_v2.is_editing,
            edit_key=getattr(admin_subprocess_state_v2, "edit_key", None),
            return_url=getattr(admin_subprocess_state_v2, "return_url", None),
            active_count=len(active_sidebar_sections_v22 or []),
            inactive_count=len(inactive_sidebar_sections_v22 or []),
        )

    auth_profile_subprocess_state_v1 = None

    auth_profile_menu_visible = (
        resolved_menu == "perfil_de_autorizacao"
        or "perfil_de_autorizacao" in visible_menu_keys
    )

    if auth_profile_menu_visible:
        auth_profile_subprocess_config_v1 = get_admin_subprocess_config("perfil_de_autorizacao")

        if auth_profile_subprocess_config_v1 is not None and auth_profile_subprocess_config_v1.enabled:
            try:
                clean_auth_profile_edit_key_v1 = (
                    str(auth_profile_edit_key or "").strip()
                    if resolved_menu == "perfil_de_autorizacao"
                    else ""
                )
                auth_profile_return_target_v1 = (
                    "#auth-profile-form-card"
                    if clean_auth_profile_edit_key_v1
                    else "#auth-profile-card"
                )
                auth_profile_return_url_v1 = _build_auth_profile_return_url_v1(
                    sidebar_menu_settings=list(page_data.get("sidebar_menu_settings", [])),
                    dynamic_process_section=clean_dynamic_section_from_query,
                    target=auth_profile_return_target_v1,
                )
                auth_profile_repo_v1 = AuthorizationProfileAdminRepository(
                    auth_profile_subprocess_config_v1
                )
                auth_profile_rows_v1 = auth_profile_repo_v1.list_rows(
                    session,
                    context={"user_id": current_user["id"]},
                )
                auth_profile_subprocess_state_v1 = build_admin_subprocess_state(
                    config=auth_profile_subprocess_config_v1,
                    rows=auth_profile_rows_v1,
                    edit_key=clean_auth_profile_edit_key_v1,
                    menu_key="perfil_de_autorizacao",
                    return_url=auth_profile_return_url_v1,
                    success=profile_success if resolved_menu == "perfil_de_autorizacao" else "",
                    error=profile_error if resolved_menu == "perfil_de_autorizacao" else "",
                    sidebar_menu_settings=list(page_data.get("sidebar_menu_settings") or []),
                    visible_sidebar_menu_keys=visible_menu_keys,
                    menu_process_history_map=dict(page_data.get("menu_process_history_map") or {}),
                    active_entity_id=selected_entity_id,
                )
            except Exception:
                auth_profile_subprocess_state_v1 = None

    # APPVERBO_ADMIN_SUBPROCESS_STATE_OBJETO_V1_START
    auth_objeto_subprocess_state_v1 = None

    if auth_profile_menu_visible:
        auth_objeto_subprocess_config_v1 = get_admin_subprocess_config("objeto_de_autorizacao")

        if auth_objeto_subprocess_config_v1 is not None and auth_objeto_subprocess_config_v1.enabled:
            try:
                clean_auth_objeto_edit_key_v1 = (
                    str(auth_objeto_edit_key or "").strip()
                    if resolved_menu == "perfil_de_autorizacao"
                    else ""
                )
                auth_objeto_return_target_v1 = (
                    "#auth-objeto-form-card"
                    if clean_auth_objeto_edit_key_v1
                    else "#auth-objeto-card"
                )
                auth_objeto_return_url_v1 = _build_auth_objeto_return_url_v1(
                    target=auth_objeto_return_target_v1,
                )
                auth_objeto_repo_v1 = ObjetoAutorizacaoAdminRepository(
                    auth_objeto_subprocess_config_v1
                )
                auth_objeto_rows_v1 = auth_objeto_repo_v1.list_rows(
                    session,
                    context={"user_id": current_user["id"]},
                )
                auth_objeto_subprocess_state_v1 = build_admin_subprocess_state(
                    config=auth_objeto_subprocess_config_v1,
                    rows=auth_objeto_rows_v1,
                    edit_key=clean_auth_objeto_edit_key_v1,
                    menu_key="perfil_de_autorizacao",
                    return_url=auth_objeto_return_url_v1,
                    success=profile_success if resolved_menu == "perfil_de_autorizacao" else "",
                    error=profile_error if resolved_menu == "perfil_de_autorizacao" else "",
                    sidebar_menu_settings=list(page_data.get("sidebar_menu_settings") or []),
                    visible_sidebar_menu_keys=visible_menu_keys,
                    menu_process_history_map=dict(page_data.get("menu_process_history_map") or {}),
                    active_entity_id=selected_entity_id,
                )
            except Exception:
                auth_objeto_subprocess_state_v1 = None
    # APPVERBO_ADMIN_SUBPROCESS_STATE_OBJETO_V1_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_MENU_V1_START
    admin_subprocess_menu_state_v1 = None

    if current_user_is_admin:
        menu_subprocess_config_v1 = get_admin_subprocess_config("menu")

        if menu_subprocess_config_v1 is not None and menu_subprocess_config_v1.enabled:
            try:
                from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository

                _menu_repo_v1 = MenuAdminRepository(menu_subprocess_config_v1)
                _menu_rows_v1 = _menu_repo_v1.list_rows(session, context={"entity_number": selected_entity_number})
                _menu_return_url_v1 = (
                    "/users/new?menu=sessoes&admin_tab=contas"
                    "&target=menu-subprocess-card-active#menu-subprocess-card-active"
                )
                admin_subprocess_menu_state_v1 = build_admin_subprocess_state(
                    config=menu_subprocess_config_v1,
                    rows=_menu_rows_v1,
                    edit_key="",
                    menu_key=ESTRUTURAS_MENU_KEY_V1,
                    return_url=_menu_return_url_v1,
                    success=settings_success if resolved_admin_tab == "contas" else "",
                    error=settings_error if resolved_admin_tab == "contas" else "",
                )
            except Exception:
                admin_subprocess_menu_state_v1 = None
    # APPVERBO_ADMIN_SUBPROCESS_STATE_MENU_V1_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V1_START
    def _normalize_user_rows_v1(rows: list[dict]) -> list[dict]:
        result = []
        for row in rows:
            r = dict(row)
            en = r.get("entity_number")
            r["entity_number"] = str(en) if en is not None else "-"
            r["entity_number_sort_value"] = str(en) if en is not None else ""
            result.append(r)
        return result

    admin_subprocess_entity_state = None
    admin_subprocess_user_state = AdminSubprocessState(
        config=UTILIZADOR_CONFIG,
        active_rows=_normalize_user_rows_v1(page_data.get("active_created_users", [])),
        inactive_rows=_normalize_user_rows_v1(page_data.get("inactive_users", [])),
        return_url="/users/new?menu=administrativo&admin_tab=utilizador#create-user-card",
    )

    if bool(entity_permissions.get("can_manage_tenant_structure", entity_permissions.get("can_manage_all_entities", False))):
        admin_subprocess_entity_state = AdminSubprocessState(
            config=ENTIDADE_CONFIG,
            active_rows=list(page_data.get("recent_entities", [])),
            inactive_rows=list(page_data.get("inactive_entities", [])),
            return_url="/users/new?menu=administrativo&admin_tab=entidade#recent-entities-card",
        )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V1_END

    # APPVERBO_RESOLVE_SUBMENU_TABS_V1_START
    initial_menu_tabs = []
    active_tab_index = 0
    
    clean_menu_key = resolve_menu_key_alias(resolved_menu)
    sidebar_menu_settings = list(page_data.get("sidebar_menu_settings", []))
    
    resolved_tabs_config = resolve_process_tabs_v1(clean_menu_key, sidebar_menu_settings)
    initial_menu_tabs = [t.to_dict() for t in resolved_tabs_config]
    
    if initial_menu_tabs:
        active_tab_index = _resolve_active_tab_index_v1(
            menu_key=clean_menu_key,
            initial_menu_tabs=initial_menu_tabs,
            initial_menu_target=initial_menu_target,
            initial_dynamic_process_section=initial_dynamic_process_section,
        )
        active_tab = initial_menu_tabs[active_tab_index]
        initial_dynamic_process_section = active_tab.get("dynamic_process_section", "")
        if not (
            clean_menu_key == "perfil_de_autorizacao"
            and _normalize_authorization_profile_target_v1(initial_menu_target)
        ):
            initial_menu_target = active_tab.get("target")

    active_menu_label = ""
    active_menu_is_list_process = False
    for setting in sidebar_menu_settings:
        if setting.get("key") == clean_menu_key:
            active_menu_label = setting.get("label")
            active_menu_is_list_process = bool(setting.get("is_list_process", False))
            break
            
    if not active_menu_label:
        if clean_menu_key == "home":
            active_menu_label = "Home"
        elif clean_menu_key == "meu_perfil":
            active_menu_label = "Meu perfil"
        else:
            active_menu_label = clean_menu_key.replace("_", " ").title()
    # APPVERBO_RESOLVE_SUBMENU_TABS_V1_END

    context = {
        "request": request,
        "initial_menu_tabs": initial_menu_tabs,
        "active_tab_index": active_tab_index,
        "initial_menu_label": active_menu_label,
        "initial_menu_is_list_process": active_menu_is_list_process,
        "errors": [error] if error else [],
        "success": success or "",
        "generated_invite_link": (invite_link or "").strip(),
        "form_data": get_form_defaults(),
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": entity_edit_data,
        "user_edit_data": user_edit_data,
        "entity_readonly_mode": bool(entity_readonly_mode),
        "user_readonly_mode": bool(user_readonly_mode),
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "user_personal_data": user_personal_data,
        "entity_success": entity_success or "",
        "entity_error": entity_error or "",
        "next_entity_number": str(next_entity_number),
        "profile_success": profile_success or "",
        "profile_error": profile_error or "",
        "settings_success": settings_success or "",
        "settings_error": settings_error or "",
        "settings_edit_data": settings_edit_data,
        "selected_entity_number": str(selected_entity_number) if selected_entity_number is not None else "",
        "settings_edit_key": clean_settings_edit_key,
        "settings_action": clean_settings_action,
        "settings_tab": clean_settings_tab,
        "profile_tab": resolved_profile_tab,
        "initial_menu": resolved_menu,
        "initial_menu_target": initial_menu_target,
        "initial_dynamic_process_section": initial_dynamic_process_section,
        "initial_profile_section": clean_profile_section_from_query,
        "requested_profile_section": clean_profile_section_from_query,
        "requested_dynamic_process_section": clean_dynamic_section_from_query,
        "appverbo_after_save": is_post_save_return,
        "sidebar_section_edit_key": str(sidebar_section_edit_key or "").strip().lower(),
        "auth_profile_edit_key": str(auth_profile_edit_key or "").strip().lower(),
        "auth_objeto_edit_key": str(auth_objeto_edit_key or "").strip().lower(),
        "sidebar_section_edit_data": sidebar_section_edit_data_v22,
        "active_sidebar_sections": active_sidebar_sections_v22,
        "inactive_sidebar_sections": inactive_sidebar_sections_v22,
        "admin_tab": resolved_admin_tab,
        "admin_subprocess_state": admin_subprocess_state_v2,
        "auth_profile_subprocess_state": auth_profile_subprocess_state_v1,
        "auth_objeto_subprocess_state": auth_objeto_subprocess_state_v1,
        "admin_subprocess_menu_state": admin_subprocess_menu_state_v1,
        "admin_subprocess_entity_state": admin_subprocess_entity_state,
        "admin_subprocess_user_state": admin_subprocess_user_state,
        "current_user_can_manage_tenant_structure": bool(entity_permissions.get("can_manage_tenant_structure", entity_permissions.get("can_manage_all_entities", False))),
        "current_user_can_manage_all_entities": bool(entity_permissions.get("can_manage_all_entities", False)),
        "debug_flicker": is_debug_flicker,
        **page_data,
    }

    # ###################################################################################
    # TEMPORARY: DEBUG FLICKER VALIDATION
    # ###################################################################################
    if is_debug_flicker:
        print(
            f"[APPVERBO FLICKER DEBUG BACKEND]\n"
            f"- menu resolvido: {resolved_menu}\n"
            f"- admin_tab resolvido: {resolved_admin_tab}\n"
            f"- target resolvido: {initial_menu_target}\n"
            f"- admin_subprocess_state presente: {admin_subprocess_state_v2 is not None}\n"
            f"- qual subprocesso administrativo montado: {admin_subprocess_state_v2.config.key if admin_subprocess_state_v2 else 'Nenhum'}\n"
            f"- template renderizando Sessões: {'Sim' if admin_subprocess_state_v2 and admin_subprocess_state_v2.config.key == 'sessoes' else 'Não'}\n"
            f"- template renderizando Perfil de autorização: {'Sim' if auth_profile_subprocess_state_v1 is not None else 'Não'}"
        )

    return templates.TemplateResponse(request, "new_user.html", context)
