"""Armazenamento dos perfis de autorizacao por entidade.

Os perfis ficam na linha sidebar_menu_settings do menu Administrativo de cada entidade
(mesmo sitio das funcoes), e nao no registo de membro de quem os criou. Assim um
utilizador comum consegue ler os perfis que as funcoes da sua entidade referenciam.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import String, cast, select, text

from appgenesis.models import Entity

AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY = "authorization_profile_fields"


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
    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'administrativo'
              AND entity_id = :entity_id
            LIMIT 1
            """
        ),
        {"entity_id": entity_id},
    ).fetchone()
    raw_config = row[0] if row else None
    menu_config = raw_config if isinstance(raw_config, dict) else json.loads(raw_config or "{}")
    raw_fields = menu_config.get(AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY)
    return EntityAuthProfileStore(
        entity_id=entity_id,
        profile_custom_fields=str(raw_fields) if raw_fields else None,
    )


def save_entity_auth_profile_store_v1(session: Any, store: EntityAuthProfileStore) -> bool:
    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'administrativo'
              AND entity_id = :entity_id
            LIMIT 1
            """
        ),
        {"entity_id": store.entity_id},
    ).fetchone()
    if not row:
        return False
    raw_config = row[0]
    menu_config = raw_config if isinstance(raw_config, dict) else json.loads(raw_config or "{}")
    if store.profile_custom_fields:
        menu_config[AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY] = store.profile_custom_fields
    else:
        menu_config.pop(AUTH_PROFILE_FIELDS_MENU_CONFIG_KEY, None)
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = 'administrativo'
              AND entity_id = :entity_id
            """
        ),
        {
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
            "entity_id": store.entity_id,
        },
    )
    return True
