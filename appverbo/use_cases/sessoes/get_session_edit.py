from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
    SESSION_STATUS_ACTIVE_V1,
    SidebarSectionAdminRepository,
)
from appverbo.admin_subprocesses.sessoes.configuracao import SESSOES_CONFIG


# ###################################################################################
# (1) DEFAULTS DE EDICAO
# ###################################################################################

def get_session_edit_defaults_v1() -> dict[str, str]:
    return {
        "key": "",
        "label": "",
        "visibility_scope_mode": "all",
        "status": SESSION_STATUS_ACTIVE_V1,
        "status_label": "Ativo",
        "perfil": "",
    }


# ###################################################################################
# (2) USE CASE DE DADOS PARA FORMULARIO DE EDICAO
# ###################################################################################

def execute_get_session_edit_v1(
    *,
    session: Session,
    session_key: str | None,
) -> dict[str, str]:
    clean_session_key = str(session_key or "").strip()

    if not clean_session_key:
        return get_session_edit_defaults_v1()

    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    row = repository.get_for_edit(
        session=session,
        edit_key=clean_session_key,
    )

    if row is None:
        return get_session_edit_defaults_v1()

    return {
        "key": str(row.get("key") or ""),
        "label": str(row.get("label") or ""),
        "visibility_scope_mode": str(row.get("visibility_scope_mode") or "all"),
        "status": str(row.get("status") or SESSION_STATUS_ACTIVE_V1),
        "status_label": str(row.get("status_label") or "Ativo"),
        "entity_internal_number": str(row.get("entity_internal_number") or ""),
        "perfil": str(row.get("perfil") or ""),
    }
