from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


####################################################################################
# (1) NORMALIZAÇÃO DO IDENTIFICADOR DO UTILIZADOR
####################################################################################

def _normalizar_user_id_v1(user_id: Any) -> str:
    clean_user_id = str(user_id or "").strip()

    if not clean_user_id.isdigit():
        return ""

    return clean_user_id


####################################################################################
# (2) URL BASE DO SUBPROCESSO UTILIZADOR
####################################################################################

def montar_url_base_utilizador_v1() -> str:
    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
    )

    return "/users/new?" + urlencode(params)


####################################################################################
# (3) URL DE EXIBIR UTILIZADOR
####################################################################################

def montar_url_exibir_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return montar_url_base_utilizador_v1()

    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
        ("user_edit_id", clean_user_id),
        ("user_view", "1"),
        ("target", "edit-user-card"),
    )

    return "/users/new?" + urlencode(params) + "#edit-user-card"


####################################################################################
# (4) URL DE EDITAR UTILIZADOR
####################################################################################

def montar_url_editar_utilizador_v1(user_id: Any) -> str:
    clean_user_id = _normalizar_user_id_v1(user_id)

    if not clean_user_id:
        return montar_url_base_utilizador_v1()

    params = (
        ("menu", "administrativo"),
        ("admin_tab", "utilizador"),
        ("user_edit_id", clean_user_id),
        ("user_view", "0"),
        ("target", "edit-user-card"),
    )

    return "/users/new?" + urlencode(params) + "#edit-user-card"


####################################################################################
# (5) URL DE FECHAR UTILIZADOR
####################################################################################

def montar_url_fechar_utilizador_v1() -> str:
    return montar_url_base_utilizador_v1()
