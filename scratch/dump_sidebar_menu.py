from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    with SessionLocal() as session:
        print("--- sidebar_menu_settings ---")
        rows = session.execute(text("SELECT id, menu_key, menu_label, is_active, is_deleted, menu_config FROM sidebar_menu_settings")).fetchall()
        for r in rows:
            print(f"ID: {r.id} | KEY: {r.menu_key} | LABEL: {r.menu_label} | ACTIVE: {r.is_active} | DELETED: {r.is_deleted}")
            config = json.loads(r.menu_config or "{}") if isinstance(r.menu_config, str) else r.menu_config
            print(f"  CONFIG: {json.dumps(config, indent=2, ensure_ascii=False)}")
            print("-" * 50)
            
if __name__ == '__main__':
    run()
