from __future__ import annotations

from appverbo.page_state.pagina_default import resolver_pagina_default_v1
from datetime import datetime, timezone
from typing import Any

from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_START
from appverbo.admin_subprocesses.menu.service import build_admin_menu_state
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.service import build_admin_subprocess_state
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_END
from appverbo.admin_subprocesses.utilizador.pagina import montar_estado_pagina_utilizador_v1
from appverbo.core import *  # noqa: F403,F401
from appverbo.menu_settings import (
    MENU_MEU_PERFIL_KEY,
    resolve_menu_key_alias,
)
from appverbo.routes.profile.router import router
from appverbo.services import *  # noqa: F403,F401
from appverbo.services.menu_admin_context import (
    build_menu_admin_context_v1,
    build_menu_admin_page_payload_v1,
)
from appverbo.services.sessoes_admin_context import (
    build_sessoes_admin_context_v1,
    build_sessoes_admin_page_payload_v1,
)
from appverbo.services.users.context import build_user_admin_edit_context_v1


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


def _resolve_admin_menu_target_v1(settings_edit_key: str) -> str:
    if str(settings_edit_key or "").strip():
        return "#settings-menu-edit-card"

    return "#admin-menu-card"


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
        if resolved_admin_tab == "menu":
            return _resolve_admin_menu_target_v1(settings_edit_key), ""
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "sessoes":
            return "#admin-sidebar-sections-card", ""
        if resolved_admin_tab in {"menu", "contas", "definicoes"}:
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


# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_START

def _normalize_admin_tab_menu_v1(raw_admin_tab: object) -> str:
    clean_admin_tab = str(raw_admin_tab or "").strip().lower()

    legacy_aliases = {
        "contas": "menu",
        "definicoes": "menu",
    }

    clean_admin_tab = legacy_aliases.get(clean_admin_tab, clean_admin_tab)

    if clean_admin_tab not in {"utilizador", "entidade", "menu", "sessoes"}:
        return "entidade"

    return clean_admin_tab

# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_END


# APPVERBO_ADMIN_TAB_SESSOES_FALLBACK_V1_START
def _resolve_sessions_admin_tab_fallback_v1(
    *,
    resolved_menu: str,
    resolved_admin_tab: str,
    target: str,
    sidebar_sections_tab: str,
    sidebar_section_edit_key: str,
) -> str:
    if str(resolved_menu or "").strip().lower() != "administrativo":
        return resolved_admin_tab

    clean_target = str(target or "").strip().lower()
    if clean_target.startswith("#"):
        clean_target = clean_target[1:]

    clean_sidebar_sections_tab = str(sidebar_sections_tab or "").strip().lower()
    clean_sidebar_section_edit_key = str(sidebar_section_edit_key or "").strip()
    session_target_keys = {
        "admin-sidebar-sections-card",
        "admin-sidebar-sections-form-card",
        "admin-sidebar-sections-card-create",
        "admin-sidebar-sections-card-inactive",
    }

    if (
        clean_sidebar_sections_tab == "sessoes"
        or bool(clean_sidebar_section_edit_key)
        or clean_target in session_target_keys
    ):
        return "sessoes"

    return resolved_admin_tab


