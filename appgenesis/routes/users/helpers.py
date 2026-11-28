from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appgenesis.config.settings import settings
from appgenesis.models import Entity
from appgenesis.repositories import user_repository as users_repo
from appgenesis.services.user_system import is_owner_system_v1


def _extract_email_domain(raw_email: str) -> str:
    clean_email = (raw_email or "").strip().lower()
    if "@" not in clean_email:
        return ""
    _, domain = clean_email.split("@", 1)
    return domain.strip()


def _resolve_entity_from_user_email(
    session: Session,
    user_email: str,
    permissions: dict[str, Any],
) -> tuple[Entity | None, str]:
    clean_email = (user_email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return None, "Email inválido para determinar entidade."

    entity_ids: list[int] | None = None
    if not permissions.get("can_manage_all_entities"):
        entity_ids = sorted(set(permissions.get("allowed_entity_ids") or set()))
        if not entity_ids:
            return None, "Sem entidades disponíveis para este utilizador."

    scoped_entities = users_repo.list_active_entities(session, entity_ids)
    if not scoped_entities:
        return None, "Sem entidades ativas disponíveis para atribuição."

    exact_matches = [
        entity
        for entity in scoped_entities
        if (entity.email or "").strip().lower() == clean_email
    ]
    if len(exact_matches) == 1:
        return exact_matches[0], ""
    if len(exact_matches) > 1:
        return (
            None,
            "Existem múltiplas entidades com o mesmo email. Corrija os dados das entidades.",
        )

    email_domain = _extract_email_domain(clean_email)
    if email_domain:
        domain_matches = [
            entity
            for entity in scoped_entities
            if _extract_email_domain((entity.email or "").strip().lower()) == email_domain
        ]
        if len(domain_matches) == 1:
            return domain_matches[0], ""
        if len(domain_matches) > 1:
            return (
                None,
                "Existem múltiplas entidades com este domínio de email. Ajuste o email das entidades.",
            )

    if not permissions.get("can_manage_all_entities") and len(scoped_entities) == 1:
        return scoped_entities[0], ""

    return (
        None,
        "Não foi possível determinar a entidade pelo email. "
        "Verifique o email da entidade (domínio) ou ajuste os dados.",
    )


def _has_other_active_admin_for_entity(
    session: Session,
    entity_id: int,
    excluded_user_id: int,
) -> bool:
    # Mesma regra de services.auth.is_admin_user, sem uma query por candidato.
    admin_email = settings.ADMIN_LOGIN_EMAIL
    return any(
        (admin_email and str(row.login_email or "").strip().lower() == admin_email)
        or is_owner_system_v1(row.system_type)
        for row in users_repo.list_active_users_in_entity(session, entity_id, excluded_user_id)
    )


def _ensure_not_last_active_admin_for_member(
    session: Session,
    member_id: int,
    excluded_user_id: int,
) -> tuple[bool, str]:
    for entity_id in users_repo.get_active_entity_ids_for_member(session, member_id):
        if _has_other_active_admin_for_entity(session, entity_id, excluded_user_id):
            continue
        clean_entity_name = str(users_repo.get_entity_name(session, entity_id) or f"ID {entity_id}")
        return (
            False,
            (
                "Tem de existir pelo menos um Admin ativo por entidade. "
                f"A entidade '{clean_entity_name}' ficaria sem Admin ativo."
            ),
        )
    return True, ""
