import json
from fastapi import (
    Request,
    Form,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from sqlalchemy import text
from appgenesis.routes.profile.router import router
from appgenesis.menu_settings import (
    delete_sidebar_section,
    update_sidebar_sections_v2,
    get_sidebar_global_refresh_version_v1,
)
from appgenesis.db.session import SessionLocal
from appgenesis.services.session import get_current_user
from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions
from appgenesis.services.session import get_session_entity_id
from appgenesis.services.sidebar_section_ownership import (
    can_manage_section,
    is_section_visible_to_entity,
    load_section_owner_map_v1,
    resolve_entity_number_v1,
    set_section_creator_v1,
    set_section_owner_v1,
)
from appgenesis.routes.profile.process_settings.common import _build_settings_redirect_url


# APPGENESIS_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_START

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

# APPGENESIS_SIDEBAR_GLOBAL_REFRESH_ENDPOINT_V1_END

# APPGENESIS_SIDEBAR_SECTIONS_DATA_ENDPOINT_V6_START

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
            from appgenesis.menu_settings import (
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

# APPGENESIS_SESSOES_RETURN_URL_V17_END

# APPGENESIS_SESSOES_SAVE_ONE_V19_START

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
    raw_value = "".join(
        char for char in raw_value if unicodedata.category(char) != "Mn"
    )
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
    return (
        "Inativo"
        if _normalize_sidebar_section_status_v19(value) == "inativo"
        else "Ativo"
    )

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

    if (
        raw_url.startswith("http://")
        or raw_url.startswith("https://")
        or raw_url.startswith("//")
    ):
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
        "appgenesis_after_save",
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

    sanitized = urlunsplit(
        ("", "", "/users/new", urlencode(clean_params), "admin-sidebar-sections-card")
    )

    return sanitized

def _append_sidebar_section_message_v19(
    return_url: str, message_key: str, message: str
) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(return_url)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]
    params.append((message_key, message))

    final_url = urlunsplit(
        (
            "",
            "",
            parts.path or "/users/new",
            urlencode(params),
            parts.fragment or "admin-sidebar-sections-card",
        )
    )

    return final_url

def _redirect_sidebar_section_message_v19(
    return_url: str,
    message_key: str,
    message: str,
    after_save: bool = False,
) -> RedirectResponse:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    safe_return_url = _sanitize_sidebar_section_return_url_v19(return_url)
    url = _append_sidebar_section_message_v19(safe_return_url, message_key, message)

    if after_save:
        parts = urlsplit(url)
        params = list(parse_qsl(parts.query, keep_blank_values=True))
        params.append(("appgenesis_after_save", "1"))
        url = urlunsplit(
            (
                "",
                "",
                parts.path or "/users/new",
                urlencode(params),
                parts.fragment or "admin-sidebar-sections-card",
            )
        )

    return RedirectResponse(
        url=url,
        status_code=status.HTTP_303_SEE_OTHER,
    )

def _redirect_sidebar_section_edit_error_v19(
    original_key: str, error: str
) -> RedirectResponse:
    from urllib.parse import urlencode, urlunsplit

    params = [
        ("menu", "sessoes"),
        ("admin_tab", "sessoes"),
        ("sidebar_sections_tab", "sessoes"),
        ("target", "admin-sidebar-sections-form-card"),
        ("sidebar_section_edit_key", original_key),
        ("error", error),
    ]
    url = urlunsplit(
        ("", "", "/users/new", urlencode(params), "admin-sidebar-sections-form-card")
    )
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

def _build_sidebar_sections_success_url_v1(message: str = "") -> str:
    """URL de sucesso pós-save de Sessões — sempre limpa, sem estado de edição."""
    from urllib.parse import urlencode, urlunsplit

    params = [
        ("menu", "sessoes"),
        ("admin_tab", "sessoes"),
        ("sidebar_sections_tab", "sessoes"),
        ("target", "admin-sidebar-sections-card"),
        ("appgenesis_after_save", "1"),
    ]
    if message:
        params.append(("success", message))
    return urlunsplit(
        ("", "", "/users/new", urlencode(params), "admin-sidebar-sections-card")
    )

def _is_sidebar_section_ajax_request_v1(request: Request) -> bool:
    requested_with = str(request.headers.get("X-Requested-With") or "").strip()

    if requested_with == "XMLHttpRequest":
        return True

    accept = str(request.headers.get("Accept") or "").strip().lower()
    return "application/json" in accept

def _sidebar_section_forbidden_message_v1(owner_map: dict[str, int], section_key: str) -> str:
    if section_key in owner_map:
        return "Apenas a entidade criadora pode alterar esta sessão."
    return "Apenas Owner pode alterar sessões do sidebar."


def _sidebar_section_json_error_v1(
    message: str,
    *,
    status_code: int,
    redirect_url: str = "",
) -> JSONResponse:
    payload = {
        "ok": False,
        "message": message,
        "error": message,
    }

    if redirect_url:
        payload["redirect_url"] = redirect_url

    return JSONResponse(payload, status_code=status_code)

def _sidebar_section_json_success_v1(message: str, redirect_url: str) -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "message": message,
            "redirect_url": redirect_url,
        }
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
    from appgenesis.menu_settings import (
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

    return normalize_sidebar_sections(menu_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY))

