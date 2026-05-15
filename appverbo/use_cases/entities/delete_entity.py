from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.repositories.entity_repository import EntityAdminRepository
from appverbo.core import BASE_DIR
from appverbo.services.page import build_users_new_url
from appverbo.services.permissions import get_user_entity_permissions
from appverbo.use_cases.entities.outcome import EntityActionOutcome
from appverbo.use_cases.entities.policies import (
    ensure_actor_can_manage_entities_v1,
    ensure_delete_only_inactive_entity_v1,
    ensure_entity_can_be_deleted_v1,
    ensure_entity_in_scope_v1,
)


# ###################################################################################
# (1) HELPERS DE REDIRECT E FICHEIROS
# ###################################################################################

def _build_entity_delete_redirect_v1(
    *,
    entity_success: str = "",
    entity_error: str = "",
    entity_edit_id: int | None = None,
    anchor: str = "#recent-entities-card",
) -> str:
    query_kwargs: dict[str, str] = {
        "entity_success": entity_success,
        "entity_error": entity_error,
        "menu": "administrativo",
        "admin_tab": "entidade",
    }

    if entity_edit_id is not None:
        query_kwargs["entity_edit_id"] = str(entity_edit_id)

    return build_users_new_url(**query_kwargs) + anchor


def _remove_local_logo_if_exists_v1(logo_url: str) -> None:
    clean_logo_url = str(logo_url or "").strip()

    if not clean_logo_url.startswith("/static/entities/"):
        return

    local_logo_path = BASE_DIR / clean_logo_url.lstrip("/")
    local_logo_path.unlink(missing_ok=True)


# ###################################################################################
# (2) USE CASE PRINCIPAL
# ###################################################################################

def execute_delete_entity_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
    selected_entity_id: int | None,
    entity_id: str | int,
) -> EntityActionOutcome:
    clean_entity_id = str(entity_id or "").strip()

    if not clean_entity_id.isdigit():
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error="Entidade inválida para eliminação.",
            ),
        )

    parsed_entity_id = int(clean_entity_id)
    repository = EntityAdminRepository(ENTIDADE_CONFIG)

    admin_error = ensure_actor_can_manage_entities_v1(
        session=session,
        actor_user=actor_user,
    )

    if admin_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error=admin_error,
            ),
        )

    permissions = get_user_entity_permissions(
        session,
        int(actor_user["id"]),
        str(actor_user["login_email"]),
        selected_entity_id,
    )

    scope_error = ensure_entity_in_scope_v1(
        entity_id=parsed_entity_id,
        permissions=permissions,
        action_label="eliminar",
    )

    if scope_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error=scope_error,
            ),
        )

    entity = repository.get_by_id(
        session=session,
        entity_id=parsed_entity_id,
    )

    if entity is None:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error="Entidade não encontrada.",
            ),
        )

    inactive_error = ensure_delete_only_inactive_entity_v1(entity)

    if inactive_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error=inactive_error,
                entity_edit_id=parsed_entity_id,
                anchor="#edit-entity-card",
            ),
        )

    delete_policy_error = ensure_entity_can_be_deleted_v1(
        repository=repository,
        session=session,
        entity_id=parsed_entity_id,
    )

    if delete_policy_error:
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error=delete_policy_error,
                entity_edit_id=parsed_entity_id,
                anchor="#edit-entity-card",
            ),
        )

    logo_url_to_remove = str(entity.logo_url or "").strip()

    repository.delete_member_entity_links(
        session=session,
        entity_id=parsed_entity_id,
    )
    repository.delete_inactive_entity(
        session=session,
        entity=entity,
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return EntityActionOutcome(
            kind="redirect",
            redirect_url=_build_entity_delete_redirect_v1(
                entity_error="Não foi possível eliminar a entidade.",
            ),
        )

    _remove_local_logo_if_exists_v1(logo_url_to_remove)

    return EntityActionOutcome(
        kind="redirect",
        redirect_url=_build_entity_delete_redirect_v1(
            entity_success="Entidade eliminada com sucesso.",
        ),
    )

