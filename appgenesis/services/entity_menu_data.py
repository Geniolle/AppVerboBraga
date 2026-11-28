"""Dados inseridos por cada entidade dentro de um menu (perfis e funcoes de autorizacao).

Os menus (sidebar_menu_settings) sao compartilhados: uma linha por menu_key, da entidade 1000.
O que cada entidade cadastra fica em entity_menu_data, uma linha por (entidade, menu, chave),
para que uma entidade nunca grave por cima dos dados de outra.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

ENTITY_MENU_DATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS entity_menu_data (
    entity_id INTEGER NOT NULL,
    menu_key VARCHAR(80) NOT NULL,
    data_key VARCHAR(80) NOT NULL,
    data TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_id, menu_key, data_key)
)
"""


def get_entity_menu_data(
    session: Any,
    entity_id: int,
    menu_key: str,
    data_key: str,
    default: Any = None,
) -> Any:
    raw_value = session.execute(
        text(
            """
            SELECT data
            FROM entity_menu_data
            WHERE entity_id = :entity_id
              AND menu_key = :menu_key
              AND data_key = :data_key
            """
        ),
        {"entity_id": entity_id, "menu_key": menu_key, "data_key": data_key},
    ).scalar_one_or_none()
    if raw_value is None:
        return default
    try:
        return json.loads(raw_value)
    except (TypeError, ValueError):
        return default


def set_entity_menu_data(
    session: Any,
    entity_id: int,
    menu_key: str,
    data_key: str,
    value: Any,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO entity_menu_data (entity_id, menu_key, data_key, data, updated_at)
            VALUES (:entity_id, :menu_key, :data_key, :data, CURRENT_TIMESTAMP)
            ON CONFLICT (entity_id, menu_key, data_key)
            DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "entity_id": entity_id,
            "menu_key": menu_key,
            "data_key": data_key,
            "data": json.dumps(value, ensure_ascii=False),
        },
    )