def _persist_sidebar_sections_status_v19(
    session,
    payload_sections: list[dict[str, str]],
    target_section_key: str,
    target_status: str,
) -> None:
    from uuid import uuid4

    from appgenesis.menu_settings import (
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
        clean_scope = _normalize_sidebar_section_scope_v19(
            section.get("visibility_scope_mode")
        )
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
    _is_ajax = _is_sidebar_section_ajax_request_v1(request)

    safe_return_url = _sanitize_sidebar_section_return_url_v19(
        sidebar_section_return_url
    )

    with SessionLocal() as session:
        current_user = get_current_user(request, session)

        if current_user is None:
            if _is_ajax:
                return _sidebar_section_json_error_v1(
                    "Efetue login para continuar.",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    redirect_url="/login?error=Efetue login para continuar.",
                )
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )

        if not is_admin_user(session, current_user["id"], current_user["login_email"]):
            if _is_ajax:
                return _sidebar_section_json_error_v1(
                    "Apenas administradores podem alterar sessões do sidebar.",
                    status_code=status.HTTP_403_FORBIDDEN,
                    redirect_url=safe_return_url,
                )
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
        is_tenant_owner = bool(
            permissions.get(
                "can_manage_tenant_structure",
                permissions.get("can_manage_all_entities", False),
            )
        )
        actor_entity_number = resolve_entity_number_v1(session, selected_entity_id)

        # Owner gere sessoes de sistema; entidade legado cria e gere as suas.
        if not is_tenant_owner and actor_entity_number is None:
            if _is_ajax:
                return _sidebar_section_json_error_v1(
                    "Apenas Owner pode alterar sessões do sidebar.",
                    status_code=status.HTTP_403_FORBIDDEN,
                    redirect_url=safe_return_url,
                )
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_mode = _normalize_sidebar_section_text_v19(section_mode).lower()
        clean_original_key = _slugify_sidebar_section_key_v19(original_section_key)
        clean_label = _normalize_sidebar_section_text_v19(section_label)
        clean_scope = _normalize_sidebar_section_scope_v19(
            section_visibility_scope_mode
        )
        if not is_tenant_owner:
            # Sessao de legado e sempre do tipo Legado (sem Default).
            clean_scope = "legado"

        if clean_mode == "edit" and clean_original_key:
            owner_map = load_section_owner_map_v1(session)
            if not can_manage_section(
                owner_map, clean_original_key, actor_entity_number, is_tenant_owner
            ):
                forbidden_message = _sidebar_section_forbidden_message_v1(
                    owner_map, clean_original_key
                )
                if _is_ajax:
                    return _sidebar_section_json_error_v1(
                        forbidden_message,
                        status_code=status.HTTP_403_FORBIDDEN,
                        redirect_url=safe_return_url,
                    )
                return _redirect_sidebar_section_message_v19(
                    safe_return_url,
                    "error",
                    forbidden_message,
                )

        effective_status = section_status_override_v19 or section_status
        clean_status = _normalize_sidebar_section_status_v19(effective_status)

        if not clean_label:
            if clean_mode == "edit" and clean_original_key:
                if _is_ajax:
                    return _sidebar_section_json_error_v1(
                        "Informe o nome da sessão.",
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    )
                return _redirect_sidebar_section_edit_error_v19(
                    clean_original_key, "Informe o nome da sessão."
                )
            if _is_ajax:
                return _sidebar_section_json_error_v1(
                    "Informe o nome da sessão.",
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
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
                            "label": _normalize_sidebar_section_text_v19(
                                section.get("label")
                            ),
                            "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                                section.get("visibility_scope_mode")
                            ),
                            "status": _normalize_sidebar_section_status_v19(
                                section.get("status")
                            ),
                        }
                    )

            if not found_section:
                if _is_ajax:
                    return _sidebar_section_json_error_v1(
                        "Sessão não encontrada para edição.",
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    )
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
            target_section_key = _make_unique_sidebar_section_key_v19(
                clean_label, used_keys
            )

            for section in current_sections:
                payload_sections.append(
                    {
                        "key": _slugify_sidebar_section_key_v19(section.get("key")),
                        "label": _normalize_sidebar_section_text_v19(
                            section.get("label")
                        ),
                        "visibility_scope_mode": _normalize_sidebar_section_scope_v19(
                            section.get("visibility_scope_mode")
                        ),
                        "status": _normalize_sidebar_section_status_v19(
                            section.get("status")
                        ),
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
            if clean_mode == "edit" and clean_original_key:
                if _is_ajax:
                    return _sidebar_section_json_error_v1(
                        error_message or "Não foi possível gravar a sessão.",
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    )
                return _redirect_sidebar_section_edit_error_v19(
                    clean_original_key,
                    error_message or "Não foi possível gravar a sessão.",
                )
            if _is_ajax:
                return _sidebar_section_json_error_v1(
                    error_message or "Não foi possível gravar a sessão.",
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                )
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

        if not is_tenant_owner and clean_mode != "edit":
            set_section_owner_v1(session, target_section_key, actor_entity_number)
        if clean_mode != "edit":
            set_section_creator_v1(session, target_section_key, actor_entity_number)

        _success_msg = (
            "Sessão atualizada com sucesso."
            if clean_mode == "edit"
            else "Sessão criada com sucesso."
        )
        _success_url = _build_sidebar_sections_success_url_v1(_success_msg)

        if _is_ajax:
            return _sidebar_section_json_success_v1(_success_msg, _success_url)

        return RedirectResponse(url=_success_url, status_code=status.HTTP_303_SEE_OTHER)

# APPGENESIS_SESSOES_SAVE_ONE_V19_END

# APPGENESIS_SESSOES_SERVER_MOVE_ONE_V25_START

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
    safe_return_url = _sanitize_sidebar_section_return_url_v19(
        sidebar_section_return_url
    )

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
        is_tenant_owner = bool(
            permissions.get(
                "can_manage_tenant_structure",
                permissions.get("can_manage_all_entities", False),
            )
        )
        actor_entity_number = resolve_entity_number_v1(session, selected_entity_id)

        if not is_tenant_owner and actor_entity_number is None:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_section_key = _slugify_sidebar_section_key_v19(section_key)
        owner_map = load_section_owner_map_v1(session)
        if not can_manage_section(
            owner_map, clean_section_key, actor_entity_number, is_tenant_owner
        ):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                _sidebar_section_forbidden_message_v1(owner_map, clean_section_key),
            )

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
                    "status": _normalize_sidebar_section_status_v19(
                        section.get("status")
                    ),
                }
            )

        current_index = next(
            (
                index
                for index, section in enumerate(payload_sections)
                if _slugify_sidebar_section_key_v19(section.get("key"))
                == clean_section_key
            ),
            -1,
        )

        if current_index < 0:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Sessão não encontrada para mover.",
            )

        target_index = (
            current_index - 1 if clean_direction == "up" else current_index + 1
        )

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

