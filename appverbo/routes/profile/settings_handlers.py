# ###################################################################################
# (1) ATUALIZACAO DOS CAMPOS ADICIONAIS DO PROCESSO MENU - V1
# ###################################################################################

import json

from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from starlette.requests import Request as RequestType

from appverbo.routes.profile.router import router

# ###################################################################################
# (2) MOVER CAMPO ADICIONAL NO FORMULÁRIO - V1
# ###################################################################################

from appverbo.menu_settings import (
    create_sidebar_menu_setting,
    delete_sidebar_menu_setting,
    move_sidebar_menu_setting,
    move_sidebar_menu_additional_field,
    resolve_menu_key_alias,
    set_sidebar_menu_visibility,
    update_sidebar_menu_label,
    update_sidebar_menu_additional_fields_v1,
    update_sidebar_menu_process_fields,
    update_sidebar_menu_process_lists,
    update_sidebar_menu_process_quantity_fields_v1,
    update_sidebar_menu_subsequent_fields,
    update_sidebar_sections_v2,
    get_sidebar_global_refresh_version_v1,
)
from appverbo.core import SessionLocal
from appverbo.services.session import get_current_user
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_session_entity_id
from appverbo.repositories.entity_repository import get_entity_by_id
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER


def _build_settings_redirect_url(
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
) -> str:
    params = []
    if error_message:
        params.append(f"error={error_message}")
    if success_message:
        params.append(f"success={success_message}")
    if redirect_menu:
        params.append(f"menu={redirect_menu}")
    if redirect_target:
        params.append(f"target={redirect_target.lstrip('#')}")
    if settings_edit_key:
        params.append(f"settings_edit_key={settings_edit_key}")
    if settings_action:
        params.append(f"settings_action={settings_action}")
    if settings_tab:
        params.append(f"settings_tab={settings_tab}")
    return f"/users/new?{chr(38).join(params)}"


