from __future__ import annotations

import json

from sqlalchemy import text

from appverbo.core import SessionLocal
from appverbo.menu_settings import (
    _rebuild_menu_process_hierarchy_from_additional_fields_v1,
    normalize_menu_process_additional_fields_v1,
)


# //###################################################################################
# (1) ATUALIZAR HIERARQUIA DOS PROCESSOS JA EXISTENTES
# //###################################################################################

def main() -> None:
    updated_count = 0

    with SessionLocal() as session:
        table_exists = session.execute(
            text("SELECT to_regclass('public.sidebar_menu_settings')")
        ).scalar_one_or_none()

        if not table_exists:
            print("[AVISO] A tabela sidebar_menu_settings nao existe nesta base de dados.")
            print("[AVISO] Execute primeiro: python -m alembic upgrade head")
            return

        rows = session.execute(
            text(
                """
                SELECT menu_key, menu_config
                FROM sidebar_menu_settings
                ORDER BY menu_key
                """
            )
        ).mappings().all()

        for row in rows:
            menu_key = str(row.get("menu_key") or "").strip().lower()
            raw_config = row.get("menu_config")

            menu_config: dict = {}

            if isinstance(raw_config, str) and raw_config.strip():
                try:
                    parsed_config = json.loads(raw_config)
                    if isinstance(parsed_config, dict):
                        menu_config = parsed_config
                except json.JSONDecodeError:
                    menu_config = {}

            normalized_fields = normalize_menu_process_additional_fields_v1(
                menu_config.get("additional_fields")
            )

            if not normalized_fields:
                continue

            new_config = _rebuild_menu_process_hierarchy_from_additional_fields_v1(
                menu_config,
                normalized_fields,
            )

            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_config = :menu_config
                    WHERE lower(trim(menu_key)) = :menu_key
                    """
                ),
                {
                    "menu_key": menu_key,
                    "menu_config": json.dumps(new_config, ensure_ascii=False),
                },
            )
            updated_count += 1

        session.commit()

    print(f"[OK] Processos atualizados com hierarquia: {updated_count}")


if __name__ == "__main__":
    main()
