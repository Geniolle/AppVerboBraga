from __future__ import annotations

from sqlalchemy.orm import Session

from appgenesis.services.auth import is_admin_user
from appgenesis.services.permissions import get_user_entity_permissions


def authorize_empresa_edit(
    session: Session,
    current_user: dict,
    selected_entity_id: int | None,
    parsed_entity_id: int,
) -> tuple[int | None, str | None]:
    """Returns (resolved_entity_id, error_message). Exactly one of the two is set."""

    if not is_admin_user(session, current_user["id"], current_user["login_email"]):
        return None, "Apenas administradores podem editar o perfil da empresa."

    entity_permissions = get_user_entity_permissions(
        session,
        current_user["id"],
        current_user["login_email"],
        selected_entity_id,
    )

    # Escopo operacional: apenas entidades com vínculo ativo do utilizador.
    # O entity_id enviado pelo form DEVE corresponder à entidade ativa da sessão.
    resolved_entity_id = entity_permissions.get("selected_entity_id")
    allowed_data_ids = entity_permissions.get("allowed_data_entity_ids") or set()

    if resolved_entity_id is None:
        return None, "Sem entidade ativa. Contacte o administrador."

    if parsed_entity_id != resolved_entity_id:
        return None, "Entidade não corresponde à entidade ativa da sessão."

    if resolved_entity_id not in allowed_data_ids:
        return None, "Sem permissão operacional para editar o perfil desta entidade."

    return resolved_entity_id, None