# APPVERBO_ADMIN_TAB_SESSOES_FALLBACK_V1_END





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
    resolved_admin_tab = _normalize_admin_tab_menu_v1(admin_tab)
    resolved_admin_tab = _resolve_sessions_admin_tab_fallback_v1(
        resolved_menu=resolved_menu,
        resolved_admin_tab=resolved_admin_tab,
        target=target,
        sidebar_sections_tab=sidebar_sections_tab,
        sidebar_section_edit_key=sidebar_section_edit_key,
    )
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
        entity_view.strip().lower() in readonly_truthy_values and parsed_entity_edit_id is not None
    )
    user_readonly_mode = (
        user_view.strip().lower() in readonly_truthy_values and parsed_user_edit_id is not None
    )
    clean_settings_edit_key = resolve_menu_key_alias(settings_edit_key)
    clean_settings_action = settings_action.strip().lower()
    # APPVERBO_ADMIN_MENU_ALLOW_MOVE_ACTIONS_V1
    if clean_settings_action not in {"toggle", "edit", "delete", "create", "move_up", "move_down"}:
        clean_settings_action = "edit"
    clean_settings_tab = settings_tab.strip().lower()
    if clean_settings_tab not in {
        "geral",
        "menu",
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
        user_edit_context = build_user_admin_edit_context_v1(
            session=session,
            actor_user_id=int(current_user["id"]),
            actor_login_email=str(current_user["login_email"]),
            selected_entity_id=selected_entity_id,
            user_edit_id=parsed_user_edit_id,
        )
        user_edit_data = user_edit_context.get("user_edit_data", get_user_edit_defaults())

        sessoes_admin_context = build_sessoes_admin_context_v1(
            session=session,
            actor_user_id=int(current_user["id"]),
            actor_login_email=str(current_user["login_email"]),
            selected_entity_id=selected_entity_id,
            session_edit_key=sidebar_section_edit_key,
        )
        sessoes_admin_page_payload = build_sessoes_admin_page_payload_v1(
            sessoes_admin_context
        )

        active_sidebar_sections_v22 = list(
            sessoes_admin_page_payload.get("active_sidebar_sections", [])
        )
        inactive_sidebar_sections_v22 = list(
            sessoes_admin_page_payload.get("inactive_sidebar_sections", [])
        )
        sidebar_section_edit_data_v22 = dict(
            sessoes_admin_page_payload.get("sidebar_section_edit_data", {})
        )
        menu_admin_context = build_menu_admin_context_v1(
            session=session,
            actor_user_id=int(current_user["id"]),
            actor_login_email=str(current_user["login_email"]),
            selected_entity_id=selected_entity_id,
            menu_edit_key=clean_settings_edit_key,
        )
        menu_admin_page_payload = build_menu_admin_page_payload_v1(menu_admin_context)

        settings_edit_data: dict[str, Any] | None = None
        if clean_settings_edit_key:
            candidate_menu_edit_data = dict(menu_admin_page_payload.get("menu_edit_data", {}))

            if str(candidate_menu_edit_data.get("key") or "").strip():
                settings_edit_data = candidate_menu_edit_data
            else:
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
        sidebar_menu_settings=list(
            menu_admin_page_payload.get("menu_settings")
            or page_data.get("sidebar_menu_settings", [])
        ),
    )

    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START
    clean_target_from_query = str(target or "").strip()
    if clean_target_from_query and not clean_target_from_query.startswith("#"):
        clean_target_from_query = f"#{clean_target_from_query}"
    clean_profile_section_from_query = str(profile_section or "").strip().lower()
    clean_dynamic_section_from_query = str(dynamic_process_section or section_key or "").strip()

    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START
    if (
        resolved_menu == "administrativo"
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        initial_menu_target = "#edit-user-card"
        initial_dynamic_process_section = ""
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_END


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
        initial_menu_target = _resolve_admin_menu_target_v1(clean_settings_edit_key)
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
    # APPVERBO_PAGE_STATE_CONTEXT_V1_START
    page_state = resolver_pagina_default_v1(
        resolved_menu=resolved_menu,
        resolved_admin_tab=resolved_admin_tab,
        resolved_profile_tab=resolved_profile_tab,
        parsed_user_edit_id=parsed_user_edit_id,
        user_view=user_view,
        parsed_entity_edit_id=parsed_entity_edit_id,
        entity_view=entity_view,
        clean_settings_edit_key=clean_settings_edit_key,
        clean_settings_action=clean_settings_action,
        clean_target_from_query=clean_target_from_query,
        clean_profile_section_from_query=clean_profile_section_from_query,
        clean_dynamic_section_from_query=clean_dynamic_section_from_query,
        sidebar_section_edit_key=sidebar_section_edit_key,
        is_post_save_return=is_post_save_return,
    )
    # APPVERBO_PAGE_STATE_CONTEXT_V1_END
    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END

    # ###################################################################################
    # A aba Administrativo -> Menu usa o alvo canonico admin-menu-card.
    # Sem esta normalizacao, a URL admin_tab=menu pode ficar sem conteudo
    # porque o backend voltava para o target padrao de Entidade.
    if resolved_menu == "administrativo" and resolved_admin_tab == "menu":
        initial_menu_target = _resolve_admin_menu_target_v1(clean_settings_edit_key)
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_END

    # APPVERBO_ADMIN_PROCESS_ONLY_V1_START
    # Quando o utilizador clica apenas no processo "Administrativo",
    # a tela deve mostrar somente o bloco central de subprocessos.
    # Os cards de Entidade, Utilizador, Sessoes e Menu so aparecem
    # depois do clique no subprocesso correspondente.
    raw_admin_tab_param_for_process_only = str(
        request.query_params.get("admin_tab", "") or ""
    ).strip()
    raw_target_param_for_process_only = str(request.query_params.get("target", "") or "").strip()
    raw_hash_target_for_process_only = str(request.query_params.get("hash", "") or "").strip()
    raw_settings_edit_key_for_process_only = str(
        request.query_params.get("settings_edit_key", "") or ""
    ).strip()
    raw_sidebar_section_edit_key_for_process_only = str(
        request.query_params.get("sidebar_section_edit_key", "") or ""
    ).strip()
    raw_settings_tab_for_process_only = str(
        request.query_params.get("settings_tab", "") or ""
    ).strip()
    raw_sidebar_sections_tab_for_process_only = str(
        request.query_params.get("sidebar_sections_tab", "") or ""
    ).strip()
    clean_settings_action_for_admin_refresh = str(settings_action or "").strip().lower()

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


    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_START
    if resolved_admin_tab == "menu":
        initial_menu_target = _resolve_admin_menu_target_v1(clean_settings_edit_key)
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START
    admin_subprocess_state_v2 = None
    admin_menu_state = None

    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START
    # Entidade permanece no fluxo legado em /users/new.
    # O renderer V2 ainda nao entrega as secoes de listagem esperadas no template
    # e acabava por mostrar apenas o botao "Criar entidade".
    if resolved_menu == "administrativo" and resolved_admin_tab == "entidade":
        admin_subprocess_state_v2 = None
    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_END

    if resolved_menu == "administrativo" and resolved_admin_tab == "sessoes":
        sessoes_subprocess_config_v2 = get_admin_subprocess_config("sessoes")

        if sessoes_subprocess_config_v2 is not None:
            all_sidebar_sections_for_subprocess_v3 = list(
                sessoes_admin_page_payload.get("all_sessions", [])
            )

            if not all_sidebar_sections_for_subprocess_v3:
                all_sidebar_sections_for_subprocess_v3 = list(
                    active_sidebar_sections_v22 or []
                ) + list(inactive_sidebar_sections_v22 or [])

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
        admin_menu_state = build_admin_menu_state(
            rows=[
                row
                for row in menu_admin_page_payload.get("menu_settings", [])
                if not bool(row.get("is_deleted"))
            ],
            section_options=tuple(
                (
                    str(option.get("key") or "").strip().lower(),
                    str(option.get("label") or "").strip(),
                )
                for option in menu_admin_page_payload.get("sidebar_section_options", [])
                if str(option.get("key") or "").strip()
                and str(option.get("label") or "").strip()
            ),
            can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
            success=settings_success if resolved_admin_tab == "menu" else "",
            error=settings_error if resolved_admin_tab == "menu" else "",
            return_url="/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card",
        )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START
    # Estado nativo em paralelo para validar o subprocesso Utilizador sem trocar a tela legada.
    # O bloco usa sessao propria para ficar isolado da estrutura legada da pagina.
    admin_subprocess_shadow_state_v1 = None

    if resolved_admin_tab == "utilizador":
        utilizador_subprocess_config_v1 = get_admin_subprocess_config("utilizador")

        if utilizador_subprocess_config_v1 is not None:
            with SessionLocal() as admin_subprocess_shadow_session_v1:
                admin_subprocess_shadow_state_v1 = build_admin_subprocess_state_from_repository(
                    config=utilizador_subprocess_config_v1,
                    session=admin_subprocess_shadow_session_v1,
                    edit_key=clean_user_edit_id,
                    success=success or "",
                    error=error or "",
                    return_url="/users/new?menu=administrativo&admin_tab=utilizador",
                    context={
                        "page_state": page_state,
                        "page_state_refresh_home_url": page_state.get("refresh_home_url", "/users/new?menu=home"),
                        "current_user": current_user,
                        "selected_entity_id": selected_entity_id,
                        "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                        "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                    },
                )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END

    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_START
    admin_subprocess_state_utilizador_v1 = None

    if resolved_admin_tab == "utilizador":
        with SessionLocal() as utilizador_subprocess_session_v1:
            admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1(
                session=utilizador_subprocess_session_v1,
                user_edit_id=clean_user_edit_id,
                user_view=user_view,
                selected_entity_id=selected_entity_id,
                allowed_entity_ids=entity_permissions["allowed_entity_ids"],
                success=success or "",
                error=error or "",
            )
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_END





    context = {
        "admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,
        "page_state": page_state,
        "page_state_refresh_home_url": page_state.get("refresh_home_url", "/users/new?menu=home"),
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
        "sessions": list(sessoes_admin_page_payload.get("sessions", [])),
        "all_sessions": list(sessoes_admin_page_payload.get("all_sessions", [])),
        "active_sessions": list(sessoes_admin_page_payload.get("active_sessions", [])),
        "inactive_sessions": list(sessoes_admin_page_payload.get("inactive_sessions", [])),
        "pending_sessions": list(sessoes_admin_page_payload.get("pending_sessions", [])),
        "blocked_sessions": list(sessoes_admin_page_payload.get("blocked_sessions", [])),
        "session_edit_data": dict(sessoes_admin_page_payload.get("session_edit_data", {})),
        "session_permissions": dict(sessoes_admin_page_payload.get("session_permissions", {})),
        "session_list_pagination": dict(
            sessoes_admin_page_payload.get("session_list_pagination", {})
        ),
        "sidebar_sections_tab": str(
            sessoes_admin_page_payload.get("sidebar_sections_tab") or "sessoes"
        ),
        "admin_tab": resolved_admin_tab,
        "admin_subprocess_state": admin_subprocess_state_utilizador_v1 if resolved_admin_tab == "utilizador" else admin_subprocess_state_v2,
        "admin_subprocess_state_utilizador": admin_subprocess_state_utilizador_v1,
        "admin_subprocess_shadow_state_v1": admin_subprocess_state_utilizador_v1,
        "admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,
        "admin_menu_state": admin_menu_state,
        "admin_menu_template_ready_v1": True,
        "admin_menu_template_mode": (str(request.query_params.get("admin_menu_template_mode") or "native").strip().lower() or "native"),
        "current_user_can_manage_all_entities": bool(entity_permissions["can_manage_all_entities"]),
        **page_data,
    }
    context["sidebar_menu_settings"] = list(
        menu_admin_page_payload.get("menu_settings")
        or page_data.get("sidebar_menu_settings", [])
    )
    context["sidebar_section_options"] = list(
        menu_admin_page_payload.get("sidebar_section_options")
        or page_data.get("sidebar_section_options", [])
    )
    context["menu_section_options"] = list(
        menu_admin_page_payload.get("menu_section_options")
        or page_data.get("sidebar_section_options", [])
    )
    context["menu_permissions"] = dict(
        menu_admin_page_payload.get("menu_permissions", {})
    )
    context["menu_list_pagination"] = dict(
        menu_admin_page_payload.get("menu_list_pagination", {})
    )
    context["menu_edit_data"] = dict(
        menu_admin_page_payload.get("menu_edit_data", {})
    )
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
