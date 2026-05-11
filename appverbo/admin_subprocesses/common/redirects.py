from __future__ import annotations

from urllib.parse import urlencode


# ###################################################################################
# (1) NORMALIZACAO DE FRAGMENTOS E PARAMETROS
# ###################################################################################

def normalize_admin_target_fragment_v1(target: object) -> str:
    clean_target = str(target or "").strip()

    if not clean_target:
        return ""

    if clean_target.startswith("#"):
        clean_target = clean_target[1:]

    return clean_target.strip()


# ###################################################################################
# (2) URL PADRAO DE RETORNO PARA O ADMINISTRATIVO
# ###################################################################################

def build_admin_return_url_v1(
    *,
    menu: str = "administrativo",
    admin_tab: str = "entidade",
    success: str = "",
    error: str = "",
    invite_link: str = "",
    target: str = "",
    appverbo_after_save: bool = False,
    extra_params: dict[str, object] | None = None,
) -> str:
    params: dict[str, str] = {
        "menu": str(menu or "administrativo").strip() or "administrativo",
        "admin_tab": str(admin_tab or "entidade").strip() or "entidade",
    }

    if success:
        params["success"] = str(success)
    if error:
        params["error"] = str(error)
    if invite_link:
        params["invite_link"] = str(invite_link)
    if appverbo_after_save:
        params["appverbo_after_save"] = "1"

    for key, value in (extra_params or {}).items():
        clean_key = str(key or "").strip()
        if not clean_key:
            continue
        if value is None:
            continue
        clean_value = str(value).strip()
        if clean_value:
            params[clean_key] = clean_value

    clean_target = normalize_admin_target_fragment_v1(target)
    fragment = f"#{clean_target}" if clean_target else ""

    return f"/users/new?{urlencode(params)}{fragment}"


# ###################################################################################
# (3) URLS ESPECIFICAS PARA CARDS DO ADMINISTRATIVO
# ###################################################################################

def build_admin_create_card_url_v1(
    *,
    admin_tab: str,
    target: str,
    success: str = "",
    error: str = "",
    extra_params: dict[str, object] | None = None,
) -> str:
    return build_admin_return_url_v1(
        admin_tab=admin_tab,
        success=success,
        error=error,
        target=target,
        appverbo_after_save=True,
        extra_params=extra_params,
    )


def build_admin_edit_card_url_v1(
    *,
    admin_tab: str,
    edit_param: str,
    edit_value: object,
    target: str,
    success: str = "",
    error: str = "",
) -> str:
    return build_admin_return_url_v1(
        admin_tab=admin_tab,
        success=success,
        error=error,
        target=target,
        appverbo_after_save=True,
        extra_params={edit_param: edit_value},
    )