from __future__ import annotations

from appverbo.services.page import build_users_new_url

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


__all__ = [
    "sanitize_admin_tab_v1",
    "build_return_url_v1",
]
