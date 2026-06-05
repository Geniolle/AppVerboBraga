from __future__ import annotations

from typing import Any

from appverbo.admin_subprocesses.runtime import (
    build_admin_subprocess_state_from_repository,
)
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG

from .urls import montar_url_fechar_utilizador_v1


####################################################################################
# (1) FUNCOES AUXILIARES
####################################################################################

def _build_select_options_v1(
    raw_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    empty_label: str,
) -> tuple[tuple[str, str], ...]:
    options: list[tuple[str, str]] = [("", empty_label)]
    seen_values: set[str] = {""}

    for raw_row in raw_rows or []:
        row = dict(raw_row or {})
        option_value = str(row.get("id") or "").strip()
        option_label = str(row.get("name") or "").strip()

        if not option_value or not option_label:
            continue

        if option_value in seen_values:
            continue

        seen_values.add(option_value)
        options.append((option_value, option_label))

    return tuple(options)


####################################################################################
# (2) CONSTRUCAO ISOLADA DO STATE DO SUBPROCESSO UTILIZADOR
####################################################################################

def montar_estado_pagina_utilizador_v1(
    *,
    session: Any,
    user_edit_id: str | int | None = "",
    user_view: str | None = "",
    create_data: dict[str, Any] | None = None,
    selected_entity_id: int | None = None,
    allowed_entity_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    entity_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    profile_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    success: str = "",
    error: str = "",
):
    config = UTILIZADOR_CONFIG

    if config is None or not config.enabled:
        return None

    clean_user_edit_id = str(user_edit_id or "").strip()

    context = {
        "selected_entity_id": selected_entity_id,
        "allowed_entity_ids": allowed_entity_ids or [],
        "user_view": str(user_view or "").strip(),
    }

    state = build_admin_subprocess_state_from_repository(
        config=config,
        session=session,
        edit_key=clean_user_edit_id,
        create_data=create_data,
        success=success or "",
        error=error or "",
        return_url=montar_url_fechar_utilizador_v1(),
        context=context,
    )

    if state is None:
        return None

    state.field_options["entity_id"] = _build_select_options_v1(
        entity_rows,
        empty_label="Selecionar entidade",
    )
    state.field_options["profile_id"] = _build_select_options_v1(
        profile_rows,
        empty_label="Selecionar perfil",
    )

    return state
