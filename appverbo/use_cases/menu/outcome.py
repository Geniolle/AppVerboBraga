from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


MENU_RETURN_URL_FALLBACK_V1 = (
    "/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card-create#admin-menu-card-create"
)


@dataclass(frozen=True)
class MenuActionOutcome:
    redirect_url: str
    redirect_status_code: int = 303


# ###################################################################################
# (1) REDIRECT PADRÃO DA ABA MENU
# ###################################################################################


def build_menu_settings_redirect_url_v1(
    *,
    error_message: str = "",
    success_message: str = "",
    redirect_menu: str = "administrativo",
    redirect_target: str = "#admin-menu-card-create",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
) -> str:
    params: list[tuple[str, str]] = []

    if error_message:
        params.append(("settings_error", error_message))

    if success_message:
        params.append(("settings_success", success_message))

    params.append(("menu", str(redirect_menu or "administrativo")))
    params.append(("admin_tab", "menu"))

    clean_target = str(redirect_target or "").strip()
    if clean_target:
        params.append(("target", clean_target.lstrip("#")))

    if settings_edit_key:
        params.append(("settings_edit_key", str(settings_edit_key)))

    if settings_action:
        params.append(("settings_action", str(settings_action)))

    if settings_tab:
        params.append(("settings_tab", str(settings_tab)))

    return urlunsplit(("", "", "/users/new", urlencode(params), clean_target.lstrip("#")))


# ###################################################################################
# (2) NORMALIZAÇÃO DE RETURN_URL
# ###################################################################################


def sanitize_menu_return_url_v1(
    return_url: object,
    *,
    default_target: str = "#admin-menu-card-create",
) -> str:
    raw_url = str(return_url or "").strip() or MENU_RETURN_URL_FALLBACK_V1

    if raw_url.startswith(("http://", "https://", "//")):
        raw_url = MENU_RETURN_URL_FALLBACK_V1

    if not raw_url.startswith("/users/new"):
        raw_url = MENU_RETURN_URL_FALLBACK_V1

    parts = urlsplit(raw_url)
    blocked_params = {
        "success",
        "error",
        "settings_success",
        "settings_error",
        "appverbo_after_save",
    }

    clean_default_target = str(default_target or "#admin-menu-card-create").strip() or "#admin-menu-card-create"
    clean_default_target = clean_default_target.lstrip("#")
    clean_params: list[tuple[str, str]] = []
    found_menu = False
    found_admin_tab = False
    found_target = False
    target_value = clean_default_target

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in blocked_params:
            continue

        if key == "menu":
            found_menu = True
            clean_params.append(("menu", "administrativo"))
            continue

        if key == "admin_tab":
            found_admin_tab = True
            clean_params.append(("admin_tab", "menu"))
            continue

        if key == "target":
            found_target = True
            clean_target_value = str(value or "").strip().lstrip("#")
            if clean_target_value:
                target_value = clean_target_value
            clean_params.append(("target", target_value))
            continue

        clean_params.append((key, value))

    if not found_menu:
        clean_params.append(("menu", "administrativo"))

    if not found_admin_tab:
        clean_params.append(("admin_tab", "menu"))

    if not found_target:
        clean_params.append(("target", target_value))

    clean_fragment = str(parts.fragment or "").strip().lstrip("#") or target_value

    return urlunsplit(
        (
            "",
            "",
            "/users/new",
            urlencode(clean_params),
            clean_fragment,
        )
    )


def append_menu_message_to_url_v1(
    return_url: str,
    message_key: str,
    message: str,
) -> str:
    parts = urlsplit(str(return_url or "").strip() or MENU_RETURN_URL_FALLBACK_V1)
    params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {"success", "error", "settings_success", "settings_error"}
    ]

    clean_message_key = "settings_success" if message_key == "success" else "settings_error"
    if message:
        params.append((clean_message_key, message))

    return urlunsplit(
        (
            "",
            "",
            parts.path or "/users/new",
            urlencode(params),
            parts.fragment or "admin-menu-card",
        )
    )


def build_menu_return_url_with_message_v1(
    *,
    return_url: str,
    message_key: str,
    message: str,
) -> MenuActionOutcome:
    safe_return_url = sanitize_menu_return_url_v1(return_url)
    return MenuActionOutcome(
        redirect_url=append_menu_message_to_url_v1(
            safe_return_url,
            message_key,
            message,
        )
    )
