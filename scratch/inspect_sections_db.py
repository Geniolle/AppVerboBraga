from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:
        # Load the administrativo menu config
        row = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'administrativo'")).first()
        if row and row.menu_config:
            config = json.loads(row.menu_config) if isinstance(row.menu_config, str) else row.menu_config
            sections = config.get("sidebar_sections", [])
            print("=== SIDEBAR_SECTIONS IN ADMINISTRATIVO MENU CONFIG ===")
            for sec in sections:
                print(f"Key: {sec.get('key')} | Label: {sec.get('label')} | Scopes: {sec.get('visibility_scopes')} | Entity ID: {sec.get('entity_id')}")
        else:
            print("No administrativo menu found")

if __name__ == '__main__':
    main()
