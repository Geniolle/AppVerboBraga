from appverbo.core import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as session:
    row = session.execute(
        text("""
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = 'documentos'
            LIMIT 1
        """)
    ).one_or_none()

    config = json.loads(row.menu_config) if isinstance(row.menu_config, str) else row.menu_config

    print("LISTAS:")
    for item in config.get("process_lists", []):
        print(item)

    print("")
    print("CAMPO ESTADO CIVIL:")
    for item in config.get("additional_fields", []):
        if "estado" in str(item.get("label", "")).lower():
            print(item)
