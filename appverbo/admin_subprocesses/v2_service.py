from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .v2_models import AdminSubprocessConfigV2, AdminSubprocessStateV2
from .v2_registry import get_admin_subprocess_config_v2
from .v2_repository import (
    load_repository_class_v2,
    normalize_admin_subprocess_text_v2,
    split_admin_subprocess_rows_v2,
)


# ###################################################################################
# (1) URLS SEGURAS
# ###################################################################################

def sanitize_admin_subprocess_return_url_v2(raw_url: object, fallback_url: str) -> str:
    clean_url = normalize_admin_subprocess_text_v2(raw_url)

    if not clean_url:
        return fallback_url

    try:
        parsed_url = urlsplit(clean_url)
    except Exception:
        return fallback_url

    if parsed_url.scheme or parsed_url.netloc:
        return fallback_url

    path = parsed_url.path or "/users/new"

    if path not in {"/users/new", "/admin/subprocess-v2/entidade"} and not path.startswith("/admin/subprocess-v2/"):
        return fallback_url

    return urlunsplit(("", "", path, parsed_url.query, parsed_url.fragment))


def add_admin_subprocess_message_v2(
    url: str,
    *,
    config: AdminSubprocessConfigV2,
    success: str = "",
    error: str = "",
) -> str:
    parsed_url = urlsplit(url)
    params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))

    params.setdefault("menu", "administrativo")
    params.setdefault("admin_tab", config.key)
    params["appverbo_after_save"] = "1"

    if success:
        params[f"{config.key}_success"] = success

    if error:
        params[f"{config.key}_error"] = error

    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path or "/users/new",
            urlencode(params),
            parsed_url.fragment,
        )
    )


def default_admin_subprocess_return_url_v2(config: AdminSubprocessConfigV2) -> str:
    return (
        f"/users/new?menu=administrativo&admin_tab={config.key}"
        f"&target=%23{config.resolved_default_target}"
    )

# ###################################################################################
# (2) REPOSITORY
# ###################################################################################

def create_admin_subprocess_repository_v2(
    *,
    config: AdminSubprocessConfigV2,
    session: Any,
    request: Any,
    current_user: dict[str, Any] | None,
) -> Any:
    repository_class = load_repository_class_v2(config.repository_class_path)
    return repository_class(
        session=session,
        request=request,
        current_user=current_user,
        config=config,
    )


# ###################################################################################
# (3) ESTADO DE TELA
# ###################################################################################

def build_admin_subprocess_state_v2(
    *,
    key: str,
    session: Any,
    request: Any,
    current_user: dict[str, Any] | None,
    edit_key: str = "",
    success: str = "",
    error: str = "",
    return_url: str = "",
) -> AdminSubprocessStateV2 | None:
    config = get_admin_subprocess_config_v2(key)

    if config is None:
        return None

    repository = create_admin_subprocess_repository_v2(
        config=config,
        session=session,
        request=request,
        current_user=current_user,
    )

    rows = repository.list_rows()
    active_rows, inactive_rows = split_admin_subprocess_rows_v2(rows, config)

    edit_data = repository.get_for_edit(edit_key) if edit_key else None

    return AdminSubprocessStateV2(
        config=config,
        mode="edit" if edit_data else "create",
        edit_key=edit_key,
        edit_data=edit_data,
        active_rows=active_rows,
        inactive_rows=inactive_rows,
        success=success,
        error=error,
        return_url=return_url or default_admin_subprocess_return_url_v2(config),
    )
