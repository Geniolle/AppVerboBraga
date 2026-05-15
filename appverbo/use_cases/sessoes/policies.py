from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
    SESSION_STATUS_INACTIVE_V1,
)
from appverbo.menu_settings import SIDEBAR_SECTION_DEFAULTS_BY_KEY
from appverbo.services.auth import is_admin_user


# ###################################################################################
# (1) POLITICAS DE PERMISSAO
# ###################################################################################

def ensure_actor_can_manage_sessions_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
) -> str:
    actor_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"] or "")

    if is_admin_user(session, actor_id, actor_login_email):
        return ""

    return "Apenas administradores podem alterar sessões do sidebar."


def ensure_actor_is_owner_for_sessions_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Apenas Owner pode alterar sessões do sidebar."


def ensure_session_in_scope_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Sem permissão para gerir sessões neste escopo."


# ###################################################################################
# (2) POLITICAS DE MOVIMENTO E ELIMINACAO
# ###################################################################################

def ensure_session_can_be_moved_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
    direction: str,
) -> str:
    clean_direction = str(direction or "").strip().lower()

    if clean_direction not in {"up", "down"}:
        return "Direção inválida para mover a sessão."

    if repository.get_for_edit(session=session, edit_key=section_key) is None:
        return "Sessão não encontrada para mover."

    return ""


def ensure_session_can_be_deleted_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
) -> str:
    row = repository.get_for_edit(session=session, edit_key=section_key)

    if row is None:
        return "Sessão não encontrada para eliminar."

    clean_key = str(row.get("key") or "").strip().lower()

    if clean_key in SIDEBAR_SECTION_DEFAULTS_BY_KEY:
        return "Não é permitido eliminar sessões padrão do sistema."

    return ""


def ensure_delete_only_inactive_session_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
) -> str:
    row = repository.get_for_edit(session=session, edit_key=section_key)

    if row is None:
        return "Sessão não encontrada para eliminar."

    row_status = repository.normalize_session_status(row.get("status"))

    if row_status == SESSION_STATUS_INACTIVE_V1:
        return ""

    return "Só é permitido eliminar sessões inativas."
