from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_START
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.service import build_admin_subprocess_state
# APPVERBO_ADMIN_SUBPROCESS_V2_PAGE_IMPORTS_START
from appverbo.admin_subprocesses.v2_service import build_admin_subprocess_state_v2
# APPVERBO_ADMIN_SUBPROCESS_V2_PAGE_IMPORTS_END
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
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)

from appverbo.routes.profile.router import router


def _write_meu_perfil_page_flow_debug_log_v1(
    request: Request,
    stage: str,
    data: dict[str, Any] | None = None,
) -> None:
    import json
    import os
    from pathlib import Path

    try:
        log_dir = Path(
            os.environ.get(
                "APPVERBO_PROFILE_SAVE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG_V1",
            "stage": str(stage or "").strip(),
            "request": {
                "method": str(getattr(request, "method", "") or ""),
                "path": str(getattr(getattr(request, "url", None), "path", "") or ""),
                "url": str(getattr(request, "url", "") or ""),
                "client": str(getattr(getattr(request, "client", None), "host", "") or ""),
            },
            "data": data or {},
        }

        log_line = json.dumps(log_entry, ensure_ascii=False, default=str, sort_keys=True)
        log_path = log_dir / "meu_perfil_process_flow.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG " + log_line, flush=True)
    except Exception as exc:
        print("APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG_ERROR " + repr(exc), flush=True)


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
    can_manage_all_entities: bool,
    sidebar_menu_settings: list[dict[str, Any]],
) -> tuple[str, str]:
    clean_menu_key = resolve_menu_key_alias(resolved_menu)
    settings_by_key = {
        str(raw_row.get("key") or "").strip().lower(): raw_row
        for raw_row in sidebar_menu_settings
        if isinstance(raw_row, dict) and str(raw_row.get("key") or "").strip()
    }

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
        if resolved_admin_tab == "menu":
            return "#settings-card", ""
        if resolved_admin_tab == "sessoes":
            return "#admin-sidebar-sections-card", ""
        if resolved_admin_tab == "contas":
            return "#admin-account-status-card", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == "configuracao":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        return "#admin-account-status-card", ""
    if clean_menu_key == MENU_MEU_PERFIL_KEY:
        return "#perfil-pessoal-card", ""

    matched_menu_row = settings_by_key.get(clean_menu_key)
    if matched_menu_row is not None:
        return "#dynamic-process-card", _resolve_first_dynamic_section_key(matched_menu_row)
    return "", ""


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
    sidebar_sections_tab: str = "",
    appverbo_after_save: str = "",
) -> HTMLResponse:
    resolved_profile_tab = profile_tab.strip().lower()
    if resolved_profile_tab not in {"pessoal", "morada", "treinamento"}:
        resolved_profile_tab = "pessoal"
    resolved_menu = resolve_menu_key_alias(menu)
    if not resolved_menu:
        resolved_menu = "home"
    resolved_admin_tab = admin_tab.strip().lower()
    if resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes", "menu"}:
        resolved_admin_tab = "entidade"
    if resolved_admin_tab == "definicoes":
        resolved_admin_tab = "contas"

    # APPVERBO_INFER_ADMIN_SESSOES_REFRESH_V1_START
    # Quando o browser atualiza uma URL antiga/curta do subprocesso de sessoes,
    # a query pode chegar apenas com target=admin-sidebar-sections-card,
    # sem admin_tab=sessoes. Nesse caso, a página misturava o subprocesso
    # com Home/Entidade. Forçamos o contexto correto no backend.
    clean_target_for_admin_refresh = str(target or "").strip().lower()
    clean_settings_tab_for_admin_refresh = (
        str(settings_tab or "")
        .strip()
        .lower()
        .replace("_", "-")
    )
    clean_sidebar_sections_tab_for_admin_refresh = (
        str(sidebar_sections_tab or "")
        .strip()
        .lower()
        .replace("_", "-")
    )
    clean_sidebar_section_edit_key_for_admin_refresh = str(sidebar_section_edit_key or "").strip()

    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "entidade"
        and (
            clean_settings_tab_for_admin_refresh in {"sessoes", "sessoes-sidebar"}
            or clean_sidebar_sections_tab_for_admin_refresh in {"sessoes", "sessoes-sidebar"}
            or bool(clean_sidebar_section_edit_key_for_admin_refresh)
            or "admin-sidebar-sections" in clean_target_for_admin_refresh
            or "sidebar-sections" in clean_target_for_admin_refresh
        )
    ):
        resolved_admin_tab = "sessoes"
    # APPVERBO_INFER_ADMIN_SESSOES_REFRESH_V1_END
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
    clean_settings_edit_key = resolve_menu_key_alias(settings_edit_key)
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
        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)
        next_entity_internal_number = get_next_entity_internal_number(session)
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

    initial_menu_target, initial_dynamic_process_section = _resolve_initial_menu_target(
        resolved_menu=resolved_menu,
        resolved_profile_tab=resolved_profile_tab,
        resolved_admin_tab=resolved_admin_tab,
        settings_edit_key=clean_settings_edit_key,
        can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
        sidebar_menu_settings=list(page_data.get("sidebar_menu_settings", [])),
    )

    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START
    clean_target_from_query = str(target or "").strip()
    if clean_target_from_query and not clean_target_from_query.startswith("#"):
        clean_target_from_query = f"#{clean_target_from_query}"
    clean_profile_section_from_query = str(profile_section or "").strip().lower()
    clean_dynamic_section_from_query = str(
        dynamic_process_section or section_key or ""
    ).strip()

    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

    if (
        resolved_menu == MENU_MEU_PERFIL_KEY
        and clean_target_from_query != "#dynamic-process-card"
        and not clean_dynamic_section_from_query
    ):
        initial_menu_target = "#perfil-pessoal-card"

    if (
        resolved_menu == MENU_MEU_PERFIL_KEY
        and clean_dynamic_section_from_query
        and not clean_target_from_query
    ):
        initial_menu_target = "#dynamic-process-card"

    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if resolved_menu == "administrativo" and resolved_admin_tab == "sessoes":
        if str(sidebar_section_edit_key or "").strip():
            initial_menu_target = "#admin-sidebar-sections-form-card"
        else:
            initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    elif resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#admin-menu-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END



    # APPVERBO_ADMIN_MENU_TAB_TARGET_V1_START
    # A aba Administrativo -> Menu usa o bloco legado settings-card.
    # Sem esta normalização, a URL admin_tab=menu pode ficar sem conteúdo
    # porque o backend voltava para o target padrão de Entidade.
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_TAB_TARGET_V1_END


    # APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_START
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"

        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_TARGET_RENDER_V3_END


    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_START
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        if clean_settings_edit_key:
            initial_menu_target = "#settings-menu-edit-card"
        else:
            initial_menu_target = "#settings-card"

        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_END

    # APPVERBO_ADMIN_PROCESS_ONLY_V1_START
    # Quando o utilizador clica apenas no processo "Administrativo",
    # a tela deve mostrar somente o bloco central de subprocessos.
    # Os cards de Entidade, Utilizador, Sessoes e Menu so aparecem
    # depois do clique no subprocesso correspondente.
    raw_admin_tab_param_for_process_only = str(request.query_params.get("admin_tab", "") or "").strip()
    raw_target_param_for_process_only = str(request.query_params.get("target", "") or "").strip()
    raw_hash_target_for_process_only = str(request.query_params.get("hash", "") or "").strip()
    raw_settings_edit_key_for_process_only = str(request.query_params.get("settings_edit_key", "") or "").strip()
    raw_sidebar_section_edit_key_for_process_only = str(request.query_params.get("sidebar_section_edit_key", "") or "").strip()
    raw_settings_tab_for_process_only = str(request.query_params.get("settings_tab", "") or "").strip()
    raw_sidebar_sections_tab_for_process_only = str(request.query_params.get("sidebar_sections_tab", "") or "").strip()

    admin_process_only = (
        resolved_menu == "administrativo"
        and not raw_admin_tab_param_for_process_only
        and not raw_target_param_for_process_only
        and not raw_hash_target_for_process_only
        and not raw_settings_edit_key_for_process_only
        and not raw_sidebar_section_edit_key_for_process_only
        and not raw_settings_tab_for_process_only
        and not raw_sidebar_sections_tab_for_process_only
    )

    if admin_process_only:
        initial_menu_target = "#menu-tabs-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_PROCESS_ONLY_V1_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START
    admin_subprocess_state_v2 = None

        # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START
    if resolved_menu == "administrativo" and resolved_admin_tab == "entidade":
        admin_subprocess_state_v2 = build_admin_subprocess_state_v2(
            key="entidade",
            session=session,
            request=request,
            current_user=current_user,
            edit_key=clean_entity_edit_id,
            success=entity_success or "",
            error=entity_error or "",
            return_url="/users/new?menu=administrativo&admin_tab=entidade&target=%23admin-subprocess-v2-entidade",
        )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_END

    if resolved_menu == "administrativo" and resolved_admin_tab == "sessoes":
        sessoes_subprocess_config_v2 = get_admin_subprocess_config("sessoes")

        if sessoes_subprocess_config_v2 is not None:
            # APPVERBO_SESSOES_HIERARQUIA_RENDER_BD_V1_START
            # A hierarquia deve refletir a ordem persistida no menu_config do BD.
            # O page_data pode trazer dados já preparados para outros blocos da página
            # e, após o redirect do POST das setas, pode reconstruir a lista sem
            # preservar a alteração visual esperada.
            try:
                from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
                    SidebarSectionAdminRepository,
                )

                all_sidebar_sections_for_subprocess_v3 = SidebarSectionAdminRepository(
                    sessoes_subprocess_config_v2
                ).list_rows(session)
            except Exception:
                all_sidebar_sections_for_subprocess_v3 = list(active_sidebar_sections_v22 or []) + list(inactive_sidebar_sections_v22 or [])
            # APPVERBO_SESSOES_HIERARQUIA_RENDER_BD_V1_END

            clean_sidebar_section_edit_key_v2 = str(sidebar_section_edit_key or "").strip()

            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=sessoes_subprocess_config_v2,
                rows=all_sidebar_sections_for_subprocess_v3,
                edit_key=clean_sidebar_section_edit_key_v2,
                success=settings_success if resolved_admin_tab == "sessoes" else "",
                error=settings_error if resolved_admin_tab == "sessoes" else "",
                return_url="/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card",
            )
    elif resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        menu_subprocess_config = get_admin_subprocess_config("menu")

        if menu_subprocess_config is not None:
            menu_field_options: dict[str, tuple[tuple[str, str], ...]] = {
                "sidebar_section": tuple(
                    (
                        str(option.get("key") or "").strip().lower(),
                        str(option.get("label") or "").strip(),
                    )
                    for option in page_data.get("sidebar_section_options", [])
                    if str(option.get("key") or "").strip() and str(option.get("label") or "").strip()
                )
            }
            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=menu_subprocess_config,
                rows=[
                    row
                    for row in page_data.get("sidebar_menu_settings", [])
                    if not bool(row.get("is_deleted"))
                ],
                edit_key="",
                success=settings_success if resolved_admin_tab == "menu" else "",
                error=settings_error if resolved_admin_tab == "menu" else "",
                return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card",
                field_options=menu_field_options,
            )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END

    context = {
        "request": request,
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
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": profile_success or "",
        "profile_error": profile_error or "",
        "settings_success": settings_success or "",
        "settings_error": settings_error or "",
        "settings_edit_data": settings_edit_data,
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
        "admin_process_only": bool(admin_process_only),
        "sidebar_section_edit_key": str(sidebar_section_edit_key or "").strip().lower(),
        "sidebar_section_edit_data": sidebar_section_edit_data_v22,
        "active_sidebar_sections": active_sidebar_sections_v22,
        "inactive_sidebar_sections": inactive_sidebar_sections_v22,
        "admin_tab": resolved_admin_tab,
        "admin_subprocess_state": admin_subprocess_state_v2,
        "current_user_can_manage_all_entities": bool(
            entity_permissions["can_manage_all_entities"]
        ),
        **page_data,
    }
    _write_meu_perfil_page_flow_debug_log_v1(
        request,
        "04_users_new_render_context",
        {
            "resolved_menu": resolved_menu,
            "resolved_profile_tab": resolved_profile_tab,
            "resolved_admin_tab": resolved_admin_tab,
            "clean_target_from_query": clean_target_from_query,
            "clean_profile_section_from_query": clean_profile_section_from_query,
            "clean_dynamic_section_from_query": clean_dynamic_section_from_query,
            "initial_menu_target": initial_menu_target,
            "initial_dynamic_process_section": initial_dynamic_process_section,
            "is_post_save_return": is_post_save_return,
            "profile_success": profile_success or "",
            "profile_error": profile_error or "",
        },
    )
    return templates.TemplateResponse(request, "new_user.html", context)