def _require_menu_settings_owner_v1(
    session,
    request: Request,
    redirect_menu: str,
    redirect_target: str,
    settings_edit_key: str = "",
    settings_action: str = "edit",
    settings_tab: str = "geral",
) -> RedirectResponse | None:
    current_user = get_current_user(request, session)

    if current_user is None:
        return RedirectResponse(
            url="/login?error=Efetue login para continuar.",
            status_code=HTTP_302_FOUND,
        )

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return RedirectResponse(
            url=_build_settings_redirect_url(
                error_message="Apenas administradores podem alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )

    selected_entity_id = get_session_entity_id(request)
    permissions = get_user_entity_permissions(
        session,
        current_user["id"],
        current_user["login_email"],
        selected_entity_id,
    )

    if not permissions["can_manage_all_entities"]:
        return RedirectResponse(
            url=_build_settings_redirect_url(
                error_message="Apenas Owner pode alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )

    return None


# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START

# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1) CONSULTAR VERSAO GLOBAL DO SIDEBAR
# ###################################################################################

@router.get("/settings/menu/sidebar-refresh-version")
def get_sidebar_refresh_version_v1(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {"authenticated": False, "version": ""},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_version = get_sidebar_global_refresh_version_v1(session)

        return JSONResponse(
            {
                "authenticated": True,
                "version": refresh_version,
            }
        )

# APPVERBO_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_END

# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_START

# ###################################################################################
# (SIDEBAR_SECTIONS_DATA_ENDPOINT_V6) LER SESSOES DO SIDEBAR DIRETO DO BD
# ###################################################################################

@router.get("/settings/menu/sidebar-sections-data")
def get_sidebar_sections_data_v6(request: Request) -> JSONResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return JSONResponse(
                {"ok": False, "sections": [], "error": "Efetue login para continuar."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            from appverbo.menu_settings import (
                MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
                normalize_sidebar_sections,
            )

            raw_menu_config = session.execute(
                text(
                    """
                    SELECT menu_config
                    FROM sidebar_menu_settings
                    WHERE lower(trim(menu_key)) = :menu_key
                    LIMIT 1
                    """
                ),
                {"menu_key": "administrativo"},
            ).scalar_one_or_none()

            try:
                menu_config = json.loads(raw_menu_config or "{}")
            except (TypeError, ValueError):
                menu_config = {}

            if not isinstance(menu_config, dict):
                menu_config = {}

            sections = normalize_sidebar_sections(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
            )

            return JSONResponse(
                {
                    "ok": True,
                    "sections": sections,
                }
            )
        except Exception as exc:
            return JSONResponse(
                {
                    "ok": False,
                    "sections": [],
                    "error": str(exc),
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# APPVERBO_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_END


# APPVERBO_SESSOES_RETURN_URL_V17_START

# ###################################################################################
# (SIDEBAR_SECTION_RETURN_URL_V17) URL SEGURA DE RETORNO PARA A ABA SESSOES
# ###################################################################################

def _sanitize_sidebar_section_return_url_v17(return_url: object) -> str:
    raw_url = str(return_url or "").strip()

    if not raw_url:
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("//"):
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    if not raw_url.startswith("/users/new"):
        return "/users/new?menu=administrativo#admin-sidebar-sections-card"

    return raw_url

# APPVERBO_SESSOES_RETURN_URL_V17_END






# APPVERBO_SESSOES_SAVE_ONE_V19_START

# ###################################################################################
# (SIDEBAR_SECTION_SAVE_ONE_V19) CRIAR/EDITAR SESSAO COM ESTADO PERSISTENTE
# ###################################################################################

def _normalize_sidebar_section_text_v19(value: object) -> str:
    return str(value or "").strip()


def _slugify_sidebar_section_key_v19(value: object) -> str:
    import re
    import unicodedata

    raw_value = _normalize_sidebar_section_text_v19(value).lower()
    raw_value = unicodedata.normalize("NFD", raw_value)
    raw_value = "".join(char for char in raw_value if unicodedata.category(char) != "Mn")
    raw_value = re.sub(r"[^a-z0-9]+", "_", raw_value)
    raw_value = re.sub(r"_+", "_", raw_value).strip("_")

    if raw_value and raw_value[0].isdigit():
        raw_value = f"secao_{raw_value}"

    return raw_value or "nova_sessao"


def _normalize_sidebar_section_status_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v19(value).lower()

    if clean_value in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_status_label_v19(value: object) -> str:
    return "Inativo" if _normalize_sidebar_section_status_v19(value) == "inativo" else "Ativo"


def _normalize_sidebar_section_scope_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_text_v19(value).lower()

    if clean_value in {"owner", "legado"}:
        return clean_value

    return "all"


def _sidebar_section_scope_to_scopes_v19(value: object) -> list[str]:
    clean_value = _normalize_sidebar_section_scope_v19(value)

    if clean_value in {"owner", "legado"}:
        return [clean_value]

    return ["owner", "legado"]


def _sidebar_section_scope_label_v19(value: object) -> str:
    clean_value = _normalize_sidebar_section_scope_v19(value)

    if clean_value == "owner":
        return "Owner"

    if clean_value == "legado":
        return "Legado"

    return "Default"


def _sanitize_sidebar_section_return_url_v19(return_url: object) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    fallback = "/users/new?menu=sessoes&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
    raw_url = _normalize_sidebar_section_text_v19(return_url) or fallback

    if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("//"):
        raw_url = fallback

    if not raw_url.startswith("/users/new"):
        raw_url = fallback

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

    clean_params = []
    found_menu = False
    found_admin_tab = False
    found_sidebar_tab = False
    found_target = False

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
            clean_params.append(("target", "admin-sidebar-sections-card"))
            continue

        clean_params.append((key, value))

    if not found_menu:
        clean_params.append(("menu", "sessoes"))

    if not found_admin_tab:
        clean_params.append(("admin_tab", "sessoes"))

    if not found_sidebar_tab:
        clean_params.append(("sidebar_sections_tab", "sessoes"))

    if not found_target:
        clean_params.append(("target", "admin-sidebar-sections-card"))

    return urlunsplit(("", "", "/users/new", urlencode(clean_params), "admin-sidebar-sections-card"))


def _append_sidebar_section_message_v19(return_url: str, message_key: str, message: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(return_url)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]
    params.append((message_key, message))

    return urlunsplit(("", "", parts.path or "/users/new", urlencode(params), parts.fragment or "admin-sidebar-sections-card"))


def _redirect_sidebar_section_message_v19(
    return_url: str,
    message_key: str,
    message: str,
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(return_url)

    return RedirectResponse(
        url=_append_sidebar_section_message_v19(safe_return_url, message_key, message),
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _make_unique_sidebar_section_key_v19(base_key: str, used_keys: set[str]) -> str:
    clean_base_key = _slugify_sidebar_section_key_v19(base_key)

    if clean_base_key not in used_keys:
        return clean_base_key

    counter = 2
    candidate = f"{clean_base_key}_{counter}"

    while candidate in used_keys:
        counter += 1
        candidate = f"{clean_base_key}_{counter}"

    return candidate


def _read_sidebar_sections_for_save_one_v19(session) -> list[dict[str, str]]:
    from appverbo.menu_settings import (
        MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
        normalize_sidebar_sections,
    )

    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).scalar_one_or_none()

    try:
        menu_config = json.loads(raw_menu_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        menu_config = {}

    return normalize_sidebar_sections(
        menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )


def _persist_sidebar_sections_status_v19(
    session,
    payload_sections: list[dict[str, str]],
    target_section_key: str,
    target_status: str,
) -> None:
    from uuid import uuid4

    from appverbo.menu_settings import (
        MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY,
        MENU_CONFIG_SIDEBAR_SECTIONS_KEY,
    )

    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).scalar_one_or_none()

    try:
        menu_config = json.loads(raw_menu_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        menu_config = {}

    clean_target_key = _slugify_sidebar_section_key_v19(target_section_key)
    clean_target_status = _normalize_sidebar_section_status_v19(target_status)

    normalized_payload_sections = []

    for section in payload_sections:
        clean_key = _slugify_sidebar_section_key_v19(section.get("key"))
        clean_label = _normalize_sidebar_section_text_v19(section.get("label"))
        clean_scope = _normalize_sidebar_section_scope_v19(section.get("visibility_scope_mode"))
        clean_status = _normalize_sidebar_section_status_v19(section.get("status"))

        if clean_key == clean_target_key:
            clean_status = clean_target_status

        if not clean_label or not clean_key:
            continue

        normalized_payload_sections.append(
            {
                "key": clean_key,
                "label": clean_label,
                "visibility_scopes": _sidebar_section_scope_to_scopes_v19(clean_scope),
                "visibility_scope_mode": clean_scope,
                "visibility_scope_label": _sidebar_section_scope_label_v19(clean_scope),
                "status": clean_status,
                "is_active": clean_status == "ativo",
                "status_label": _sidebar_section_status_label_v19(clean_status),
            }
        )

    menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_payload_sections
    menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = str(uuid4())

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": "administrativo",
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()


@router.post("/settings/menu/sidebar-section-save", response_class=HTMLResponse)
def save_one_sidebar_section_v19(
    request: Request,
    section_mode: str = Form("create"),
    original_section_key: str = Form(""),
    section_label: str = Form(""),
    section_visibility_scope_mode: str = Form("all"),
    section_status: str = Form("ativo"),
    section_status_override_v19: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(sidebar_section_return_url)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas administradores podem alterar sessões do sidebar.",
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_mode = _normalize_sidebar_section_text_v19(section_mode).lower()
        clean_original_key = _slugify_sidebar_section_key_v19(original_section_key)
        clean_label = _normalize_sidebar_section_text_v19(section_label)
        clean_scope = _normalize_sidebar_section_scope_v19(section_visibility_scope_mode)

        effective_status = section_status_override_v19 or section_status
        clean_status = _normalize_sidebar_section_status_v19(effective_status)

        if not clean_label:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Informe o nome da sessão.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v19(session)
        payload_sections: list[dict[str, str]] = []
        target_section_key = clean_original_key

        if clean_mode == "edit":
            found_section = False

            for section in current_sections:
                section_key = _slugify_sidebar_section_key_v19(section.get("key"))

                if section_key == clean_original_key:
                    found_section = True
                    payload_sections.append(
                        {
                            "key": section_key,
                            "label": clean_label,
                            "visibility_scope_mode": clean_scope,
                            "status": clean_status,
                        }
                    )
                else:
                    payload_sections.append(
                        {
                            "key": section_key,
                            "label": _normalize_sidebar_section_text_v19(section.get("label")),
                            "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                                section.get("visibility_scope_mode")
                            ),
                            "status": _normalize_sidebar_section_status_v19(section.get("status")),
                        }
                    )

            if not found_section:
                return _redirect_sidebar_section_message_v19(
                    safe_return_url,
                    "error",
                    "Sessão não encontrada para edição.",
                )
        else:
            used_keys = {
                _slugify_sidebar_section_key_v19(section.get("key"))
                for section in current_sections
            }
            target_section_key = _make_unique_sidebar_section_key_v19(clean_label, used_keys)

            for section in current_sections:
                payload_sections.append(
                    {
                        "key": _slugify_sidebar_section_key_v19(section.get("key")),
                        "label": _normalize_sidebar_section_text_v19(section.get("label")),
                        "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                            section.get("visibility_scope_mode")
                        ),
                        "status": _normalize_sidebar_section_status_v19(section.get("status")),
                    }
                )

            payload_sections.append(
                {
                    "key": target_section_key,
                    "label": clean_label,
                    "visibility_scope_mode": clean_scope,
                    "status": clean_status,
                }
            )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Não foi possível gravar a sessão.",
            )

        _persist_sidebar_sections_status_v19(
            session=session,
            payload_sections=payload_sections,
            target_section_key=target_section_key,
            target_status=clean_status,
        )

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            (
                "Sessão atualizada com sucesso."
                if clean_mode == "edit"
                else "Sessão criada com sucesso."
            ),
        )

# APPVERBO_SESSOES_SAVE_ONE_V19_END


# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_START

# ###################################################################################
# (SIDEBAR_SECTION_MOVE_ONE_V25) MOVER SESSAO COM FLUXO SERVER-SIDE
# ###################################################################################

@router.post("/settings/menu/sidebar-section-move-one", response_class=HTMLResponse)
def move_one_sidebar_section_v25(
    request: Request,
    section_key: str = Form(""),
    direction: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(sidebar_section_return_url)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas administradores podem alterar sessões do sidebar.",
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_section_key = _slugify_sidebar_section_key_v19(section_key)
        clean_direction = str(direction or "").strip().lower()

        if clean_direction not in {"up", "down"}:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Direção inválida para mover a sessão.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v19(session)
        payload_sections: list[dict[str, str]] = []

        for section in current_sections:
            payload_sections.append(
                {
                    "key": _slugify_sidebar_section_key_v19(section.get("key")),
                    "label": _normalize_sidebar_section_text_v19(section.get("label")),
                    "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                        section.get("visibility_scope_mode")
                    ),
                    "status": _normalize_sidebar_section_status_v19(section.get("status")),
                }
            )

        current_index = next(
            (
                index
                for index, section in enumerate(payload_sections)
                if _slugify_sidebar_section_key_v19(section.get("key")) == clean_section_key
            ),
            -1,
        )

        if current_index < 0:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Sessão não encontrada para mover.",
            )

        target_index = current_index - 1 if clean_direction == "up" else current_index + 1

        if target_index < 0 or target_index >= len(payload_sections):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "success",
                "Sessão já está no limite da hierarquia.",
            )

        payload_sections[current_index], payload_sections[target_index] = (
            payload_sections[target_index],
            payload_sections[current_index],
        )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Não foi possível mover a sessão.",
            )

        target_status = payload_sections[target_index].get("status", "ativo")
        _persist_sidebar_sections_status_v19(
            session=session,
            payload_sections=payload_sections,
            target_section_key=clean_section_key,
            target_status=target_status,
        )

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            "Hierarquia da sessão atualizada com sucesso.",
        )

# APPVERBO_SESSOES_SERVER_MOVE_ONE_V25_END


# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_START

# ###################################################################################
# (SIDEBAR_SECTIONS_HANDLER_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################

@router.post("/settings/menu/sidebar-sections", response_class=HTMLResponse)
def edit_sidebar_sections_v2(
    request: Request,
    section_key: list[str] = Form(default=[]),
    section_label: list[str] = Form(default=[]),
    section_visibility_scope_mode: list[str] = Form(default=[]),
    section_status: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode alterar sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(section_key),
            len(section_label),
            len(section_visibility_scope_mode),
            len(section_status),
        )

        payload_sections: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_sections.append(
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

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível gravar as sessões do sidebar.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Sessões do sidebar e visibilidade dos menus atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key="administrativo",
                settings_action="edit",
                settings_tab="sessoes",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

# APPVERBO_SIDEBAR_SECTIONS_HANDLER_V2_END


# ###################################################################################
# (MENU_SETTINGS_CRUD_V1) GRAVAR CONFIGURACOES GERAIS DAS PASTAS
# ###################################################################################

@router.post("/settings/menu/edit", response_class=HTMLResponse)
def edit_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    menu_label: str = Form(...),
    menu_status: str = Form("ativo"),
    menu_visibility_scope: str = Form("all"),
    menu_sidebar_section: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)
    clean_status = str(menu_status or "").strip().lower()
    make_visible = clean_status not in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_edit_key=clean_menu_key,
            settings_action="edit",
            settings_tab="geral",
        )
        if blocked_response is not None:
            return blocked_response

        if not make_visible:
            ok, error_message = set_sidebar_menu_visibility(
                session,
                clean_menu_key,
                False,
            )
            if not ok:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message=error_message or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        _session_entity_id = get_session_entity_id(request)
        _session_entity = get_entity_by_id(session, _session_entity_id) if _session_entity_id is not None else None
        _session_entity_number = _session_entity.entity_number if _session_entity is not None else None

        ok, error_message = update_sidebar_menu_label(
            session,
            clean_menu_key,
            menu_label,
            menu_visibility_scope,
            menu_sidebar_section,
            entity_number=_session_entity_number,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar o menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="geral",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        if make_visible:
            ok, error_message = set_sidebar_menu_visibility(
                session,
                clean_menu_key,
                True,
            )
            if not ok:
                return RedirectResponse(
                    url=_build_settings_redirect_url(
                        error_message=error_message or "Não foi possível atualizar o estado do menu.",
                        redirect_menu=redirect_menu,
                        redirect_target=redirect_target,
                        settings_edit_key=clean_menu_key,
                        settings_action="edit",
                        settings_tab="geral",
                    ),
                    status_code=HTTP_303_SEE_OTHER,
                )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Menu atualizado com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="geral",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/create", response_class=HTMLResponse)
def create_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_label: str = Form(...),
    menu_visibility_scope: str = Form("all"),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_action="create",
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message, new_menu_key = create_sidebar_menu_setting(
            session,
            menu_label,
            menu_visibility_scope,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível criar a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Pasta criada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=(
                    new_menu_key
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
                settings_action=(
                    "edit"
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
                settings_tab=(
                    "geral"
                    if str(redirect_target or "").lstrip("#") == "settings-menu-edit-card"
                    else ""
                ),
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/move", response_class=HTMLResponse)
def move_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message = move_sidebar_menu_setting(
            session,
            clean_menu_key,
            direction,
        )
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível mover a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Ordem da pasta atualizada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/delete", response_class=HTMLResponse)
def delete_sidebar_menu_setting_handler_v1(
    request: Request,
    menu_key: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#admin-account-status-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
        )
        if blocked_response is not None:
            return blocked_response

        ok, error_message = delete_sidebar_menu_setting(session, clean_menu_key)
        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível eliminar a pasta.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Pasta eliminada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/field-move", response_class=HTMLResponse)
def move_sidebar_menu_additional_field_handler(
    request: Request,
    menu_key: str = Form(...),
    field_key: str = Form(...),
    direction: str = Form(...),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem mover campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode mover campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        ok, error_message = move_sidebar_menu_additional_field(
            session,
            clean_menu_key,
            field_key,
            direction,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível mover o campo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campo movido com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-adicionais",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )




# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_START

# ###################################################################################
# (PRESERVE_HEADER_ASSIGNMENTS_V1) PRESERVAR ATRIBUICAO CAMPO -> CABECALHO
# ###################################################################################

def _normalize_menu_key_local_v1(value: object) -> str:
    return str(value or "").strip().lower()


def _read_sidebar_menu_config_v1(session, menu_key: str) -> dict:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()

    if not raw_config:
        return {}

    try:
        parsed_config = json.loads(raw_config)
    except (TypeError, ValueError):
        return {}

    return parsed_config if isinstance(parsed_config, dict) else {}


def _write_sidebar_menu_config_v1(session, menu_key: str, menu_config: dict) -> None:
    clean_menu_key = _normalize_menu_key_local_v1(menu_key)

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )


def _get_header_assignments_from_config_v1(menu_config: dict) -> dict[str, str]:
    assignments: dict[str, str] = {}

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))
            header_key = _normalize_menu_key_local_v1(raw_row.get("header_key"))

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    raw_header_map = menu_config.get("process_visible_field_header_map")
    if isinstance(raw_header_map, dict):
        for raw_field_key, raw_header_key in raw_header_map.items():
            field_key = _normalize_menu_key_local_v1(raw_field_key)
            header_key = _normalize_menu_key_local_v1(raw_header_key)

            if not field_key or not header_key:
                continue

            assignments[field_key] = header_key

    return assignments


def _get_header_keys_from_config_v1(menu_config: dict) -> set[str]:
    header_keys: set[str] = set()

    raw_fields = menu_config.get("additional_fields")
    if not isinstance(raw_fields, list):
        return header_keys

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        field_key = _normalize_menu_key_local_v1(raw_field.get("key"))
        field_type = _normalize_menu_key_local_v1(raw_field.get("field_type") or raw_field.get("type"))

        if field_key and field_type == "header":
            header_keys.add(field_key)

    return header_keys


def _get_visible_fields_from_config_v1(menu_config: dict) -> list[str]:
    visible_fields: list[str] = []
    seen_fields: set[str] = set()

    raw_visible_fields = menu_config.get("process_visible_fields")
    if isinstance(raw_visible_fields, list):
        for raw_field_key in raw_visible_fields:
            field_key = _normalize_menu_key_local_v1(raw_field_key)

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    raw_rows = menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue

            field_key = _normalize_menu_key_local_v1(raw_row.get("field_key"))

            if not field_key or field_key in seen_fields:
                continue

            seen_fields.add(field_key)
            visible_fields.append(field_key)

    return visible_fields


def _restore_menu_header_assignments_after_additional_fields_v1(
    session,
    menu_key: str,
    old_menu_config: dict,
) -> None:
    old_assignments = _get_header_assignments_from_config_v1(old_menu_config)

    if not old_assignments:
        return

    current_config = _read_sidebar_menu_config_v1(session, menu_key)
    if not current_config:
        return

    current_header_keys = _get_header_keys_from_config_v1(current_config)
    current_visible_fields = _get_visible_fields_from_config_v1(current_config)

    if not current_visible_fields:
        return

    restored_header_map: dict[str, str] = {}
    restored_rows: list[dict[str, str]] = []

    for field_key in current_visible_fields:
        if field_key in current_header_keys:
            continue

        header_key = old_assignments.get(field_key, "")
        if header_key not in current_header_keys:
            header_key = ""

        if header_key:
            restored_header_map[field_key] = header_key

        restored_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    current_config["process_visible_field_header_map"] = restored_header_map
    current_config["process_visible_field_rows"] = restored_rows

    _write_sidebar_menu_config_v1(session, menu_key, current_config)
    session.commit()


def _update_sidebar_menu_additional_fields_preserve_headers_v1(
    session,
    menu_key: str,
    payload_fields: list[dict[str, str]],
) -> tuple[bool, str]:
    old_menu_config = _read_sidebar_menu_config_v1(session, menu_key)

    ok, error_message = update_sidebar_menu_additional_fields_v1(
        session,
        menu_key,
        payload_fields,
    )

    if not ok:
        return ok, error_message

    _restore_menu_header_assignments_after_additional_fields_v1(
        session,
        menu_key,
        old_menu_config,
    )

    return ok, error_message

# APPVERBO_PRESERVE_HEADER_ASSIGNMENTS_V1_END


@router.post("/settings/menu/process-additional-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_additional_fields_v1(
    request: Request,
    menu_key: str = Form(...),
    additional_field_key: list[str] = Form(default=[]),
    additional_field_label: list[str] = Form(default=[]),
    additional_field_type: list[str] = Form(default=[]),
    additional_field_required: list[str] = Form(default=[]),
    additional_field_size: list[str] = Form(default=[]),
    additional_field_list_key: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos adicionais por processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(additional_field_key),
            len(additional_field_label),
            len(additional_field_type),
            len(additional_field_required),
            len(additional_field_size),
            len(additional_field_list_key),
        )

        payload_fields: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_fields.append(
                {
                    "key": additional_field_key[row_index] if row_index < len(additional_field_key) else "",
                    "label": additional_field_label[row_index] if row_index < len(additional_field_label) else "",
                    "field_type": additional_field_type[row_index] if row_index < len(additional_field_type) else "",
                    "is_required": additional_field_required[row_index] if row_index < len(additional_field_required) else "",
                    "size": additional_field_size[row_index] if row_index < len(additional_field_size) else "",
                    "list_key": additional_field_list_key[row_index] if row_index < len(additional_field_list_key) else "",
                }
            )

        ok, error_message = _update_sidebar_menu_additional_fields_preserve_headers_v1(
            session,
            clean_menu_key,
            payload_fields,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos adicionais do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-adicionais",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos adicionais e hierarquia do processo atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-adicionais",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    visible_fields: list[str] = Form(default=[]),
    visible_headers: list[str] = Form(default=[]),
    visible_rows_json: str = Form(""),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar definições do menu.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )





        # APPVERBO_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_START
        clean_visible_fields: list[str] = []
        clean_visible_headers: list[str] = []
        seen_visible_fields: set[str] = set()

        raw_rows_json_text = str(visible_rows_json or "").strip()

        if raw_rows_json_text:
            try:
                parsed_visible_rows = json.loads(raw_rows_json_text)
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed_visible_rows = []
        else:
            parsed_visible_rows = []

        if isinstance(parsed_visible_rows, list):
            for raw_row in parsed_visible_rows:
                if not isinstance(raw_row, dict):
                    continue

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

                if not field_key:
                    continue

                if field_key in seen_visible_fields:
                    continue

                seen_visible_fields.add(field_key)
                clean_visible_fields.append(field_key)
                clean_visible_headers.append(header_key)

        if not clean_visible_fields:
            raw_visible_fields_list = list(visible_fields or [])
            raw_visible_headers_list = list(visible_headers or [])

            for row_index, raw_field_key in enumerate(raw_visible_fields_list):
                field_key = str(raw_field_key or "").strip().lower()

                if not field_key:
                    continue

                if field_key in seen_visible_fields:
                    continue

                raw_header_key = (
                    raw_visible_headers_list[row_index]
                    if row_index < len(raw_visible_headers_list)
                    else ""
                )
                header_key = str(raw_header_key or "").strip().lower()

                seen_visible_fields.add(field_key)
                clean_visible_fields.append(field_key)
                clean_visible_headers.append(header_key)
        # APPVERBO_PROCESS_FIELDS_HEADER_ROWS_JSON_V4_END

        ok, error_message = update_sidebar_menu_process_fields(
            session=session,
            menu_key=clean_menu_key,
            visible_fields=clean_visible_fields,
            visible_headers=clean_visible_headers,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar a configuração dos campos.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-config",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Configuração dos campos atualizada com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-config",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-quantity-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_quantity_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    quantity_rule_key: list[str] = Form(default=[]),
    quantity_rule_label: list[str] = Form(default=[]),
    quantity_field_key: list[str] = Form(default=[]),
    quantity_repeated_field_keys_json: list[str] = Form(default=[]),
    quantity_header_key: list[str] = Form(default=[]),
    quantity_max_items: list[str] = Form(default=[]),
    quantity_item_label: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        blocked_response = _require_menu_settings_owner_v1(
            session,
            request,
            redirect_menu,
            redirect_target,
            settings_edit_key=clean_menu_key,
            settings_action="edit",
            settings_tab="campos-quantidade",
        )
        if blocked_response is not None:
            return blocked_response

        rows_count = max(
            len(quantity_rule_key),
            len(quantity_rule_label),
            len(quantity_field_key),
            len(quantity_repeated_field_keys_json),
            len(quantity_header_key),
            len(quantity_max_items),
            len(quantity_item_label),
        )

        payload_rules: list[dict[str, str]] = []
        for row_index in range(rows_count):
            payload_rules.append(
                {
                    "key": quantity_rule_key[row_index] if row_index < len(quantity_rule_key) else "",
                    "label": quantity_rule_label[row_index] if row_index < len(quantity_rule_label) else "",
                    "quantity_field_key": quantity_field_key[row_index] if row_index < len(quantity_field_key) else "",
                    "repeated_field_keys": (
                        quantity_repeated_field_keys_json[row_index]
                        if row_index < len(quantity_repeated_field_keys_json)
                        else ""
                    ),
                    "header_key": quantity_header_key[row_index] if row_index < len(quantity_header_key) else "",
                    "max_items": quantity_max_items[row_index] if row_index < len(quantity_max_items) else "",
                    "item_label": quantity_item_label[row_index] if row_index < len(quantity_item_label) else "",
                }
            )

        ok, error_message = update_sidebar_menu_process_quantity_fields_v1(
            session=session,
            menu_key=clean_menu_key,
            raw_fields=payload_rules,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "NÃ£o foi possÃ­vel atualizar os Campos Quantidade.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos-quantidade",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos Quantidade atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos-quantidade",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.post("/settings/menu/process-lists", response_class=HTMLResponse)
def edit_sidebar_menu_process_lists_handler(
    request: Request,
    menu_key: str = Form(...),
    process_list_key: list[str] = Form(default=[]),
    process_list_label: list[str] = Form(default=[]),
    process_list_items_csv: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(process_list_key),
            len(process_list_label),
            len(process_list_items_csv),
        )

        payload_lists: list[dict[str, str]] = []

        for row_index in range(rows_count):
            label = process_list_label[row_index] if row_index < len(process_list_label) else ""
            items_csv = (
                process_list_items_csv[row_index]
                if row_index < len(process_list_items_csv)
                else ""
            )

            if not str(label or "").strip() and not str(items_csv or "").strip():
                continue

            payload_lists.append(
                {
                    "key": process_list_key[row_index] if row_index < len(process_list_key) else "",
                    "label": label,
                    "items_csv": items_csv,
                }
            )

        ok, error_message = update_sidebar_menu_process_lists(
            session=session,
            menu_key=clean_menu_key,
            raw_lists=payload_lists,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar as listas do processo.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="lista",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Listas do processo atualizadas com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="lista",
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )


# ###################################################################################
# (4) CAMPOS SUBSEQUENTES - V1
# ###################################################################################

@router.post("/settings/menu/process-subsequent-fields", response_class=HTMLResponse)
def edit_sidebar_menu_process_subsequent_fields_handler(
    request: Request,
    menu_key: str = Form(...),
    subsequent_field_key: list[str] = Form(default=[]),
    subsequent_trigger_field: list[str] = Form(default=[]),
    subsequent_field: list[str] = Form(default=[]),
    subsequent_operator: list[str] = Form(default=[]),
    subsequent_trigger_value: list[str] = Form(default=[]),
    redirect_menu: str = Form("administrativo"),
    redirect_target: str = Form("#settings-menu-edit-card"),
) -> RedirectResponse:
    clean_menu_key = resolve_menu_key_alias(menu_key)

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas administradores podem alterar campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        selected_entity_id = get_session_entity_id(request)
        permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )

        if not permissions["can_manage_all_entities"]:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Apenas Owner pode configurar campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        rows_count = max(
            len(subsequent_field_key),
            len(subsequent_trigger_field),
            len(subsequent_field),
            len(subsequent_operator),
            len(subsequent_trigger_value),
        )

        payload_fields: list[dict[str, str]] = []

        for row_index in range(rows_count):
            if row_index < len(subsequent_trigger_field) and row_index < len(subsequent_field):
                payload_fields.append(
                    {
                        "key": subsequent_field_key[row_index] if row_index < len(subsequent_field_key) else "",
                        "trigger_field": subsequent_trigger_field[row_index] if row_index < len(subsequent_trigger_field) else "",
                        "field_key": subsequent_field[row_index] if row_index < len(subsequent_field) else "",
                        "operator": subsequent_operator[row_index] if row_index < len(subsequent_operator) else "",
                        "trigger_value": subsequent_trigger_value[row_index] if row_index < len(subsequent_trigger_value) else "",
                    }
                )

        ok, error_message = update_sidebar_menu_subsequent_fields(
            session,
            clean_menu_key,
            payload_fields,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message or "Não foi possível atualizar os campos subsequentes.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key=clean_menu_key,
                    settings_action="edit",
                    settings_tab="campos_subsequentes",
                ),
                status_code=HTTP_303_SEE_OTHER,
            )

        return RedirectResponse(
            url=_build_settings_redirect_url(
                success_message="Campos subsequentes atualizados com sucesso.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=clean_menu_key,
                settings_action="edit",
                settings_tab="campos_subsequentes",
            ),
            status_code=HTTP_303_SEE_OTHER,
        )
