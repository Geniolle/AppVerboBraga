from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
    SidebarSectionAdminRepository,
)
from appverbo.admin_subprocesses.sessoes.configuracao import SESSOES_CONFIG
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.sessoes.outcome import SessionActionOutcome
from appverbo.use_cases.sessoes.policies import (
    ensure_actor_can_manage_sessions_v1,
    ensure_actor_is_owner_for_sessions_v1,
    ensure_delete_only_inactive_session_v1,
    ensure_session_can_be_deleted_v1,
)
from appverbo.use_cases.sessoes.save_session import (
    build_sidebar_section_redirect_v1,
    sanitize_sidebar_section_return_url_v1,
)


# ###################################################################################
# (1) NORMALIZACAO DE PAYLOAD
# ###################################################################################

def normalize_delete_session_input_v1(
    *,
    section_key: str,
    key: str,
    sidebar_section_return_url: str,
) -> dict[str, str]:
    return {
        "section_key": str(section_key or key or "").strip(),
        "sidebar_section_return_url": str(sidebar_section_return_url or "").strip(),
    }


# ###################################################################################
# (2) USE CASE DE ELIMINACAO DE SESSAO
# ###################################################################################

def execute_delete_session_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    payload: dict[str, str],
) -> SessionActionOutcome:
    repository = SidebarSectionAdminRepository(SESSOES_CONFIG)
    safe_return_url = sanitize_sidebar_section_return_url_v1(
        payload.get("sidebar_section_return_url", "")
    )

    policy_error = ensure_actor_can_manage_sessions_v1(
        session=session,
        actor_user=actor_user,
    )

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"] or ""),
        selected_entity_id,
    )

    policy_error = ensure_actor_is_owner_for_sessions_v1(permissions=permissions)

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    policy_error = ensure_session_can_be_deleted_v1(
        repository=repository,
        session=session,
        section_key=payload.get("section_key", ""),
    )

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    policy_error = ensure_delete_only_inactive_session_v1(
        repository=repository,
        session=session,
        section_key=payload.get("section_key", ""),
    )

    if policy_error:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=policy_error,
        )

    ok, error_message = repository.delete_session(
        session=session,
        section_key=payload.get("section_key", ""),
    )

    if not ok:
        return build_sidebar_section_redirect_v1(
            return_url=safe_return_url,
            message_key="error",
            message=error_message or "Não foi possível eliminar a sessão.",
        )

    return build_sidebar_section_redirect_v1(
        return_url=safe_return_url,
        message_key="success",
        message="Sessão eliminada com sucesso.",
    )
