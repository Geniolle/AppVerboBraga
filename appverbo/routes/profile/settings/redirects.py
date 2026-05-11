from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


####################################################################################
# (1) URL DE RETORNO PADRÃO DAS CONFIGURAÇÕES DO MENU
####################################################################################

def build_settings_redirect_url_v1(
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
        params.append(("error", error_message))

    if success_message:
        params.append(("success", success_message))

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


####################################################################################
# (2) MENSAGENS EM RETURN_URL
####################################################################################

def append_settings_message_to_url_v1(return_url: str, message_key: str, message: str) -> str:
    parts = urlsplit(str(return_url or "").strip() or "/users/new?menu=administrativo")
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error"}
    ]

    if message_key and message:
        params.append((message_key, message))

    return urlunsplit((
        "",
        "",
        parts.path or "/users/new",
        urlencode(params),
        parts.fragment,
    ))
