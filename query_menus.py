from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    with SessionLocal() as session:
        result = session.execute(text("SELECT menu_key, menu_label, menu_config FROM sidebar_menu_settings"))
        rows = result.fetchall()
        print(f"Found {len(rows)} menu settings rows:")
        for menu_key, menu_label, menu_config_str in rows:
            print(f"\n--- Menu Key: {menu_key} | Label: {menu_label} ---")
            config = json.loads(menu_config_str or "{}")
            visible_fields = config.get("visible_fields", [])
            process_visible_fields = config.get("process_visible_fields", [])
            print(f"visible_fields: {visible_fields}")
            print(f"process_visible_fields: {process_visible_fields}")
            headers = config.get("visible_field_headers", {})
            print(f"visible_field_headers: {headers}")

if __name__ == '__main__':
    run()
