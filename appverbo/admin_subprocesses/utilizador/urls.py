from __future__ import annotations

from typing import Any


USER_ADMIN_BASE_URL_V1 = "/users/new"
USER_ADMIN_MENU_V1 = "administrativo"
USER_ADMIN_TAB_V1 = "utilizador"
USER_EDIT_TARGET_V1 = "edit-user-card"


def _normalizar_user_id_v1(user_id: Any) -> str:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return ""

    return clean_user_id


def montar_url_exibir_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return ""

    return (
        f"{USER_ADMIN_BASE_URL_V1}"
        f"?menu={USER_ADMIN_MENU_V1}"
        f"&admin_tab={USER_ADMIN_TAB_V1}"
        f"&user_edit_id={clean_user_id}"
        f"&user_view=1"
        f"&target={USER_EDIT_TARGET_V1}"
        f"#{USER_EDIT_TARGET_V1}"
    )


def montar_url_editar_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return ""

    return (
        f"{USER_ADMIN_BASE_URL_V1}"
        f"?menu={USER_ADMIN_MENU_V1}"
        f"&admin_tab={USER_ADMIN_TAB_V1}"
        f"&user_edit_id={clean_user_id}"
        f"&user_view=0"
        f"&target={USER_EDIT_TARGET_V1}"
        f"#{USER_EDIT_TARGET_V1}"
    )


def montar_url_fechar_utilizador_v1() -> str:
    return f"{USER_ADMIN_BASE_URL_V1}?menu={USER_ADMIN_MENU_V1}&admin_tab={USER_ADMIN_TAB_V1}"


__all__ = (
    "USER_ADMIN_BASE_URL_V1",
    "USER_ADMIN_MENU_V1",
    "USER_ADMIN_TAB_V1",
    "USER_EDIT_TARGET_V1",
    "montar_url_exibir_utilizador_v1",
    "montar_url_editar_utilizador_v1",
    "montar_url_fechar_utilizador_v1",
)
