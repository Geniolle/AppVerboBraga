# ###################################################################################
# HELPERS PARTILHADOS PELOS HANDLERS DE PROCESS-SETTINGS (Fase 8)
# ###################################################################################

import logging as _logging_sessoes
import os as _os_sessoes
from urllib.parse import parse_qsl, urlencode, urlsplit

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER

from appgenesis.services.session import get_current_user, get_session_entity_id
from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions

# APPGENESIS_DEBUG_PROCESS_EDITOR_FLOW_V1_START
_PROCESS_EDITOR_FLOW_LOGGER = _logging_sessoes.getLogger(__name__ + ".process_editor")


def _debug_process_editor_flow_enabled_v1(request: Request | None = None) -> bool:
    if _os_sessoes.environ.get("APPGENESIS_DEBUG_PROCESS_EDITOR") == "1":
        return True
    if request is not None:
        try:
            qs = dict(request.query_params)
            if qs.get("debug_process_editor") == "1":
                return True
        except Exception:
            pass
    return False


def _log_process_editor_flow_v1(request: Request | None, event: str, **payload) -> None:
    if not _debug_process_editor_flow_enabled_v1(request):
        return
    parts = " | ".join(f"{k}={v!r}" for k, v in payload.items())
    _PROCESS_EDITOR_FLOW_LOGGER.info("[PROCESS_EDITOR_FLOW] %s | %s", event, parts)


# APPGENESIS_DEBUG_PROCESS_EDITOR_FLOW_V1_END


def _sanitize_users_new_settings_return_url_v1(
    raw_return_url: object,
    extra_params: dict[str, object] | None = None,
) -> str:
    clean_return_url = str(raw_return_url or "").strip()

    if not clean_return_url:
        return ""

    try:
        parsed_url = urlsplit(clean_return_url)
    except Exception:
        return ""

    if parsed_url.scheme or parsed_url.netloc:
        return ""

    path = parsed_url.path or "/users/new"

    if path != "/users/new":
        return ""

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    # Campos de identidade do editor (menu, target, settings_edit_key, etc.) sao sempre
    # autoritativos a partir do chamador: se o chamador passa "" e' porque quer limpar o
    # contexto de edicao (ex.: ao sair do editor apos gravar), nao herdar o valor antigo
    # que veio no return_url capturado no momento do submit.
    for raw_key, raw_value in (extra_params or {}).items():
        clean_key = str(raw_key or "").strip()

        if not clean_key:
            continue

        clean_value = str(raw_value or "").strip()

        if clean_value:
            query_params[clean_key] = clean_value
        else:
            query_params.pop(clean_key, None)

    query_string = urlencode(query_params)

    # O fragment final acompanha o "target" resolvido (mesma fonte de verdade usada pelo
    # servidor para decidir qual card mostrar), nunca o fragment estatico do return_url --
    # caso contrario o card do editor pode permanecer "ativo" mesmo depois do target mudar.
    resolved_target = query_params.get("target", "")
    fragment = (
        f"#{resolved_target}"
        if resolved_target
        else (f"#{parsed_url.fragment}" if parsed_url.fragment else "")
    )

    return f"{path}?{query_string}{fragment}" if query_string else f"{path}{fragment}"


# Alvo exclusivo do editor de processo. Outros cards continuam a usar os seus proprios
# destinos de retorno no template e nos respetivos handlers.
_SETTINGS_MENU_EDITOR_STAY_TARGET_V1 = "settings-menu-edit-card"


def _build_settings_redirect_url(
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-account-status-card",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
    return_url: str = "",
) -> str:
    safe_return_url = _sanitize_users_new_settings_return_url_v1(
        return_url,
        {
            "error": error_message,
            "success": success_message,
            "menu": redirect_menu,
            "target": str(redirect_target or "").lstrip("#"),
            "settings_edit_key": settings_edit_key,
            "settings_action": settings_action,
            "settings_tab": settings_tab,
            # Marca este redirect como a URL final autoritativa do backend, para que
            # return_after_save.js (isBackendPostSaveReturnUrl) nao aplique a heuristica
            # de navegacao corretiva e reabra o editor com o contexto antigo do submit.
            "appgenesis_after_save": "1",
        },
    )

    if safe_return_url:
        return safe_return_url

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
    params.append("appgenesis_after_save=1")
    return f"/users/new?{chr(38).join(params)}"


# ###################################################################################
# (SETTINGS_MENU_EDITOR_STAY_REDIRECT_V1) PERMANECER NO PROCESSO E NA ABA EM EDICAO
# ###################################################################################


def _build_settings_editor_stay_redirect_url_v1(
    *,
    success_message: str,
    redirect_menu: str,
    settings_edit_key: str,
    settings_tab: str,
    return_url: str = "",
) -> str:
    return _build_settings_redirect_url(
        success_message=success_message,
        redirect_menu=redirect_menu,
        redirect_target=_SETTINGS_MENU_EDITOR_STAY_TARGET_V1,
        settings_edit_key=settings_edit_key,
        settings_action="edit",
        settings_tab=settings_tab,
        return_url=return_url,
    )


def _require_menu_settings_owner_v1(
    session,
    request: Request,
    redirect_menu: str,
    redirect_target: str,
    settings_edit_key: str = "",
    settings_action: str = "edit",
    settings_tab: str = "geral",
    return_url: str = "",
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
                return_url=return_url,
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

    if not permissions.get(
        "can_manage_tenant_structure", permissions.get("can_manage_all_entities", False)
    ):
        return RedirectResponse(
            url=_build_settings_redirect_url(
                error_message="Apenas Owner pode alterar definições do menu.",
                redirect_menu=redirect_menu,
                redirect_target=redirect_target,
                settings_edit_key=settings_edit_key,
                settings_action=settings_action,
                settings_tab=settings_tab,
                return_url=return_url,
            ),
            status_code=HTTP_303_SEE_OTHER,
        )

    return None
