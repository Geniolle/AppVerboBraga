"""Dono das sessoes do sidebar (entidade legado cria as suas).

Sessoes de sistema (Default) nao tem dono e continuam a ser geridas pelo Owner.
Sessoes criadas por uma entidade legado guardam o Nº da entidade criadora em
``menu_config["sidebar_section_owners"]`` (chave = key da sessao). A regra usa o
entity_number, nunca o id interno.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from appgenesis.models import Entity
from appgenesis.services.process_settings.normalizers import _normalize_sidebar_section_key

MENU_CONFIG_SIDEBAR_SECTION_OWNERS_KEY = "sidebar_section_owners"
MENU_CONFIG_SIDEBAR_SECTION_CREATORS_KEY = "sidebar_section_creators"
ADMIN_MENU_KEY = "administrativo"


def resolve_entity_number_v1(session: Session, entity_id: int | None) -> int | None:
    if entity_id is None:
        return None
    value = session.execute(
        select(Entity.entity_number).where(Entity.id == entity_id).limit(1)
    ).scalar()
    return int(value) if value is not None else None


def _get_section_number_map(menu_config: dict[str, Any] | None, map_key: str) -> dict[str, int]:
    raw = (menu_config or {}).get(map_key) or {}
    if not isinstance(raw, dict):
        return {}
    owners: dict[str, int] = {}
    for raw_key, raw_number in raw.items():
        clean_key = _normalize_sidebar_section_key(raw_key)
        if not clean_key:
            continue
        try:
            owners[clean_key] = int(raw_number)
        except (TypeError, ValueError):
            continue
    return owners


def get_section_owner_map(menu_config: dict[str, Any] | None) -> dict[str, int]:
    return _get_section_number_map(menu_config, MENU_CONFIG_SIDEBAR_SECTION_OWNERS_KEY)


def is_section_visible_to_entity(
    owner_map: dict[str, int], section_key: Any, entity_number: int | None
) -> bool:
    owner = owner_map.get(_normalize_sidebar_section_key(section_key))
    return owner is None or owner == entity_number


def filter_sections_for_entity(
    sections: Iterable[dict[str, Any]],
    owner_map: dict[str, int],
    entity_number: int | None,
) -> list[dict[str, Any]]:
    return [
        dict(section)
        for section in sections
        if is_section_visible_to_entity(owner_map, section.get("key"), entity_number)
    ]


def can_manage_section(
    owner_map: dict[str, int],
    section_key: Any,
    entity_number: int | None,
    is_tenant_owner: bool,
) -> bool:
    """Owner gere sessoes de sistema; legado gere apenas as que criou."""
    owner = owner_map.get(_normalize_sidebar_section_key(section_key))
    if owner is None:
        return is_tenant_owner
    return entity_number is not None and owner == entity_number


def load_section_owner_map_v1(session: Session) -> dict[str, int]:
    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": ADMIN_MENU_KEY},
    ).scalar_one_or_none()
    try:
        menu_config = json.loads(raw_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}
    return get_section_owner_map(menu_config if isinstance(menu_config, dict) else {})


def _set_section_number_map_v1(
    session: Session, map_key: str, section_key: str, entity_number: int | None
) -> None:
    """Grava (ou remove, com entity_number=None) um Nº de entidade por sessao no mapa indicado."""
    clean_key = _normalize_sidebar_section_key(section_key)
    if not clean_key:
        return

    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": ADMIN_MENU_KEY},
    ).scalar_one_or_none()

    try:
        menu_config = json.loads(raw_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}
    if not isinstance(menu_config, dict):
        menu_config = {}

    numbers = _get_section_number_map(menu_config, map_key)
    if entity_number is None:
        numbers.pop(clean_key, None)
    else:
        numbers[clean_key] = int(entity_number)
    menu_config[map_key] = numbers

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": ADMIN_MENU_KEY,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()


def set_section_owner_v1(
    session: Session, section_key: str, entity_number: int | None
) -> None:
    """Grava (ou remove, com entity_number=None) o dono de uma sessao."""
    _set_section_number_map_v1(
        session, MENU_CONFIG_SIDEBAR_SECTION_OWNERS_KEY, section_key, entity_number
    )


def set_section_creator_v1(
    session: Session, section_key: str, entity_number: int | None
) -> None:
    """Grava (ou remove) o Nº da entidade que criou a sessao (so para exibicao)."""
    _set_section_number_map_v1(
        session, MENU_CONFIG_SIDEBAR_SECTION_CREATORS_KEY, section_key, entity_number
    )


def load_section_creator_map_v1(session: Session) -> dict[str, int]:
    raw_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": ADMIN_MENU_KEY},
    ).scalar_one_or_none()
    try:
        menu_config = json.loads(raw_config or "{}")
    except (TypeError, ValueError):
        menu_config = {}
    return _get_section_number_map(
        menu_config if isinstance(menu_config, dict) else {},
        MENU_CONFIG_SIDEBAR_SECTION_CREATORS_KEY,
    )


SESSION_ENTITY_NUMBER_FIELD_KEY = "entity_number"


def with_session_entity_number_v1(config, entity_number_display: str):
    """Preenche o campo Nº DA ENTIDADE (somente leitura) da configuracao de sessoes."""
    from dataclasses import replace

    adjusted = tuple(
        replace(field, default_value=entity_number_display)
        if field.key == SESSION_ENTITY_NUMBER_FIELD_KEY
        else field
        for field in config.fields
    )
    return replace(config, fields=adjusted)
