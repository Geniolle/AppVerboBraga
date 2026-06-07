# ###################################################################################
# LIST ALL SIDEBAR MENU SETTINGS
# ###################################################################################
from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:
        rows = session.execute(text("select id, menu_key, menu_label, is_active, is_deleted, menu_config from sidebar_menu_settings")).mappings().all()
        for r in rows:
            print(f"ID: {r['id']}")
            print(f"  Key: {r['menu_key']}")
            print(f"  Label: {r['menu_label']}")
            print(f"  Is Active: {r['is_active']}, Is Deleted: {r['is_deleted']}")
            cfg = r['menu_config']
            if cfg:
                parsed = json.loads(cfg) if isinstance(cfg, str) else cfg
                print(f"  Sidebar Section: {parsed.get('sidebar_section')}")
                print(f"  Menu Section: {parsed.get('menu_section')}")
                print(f"  Overrides: {parsed.get('entity_scoped_overrides_v1')}")
            print("-" * 40)

if __name__ == "__main__":
    main()
