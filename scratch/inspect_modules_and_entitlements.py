from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:
        print("=== APP MODULES ===")
        modules = session.execute(text("SELECT id, module_name, module_key, is_active FROM app_modules")).mappings().all()
        for m in modules:
            print(f"ID: {m['id']} | Name: {m['module_name']} | Key: {m['module_key']} | Active: {m['is_active']}")
        print("-" * 50)

        print("=== ENTITY MODULE ENTITLEMENTS ===")
        entitlements = session.execute(text("SELECT id, entity_id, module_key, status FROM entity_module_entitlements")).mappings().all()
        for e in entitlements:
            print(f"ID: {e['id']} | Entity ID: {e['entity_id']} | Module Key: {e['module_key']} | Status: {e['status']}")
        print("-" * 50)

        print("=== SIDEBAR MENU ITEMS ===")
        items = session.execute(text("SELECT id, item_key, module_key, is_active FROM sidebar_menu_items")).mappings().all()
        for i in items:
            print(f"ID: {i['id']} | Item Key: {i['item_key']} | Module Key: {i['module_key']} | Active: {i['is_active']}")
        print("-" * 50)

if __name__ == '__main__':
    main()
