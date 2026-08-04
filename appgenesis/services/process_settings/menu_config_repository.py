from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.services.process_settings.normalizers import _parse_menu_config


def load_menu_config(
    session: Session,
    entity_id: int,
    menu_key: str,
) -> dict[str, Any]:
    clean_menu_key = str(menu_key or "").strip().lower()
    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE entity_id = :entity_id
              AND lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"entity_id": int(entity_id), "menu_key": clean_menu_key},
    ).scalar_one_or_none()
    return _parse_menu_config(raw_menu_config)


def save_menu_config(
    session: Session,
    entity_id: int,
    menu_key: str,
    menu_config: dict[str, Any],
) -> tuple[bool, str]:
    clean_menu_key = str(menu_key or "").strip().lower()
    result = session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE entity_id = :entity_id
              AND lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "entity_id": int(entity_id),
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    if result.rowcount != 1:
        session.rollback()
        return False, "Configuração do processo não encontrada para a entidade ativa."

    session.commit()
    return True, ""
