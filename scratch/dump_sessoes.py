from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    with SessionLocal() as session:
        print("--- sidebar_menu_settings: sessoes ---")
        row = session.execute(text("SELECT id, menu_key, menu_label, is_active, is_deleted, menu_config FROM sidebar_menu_settings WHERE menu_key = 'sessoes'")).first()
        if row:
            print(f"ID: {row.id} | KEY: {row.menu_key} | LABEL: {row.menu_label} | ACTIVE: {row.is_active} | DELETED: {row.is_deleted}")
            config = json.loads(row.menu_config or "{}") if isinstance(row.menu_config, str) else row.menu_config
            print(f"  CONFIG: {json.dumps(config, indent=2, ensure_ascii=False)}")
            
if __name__ == '__main__':
    run()