# APPGENESIS_SESSOES_SERVER_MOVE_ONE_V25_END

# APPGENESIS_SESSOES_SERVER_DELETE_ONE_V1_START

# ###################################################################################
# (SIDEBAR_SECTION_DELETE_ONE_V1) ELIMINAR SESSAO INATIVA COM VALIDACAO DE OWNER
# ###################################################################################

@router.post("/settings/menu/sidebar-section-delete", response_class=HTMLResponse)
def delete_one_sidebar_section_v1(
    request: Request,
    section_key: str = Form(""),
    sidebar_section_return_url: str = Form(""),
) -> RedirectResponse:
    safe_return_url = _sanitize_sidebar_section_return_url_v19(
        sidebar_section_return_url
    )

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
        is_tenant_owner = bool(
            permissions.get(
                "can_manage_tenant_structure",
                permissions.get("can_manage_all_entities", False),
            )
        )
        actor_entity_number = resolve_entity_number_v1(session, selected_entity_id)

        if not is_tenant_owner and actor_entity_number is None:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                "Apenas Owner pode alterar sessões do sidebar.",
            )

        clean_section_key = _slugify_sidebar_section_key_v19(section_key)
        owner_map = load_section_owner_map_v1(session)
        if not can_manage_section(
            owner_map, clean_section_key, actor_entity_number, is_tenant_owner
        ):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                _sidebar_section_forbidden_message_v1(owner_map, clean_section_key),
            )

        ok, error_message = delete_sidebar_section(session, clean_section_key)

        if not ok:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "error",
                error_message or "Não foi possível eliminar a sessão.",
            )

        set_section_owner_v1(session, clean_section_key, None)
        set_section_creator_v1(session, clean_section_key, None)

        return _redirect_sidebar_section_message_v19(
            safe_return_url,
            "success",
            "Sessão eliminada com sucesso.",
        )

