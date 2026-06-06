from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.common.row_action_access import (
    build_admin_subprocess_row_action_access_v1,
)
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

    return "Apenas administradores podem alterar sessoes do sidebar."


def ensure_actor_is_owner_for_sessions_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Apenas Owner pode alterar sessoes do sidebar."


def ensure_session_in_scope_v1(
    *,
    permissions: dict[str, Any],
    selected_entity_id: object = None,
    current_entity_scope: object = "",
) -> str:
    clean_current_entity_scope = str(current_entity_scope or "").strip().lower()

    if clean_current_entity_scope == "owner":
        return ""

    resolved_selected_entity_id = selected_entity_id or permissions.get("selected_entity_id")

    if str(resolved_selected_entity_id or "").strip().isdigit():
        return ""

    return "Selecione uma entidade valida para gerir sessoes neste escopo."


def ensure_session_row_action_allowed_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
    action: str,
    selected_entity_id: object = None,
    current_entity_scope: object = "",
) -> str:
    clean_action = str(action or "").strip().lower()
    row = repository.get_session_row_by_key_v1(
        session=session,
        section_key=section_key,
        selected_entity_id=selected_entity_id,
    )

    if row is None:
        if clean_action == "move":
            return "Sessao nao encontrada para mover."
        if clean_action == "delete":
            return "Sessao nao encontrada para eliminar."
        return "Sessao nao encontrada para edicao."

    action_access = build_admin_subprocess_row_action_access_v1(
        subprocess_key="sessoes",
        row=row,
        current_entity_scope=current_entity_scope,
    )

    if clean_action == "move" and not bool(action_access.get("can_move", True)):
        return str(action_access.get("move_disabled_reason") or "").strip() or (
            "Sem permissao para mover esta sessao."
        )

    if clean_action == "delete" and not bool(action_access.get("can_delete", True)):
        return str(action_access.get("delete_disabled_reason") or "").strip() or (
            "Sem permissao para eliminar esta sessao."
        )

    if clean_action == "edit" and not bool(action_access.get("can_edit", True)):
        return str(action_access.get("edit_disabled_reason") or "").strip() or (
            "Sem permissao para editar esta sessao."
        )

    return ""


# ###################################################################################
# (2) POLITICAS DE MOVIMENTO E ELIMINACAO
# ###################################################################################


def ensure_session_can_be_moved_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
    direction: str,
    selected_entity_id: object = None,
) -> str:
    clean_direction = str(direction or "").strip().lower()

    if clean_direction not in {"up", "down"}:
        return "Direcao invalida para mover a sessao."

    if repository.get_session_row_by_key_v1(
        session=session,
        section_key=section_key,
        selected_entity_id=selected_entity_id,
    ) is None:
        return "Sessao nao encontrada para mover."

    return ""


def ensure_session_can_be_deleted_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
    selected_entity_id: object = None,
) -> str:
    row = repository.get_session_row_by_key_v1(
        session=session,
        section_key=section_key,
        selected_entity_id=selected_entity_id,
    )

    if row is None:
        return "Sessao nao encontrada para eliminar."

    clean_key = str(row.get("key") or "").strip().lower()

    if clean_key in SIDEBAR_SECTION_DEFAULTS_BY_KEY:
        return "Nao e permitido eliminar sessoes padrao do sistema."

    return ""


def ensure_delete_only_inactive_session_v1(
    *,
    repository: Any,
    session: Session,
    section_key: str,
    selected_entity_id: object = None,
) -> str:
    row = repository.get_session_row_by_key_v1(
        session=session,
        section_key=section_key,
        selected_entity_id=selected_entity_id,
    )

    if row is None:
        return "Sessao nao encontrada para eliminar."

    row_status = repository.normalize_session_status(row.get("status"))

    if row_status == SESSION_STATUS_INACTIVE_V1:
        return ""

    return "So e permitido eliminar sessoes inativas."
