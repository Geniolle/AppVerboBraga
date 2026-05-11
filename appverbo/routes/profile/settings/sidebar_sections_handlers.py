from __future__ import annotations

import json

from fastapi import Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import text

from appverbo.core import SessionLocal
from appverbo.menu_settings import (
    get_sidebar_global_refresh_version_v1,
    update_sidebar_sections_v2,
)
from appverbo.routes.profile.router import router
from appverbo.routes.profile.settings.redirects import build_settings_redirect_url_v1
from appverbo.services.auth import is_admin_user
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.services.session import get_current_user, get_session_entity_id
from appverbo.menu_settings import *  # noqa: F403,F401


####################################################################################
# (1) ALIAS TEMPORÁRIO PARA COMPATIBILIDADE COM O CÓDIGO MIGRADO
####################################################################################

_build_settings_redirect_url = build_settings_redirect_url_v1


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

    return "Owner e Legado"


def _sanitize_sidebar_section_return_url_v19(return_url: object) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    fallback = "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
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
            clean_params.append(("menu", "administrativo"))
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
        clean_params.append(("menu", "administrativo"))

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
    key: str = Form(""),
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

        clean_section_key = _slugify_sidebar_section_key_v19(section_key or key)
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

        # APPVERBO_SESSOES_HIERARQUIA_SETAS_V1_START
        # Move apenas dentro do mesmo grupo visual da tabela.
        # Na tela atual as setas aparecem nas sessões ativas; se houver sessões
        # inativas intercaladas no JSON, trocar com a próxima linha física pode
        # não alterar a ordem visível. Por isso procuramos o próximo item com o
        # mesmo estado da sessão clicada.
        current_status = _normalize_sidebar_section_status_v19(
            payload_sections[current_index].get("status")
        )

        if clean_direction == "up":
            target_index = next(
                (
                    index
                    for index in range(current_index - 1, -1, -1)
                    if _normalize_sidebar_section_status_v19(
                        payload_sections[index].get("status")
                    ) == current_status
                ),
                -1,
            )
        else:
            target_index = next(
                (
                    index
                    for index in range(current_index + 1, len(payload_sections))
                    if _normalize_sidebar_section_status_v19(
                        payload_sections[index].get("status")
                    ) == current_status
                ),
                -1,
            )

        if target_index < 0:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "success",
                "Sessão já está no limite da hierarquia.",
            )

        payload_sections[current_index], payload_sections[target_index] = (
            payload_sections[target_index],
            payload_sections[current_index],
        )
        # APPVERBO_SESSOES_HIERARQUIA_SETAS_V1_END

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

# APPVERBO_REMAINING_ROUTES_SIDEBAR_SECTIONS_V1_START

# APPVERBO_SESSOES_SERVER_DELETE_ONE_V26_START

# ###################################################################################
# (SIDEBAR_SECTION_DELETE_ONE_V26) ELIMINAR SESSAO COM FLUXO SERVER-SIDE
# ###################################################################################

@router.post("/settings/menu/sidebar-section-delete-one", response_class=HTMLResponse)
def delete_one_sidebar_section_v26(
    request: Request,
    section_key: str = Form(""),
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
                "Apenas administradores podem alterar sessoes do sidebar.",
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
                "Apenas Owner pode alterar sessoes do sidebar.",
            )

        clean_section_key = _slugify_sidebar_section_key_v19(section_key)
        if not clean_section_key:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Sessao invalida para eliminar.",
            )

        if clean_section_key in SIDEBAR_SECTION_DEFAULTS_BY_KEY:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Nao e permitido eliminar sessoes padrao do sistema.",
            )

        current_sections = _read_sidebar_sections_for_save_one_v19(session)
        payload_sections: list[dict[str, str]] = []
        found_section = False

        for section in current_sections:
            normalized_key = _slugify_sidebar_section_key_v19(section.get("key"))
            if normalized_key == clean_section_key:
                found_section = True
                continue
            payload_sections.append(
                {
                    "key": normalized_key,
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
                "Sessao nao encontrada para eliminar.",
            )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Nao foi possivel eliminar a sessao.",
            )

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            "Sessao eliminada com sucesso.",
        )

# APPVERBO_REMAINING_ROUTES_SIDEBAR_SECTIONS_V1_END
