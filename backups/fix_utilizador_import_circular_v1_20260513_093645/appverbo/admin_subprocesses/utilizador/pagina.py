from __future__ import annotations

from typing import Any

from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository

from .urls import montar_url_fechar_utilizador_v1


####################################################################################
# (1) CONSTRUÇÃO ISOLADA DO STATE DO SUBPROCESSO UTILIZADOR
####################################################################################

def montar_estado_pagina_utilizador_v1(
    *,
    session: Any,
    user_edit_id: str | int | None = "",
    user_view: str | None = "",
    selected_entity_id: int | None = None,
    allowed_entity_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    success: str = "",
    error: str = "",
):
    config = get_admin_subprocess_config("utilizador")

    if config is None or not config.enabled:
        return None

    clean_user_edit_id = str(user_edit_id or "").strip()

    context = {
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": allowed_entity_ids or [],
        "user_view": str(user_view or "").strip(),
    }

    return build_admin_subprocess_state_from_repository(
        config=config,
        session=session,
        edit_key=clean_user_edit_id,
        success=success or "",
        error=error or "",
        return_url=montar_url_fechar_utilizador_v1(),
        context=context,
    )
