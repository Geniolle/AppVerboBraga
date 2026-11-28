"""Armazenamento dos perfis de autorizacao por entidade.

Os perfis ficam na linha sidebar_menu_settings do menu Administrativo de cada entidade
(mesmo sitio das funcoes), e nao no registo de membro de quem os criou. Assim um
utilizador comum consegue ler os perfis que as funcoes da sua entidade referenciam.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import (
    String,
    cast,
    select,
)

from appgenesis.models import Entity
from appgenesis.services.entity_menu_data import get_entity_menu_data, set_entity_menu_data

AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY = "authorization_profile_fields"
AUTH_PROFILE_MENU_KEY = "administrativo"


@dataclass
class EntityAuthProfileStore:
    entity_id: int
    profile_custom_fields: str | None


def resolve_entity_id_for_auth_profiles_v1(session: Any, context: dict[str, Any] | None) -> int | None:
    safe_context = context or {}
    raw_entity_id = safe_context.get("selected_entity_id")
    if raw_entity_id not in (None, ""):
        try:
            return int(raw_entity_id)
        except (TypeError, ValueError):
            return None
    entity_number = str(safe_context.get("entity_number") or "").strip()
    if not entity_number:
        return None
    return session.execute(
        select(Entity.id)
        .where(cast(Entity.entity_number, String) == entity_number)
        .limit(1)
    ).scalar()


def load_entity_auth_profile_store_v1(session: Any, entity_id: int) -> EntityAuthProfileStore:
    raw_fields = get_entity_menu_data(
        session, entity_id, AUTH_PROFILE_MENU_KEY, AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY
    )
    return EntityAuthProfileStore(
        entity_id=entity_id,
        profile_custom_fields=str(raw_fields) if raw_fields else None,
    )


def save_entity_auth_profile_store_v1(session: Any, store: EntityAuthProfileStore) -> bool:
    set_entity_menu_data(
        session,
        store.entity_id,
        AUTH_PROFILE_MENU_KEY,
        AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY,
        store.profile_custom_fields or "",
    )
    return True
