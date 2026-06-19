from __future__ import annotations

from dataclasses import replace
from typing import Any

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository


_PERMISSION_LOCKED_FIELDS = frozenset({"profile_scope", "status"})

_RETURN_URL = "/users/new?menu=administrativo&admin_tab=entidade#create-entity-card"


def montar_estado_pagina_entidade_v1(
    *,
    session: Any,
    entity_edit_id: str | int | None = "",
    view_mode: bool = False,
    can_manage_all_entities: bool = True,
    allowed_entity_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    success: str = "",
    error: str = "",
) -> Any | None:
    config = ENTIDADE_CONFIG

    if not config.enabled:
        return None

    clean_edit_id = str(entity_edit_id or "").strip()

    context: dict[str, Any] = {}
    # Só restringir por entidade quando o utilizador NÃO pode gerir todas.
    # Para admins (can_manage_all_entities=True), deixar context sem
    # allowed_entity_ids → repositório não aplica filtro → todas as entidades visíveis.
    if not can_manage_all_entities and allowed_entity_ids is not None:
        context["allowed_entity_ids"] = list(allowed_entity_ids)

    state = build_admin_subprocess_state_from_repository(
        config=config,
        session=session,
        edit_key=clean_edit_id,
        success=success,
        error=error,
        return_url=_RETURN_URL,
        context=context,
    )

    if state is None:
        return None

    state.view_mode = view_mode

    if not can_manage_all_entities:
        state.active_fields = tuple(
            replace(f, readonly_on_edit=True) if f.key in _PERMISSION_LOCKED_FIELDS else f
            for f in state.effective_fields
        )

    return state
