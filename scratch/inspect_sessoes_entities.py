# ###################################################################################
# INSPECT SESSOES / MENU ASSIGNMENTS PER ENTITY
# ###################################################################################
from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:
        print("=== APP_MODULES ===")
        app_modules = session.execute(text("select * from app_modules")).mappings().all()
        for row in app_modules:
            print(dict(row))
            
        print("\n=== ENTITY_MODULE_ENTITLEMENTS ===")
        entitlements = session.execute(text("select * from entity_module_entitlements")).mappings().all()
        for row in entitlements:
            print(dict(row))

        print("\n=== SIDEBAR_MENU_SETTINGS ===")
        settings = session.execute(text("select * from sidebar_menu_settings")).mappings().all()
        for row in settings:
            row_dict = dict(row)
            config = row_dict.pop("menu_config", None)
            parsed_config = None
            if config:
                try:
                    parsed_config = json.loads(config) if isinstance(config, str) else config
                except:
                    parsed_config = str(config)
            print({k: v for k, v in row_dict.items() if k != "menu_config"})
            if parsed_config:
                # print some config properties
                print("  Config - sidebar_section:", parsed_config.get("sidebar_section"))
                print("  Config - menu_section:", parsed_config.get("menu_section"))
                print("  Config - entity_scoped_overrides_v1:", parsed_config.get("entity_scoped_overrides_v1"))

        print("\n=== SIDEBAR_MENU_ITEMS ===")
        try:
            items = session.execute(text("select * from sidebar_menu_items")).mappings().all()
            for row in items:
                print(dict(row))
        except Exception as e:
            print("Error querying sidebar_menu_items:", e)

if __name__ == "__main__":
    main()
