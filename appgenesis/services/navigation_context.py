from __future__ import annotations

from appgenesis.services.page import build_users_new_url

# Marca um redirect como URL final autoritativa do backend pós-save, para que
# return_after_save.js (isBackendPostSaveReturnUrl) nao aplique a heuristica de
# navegacao corretiva via sessionStorage e reabra o card/editor com o contexto
# antigo do submit. Mesmo parametro ja usado em
# appgenesis/routes/profile/settings_handlers.py (_build_settings_redirect_url).
POST_SAVE_MARKER_PARAM_V1 = "appgenesis_after_save"

_ALLOWED_ADMIN_TABS: frozenset[str] = frozenset({
    "utilizador",
    "entidade",
    "sessoes",
    "menu",
    "perfil_autorizacao",
    "contas",
    "definicoes",
})


def sanitize_admin_tab_v1(value: str | None) -> str:
    clean = (value or "").strip().lower()
    return clean if clean in _ALLOWED_ADMIN_TABS else ""


def build_return_url_v1(
    *,
    return_menu: str = "",
    return_admin_tab: str = "",
    return_target: str = "",
    success: str = "",
    error: str = "",
    default_menu: str = "administrativo",
    default_admin_tab: str = "",
    default_hash: str = "",
    **extra_params: str,
) -> str:
    """
    Constrói URL de retorno /users/new preservando o contexto de subprocesso.

    Prioridade menu: return_menu > default_menu > "administrativo"
    Prioridade admin_tab: return_admin_tab (validado) > default_admin_tab (validado)
    Prioridade hash: default_hash (backend explícito) > return_target (vindo do form)
    """
    menu = (return_menu or "").strip() or default_menu or "administrativo"
    admin_tab = sanitize_admin_tab_v1(return_admin_tab) or sanitize_admin_tab_v1(default_admin_tab)

    hash_part = default_hash.strip() or (return_target or "").strip()
    if hash_part and not hash_part.startswith("#"):
        hash_part = "#" + hash_part

    params: dict[str, str] = {}
    if menu:
        params["menu"] = menu
    if admin_tab:
        params["admin_tab"] = admin_tab
    if success:
        params["success"] = success
    if error:
        params["error"] = error
    for k, v in extra_params.items():
        if isinstance(v, str) and v.strip():
            params[k] = v

    return build_users_new_url(**params) + hash_part


def build_post_save_return_url_v1(
    *,
    return_menu: str = "",
    return_admin_tab: str = "",
    return_target: str = "",
    success: str = "",
    error: str = "",
    default_menu: str = "administrativo",
    default_admin_tab: str = "",
    default_hash: str = "",
    **extra_params: str,
) -> str:
    """
    Igual a build_return_url_v1, mas marca a URL resultante com
    POST_SAVE_MARKER_PARAM_V1=1 -- usar exclusivamente no redirect final de
    sucesso apos um save, nunca em redirects de erro/validacao que devem
    manter um card/editor aberto.
    """
    extra_params[POST_SAVE_MARKER_PARAM_V1] = "1"
    return build_return_url_v1(
        return_menu=return_menu,
        return_admin_tab=return_admin_tab,
        return_target=return_target,
        success=success,
        error=error,
        default_menu=default_menu,
        default_admin_tab=default_admin_tab,
        default_hash=default_hash,
        **extra_params,
    )


__all__ = [
    "sanitize_admin_tab_v1",
    "build_return_url_v1",
    "build_post_save_return_url_v1",
    "POST_SAVE_MARKER_PARAM_V1",
]
