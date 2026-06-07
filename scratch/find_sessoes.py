import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        print("=== SEARCHING IN SIDEBAR_MENU_SETTINGS ===")
        rows = session.execute(text("SELECT id, menu_key, menu_label, menu_config FROM sidebar_menu_settings")).all()
        for r in rows:
            cfg_str = str(r.menu_config or "")
            if any(x in cfg_str.lower() for x in ["dados gerais", "igreja", "sessões", "sessoes"]):
                print(f"Match in sidebar_menu_settings: ID={r.id}, Key={r.menu_key}, Label={r.menu_label}")
                if r.menu_config:
                    try:
                        cfg = json.loads(r.menu_config)
                        # Let's inspect where they match
                        if "sidebar_section" in cfg:
                            print(f"  sidebar_section: {cfg.get('sidebar_section')}")
                        if "menu_section" in cfg:
                            print(f"  menu_section: {cfg.get('menu_section')}")
                        if "sidebar_sections" in cfg:
                            print(f"  sidebar_sections: {[s.get('key') for s in cfg['sidebar_sections']]}")
                        if "entity_scoped_overrides_v1" in cfg and cfg["entity_scoped_overrides_v1"]:
                            print(f"  Overrides: {list(cfg['entity_scoped_overrides_v1'].keys())}")
                            for k, v in cfg["entity_scoped_overrides_v1"].items():
                                if "sidebar_section" in v:
                                    print(f"    - Entity {k} override sidebar_section: {v.get('sidebar_section')}")
                    except Exception as e:
                        print(f"  Error: {e}")
                        
        print("\n=== SEARCHING IN SIDEBAR_MENU_ITEMS ===")
        items = session.execute(text("SELECT * FROM sidebar_menu_items")).mappings().all()
        for item in items:
            item_str = str(dict(item))
            if any(x in item_str.lower() for x in ["dados gerais", "igreja", "sessões", "sessoes"]):
                print(f"Match in sidebar_menu_items: {dict(item)}")

        print("\n=== SEARCHING IN ENTITIES ===")
        entities = session.execute(text("SELECT * FROM entities")).mappings().all()
        for ent in entities:
            print(f"Entity: {dict(ent)}")

if __name__ == '__main__':
    main()