# APPGENESIS_SESSOES_SERVER_DELETE_ONE_V1_END

# APPGENESIS_SIDEBAR_SECTIONS_HANDLER_V2_START

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
        actor_entity_number = resolve_entity_number_v1(session, selected_entity_id)

        # Edicao em lote so para o Owner; entidade legado edita cada sessao (Editar).
        if not permissions.get(
            "can_manage_tenant_structure",
            permissions.get("can_manage_all_entities", False),
        ):
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

        # Pedido sem linhas (formulario vazio/truncado) apagaria todas as sessoes do owner.
        if rows_count == 0:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message="Nenhuma sessão enviada; nada foi alterado.",
                    redirect_menu=redirect_menu,
                    redirect_target=redirect_target,
                    settings_edit_key="administrativo",
                    settings_action="edit",
                    settings_tab="sessoes",
                ),
                status_code=status.HTTP_303_SEE_OTHER,
            )

        payload_sections: list[dict[str, str]] = []

        for row_index in range(rows_count):
            payload_sections.append(
                {
                    "key": section_key[row_index]
                    if row_index < len(section_key)
                    else "",
                    "label": section_label[row_index]
                    if row_index < len(section_label)
                    else "",
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

        # Sessoes de legado que o Owner nao ve nao entram na tabela: mantem-se como estao.
        owner_map = load_section_owner_map_v1(session)
        for current_section in _read_sidebar_sections_for_save_one_v19(session):
            if not is_section_visible_to_entity(
                owner_map, current_section.get("key"), actor_entity_number
            ):
                payload_sections.append(
                    {
                        "key": current_section.get("key"),
                        "label": current_section.get("label"),
                        "visibility_scope_mode": current_section.get("visibility_scope_mode"),
                        "status": current_section.get("status"),
                    }
                )

        ok, error_message = update_sidebar_sections_v2(
            session,
            payload_sections,
        )

        if not ok:
            return RedirectResponse(
                url=_build_settings_redirect_url(
                    error_message=error_message
                    or "Não foi possível gravar as sessões do sidebar.",
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
