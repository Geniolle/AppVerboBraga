# ###################################################################################
# (1) QUERY DATABASE FOR SIDEBAR MENU SETTINGS AND SESSIONS
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    print("=== Records in sidebar_menu_settings ===")
    rows = session.execute(text(
        "SELECT id, menu_key, menu_label, is_active, is_deleted, menu_config FROM sidebar_menu_settings"
    )).all()
    
    for r in rows:
        print(f"ID: {r.id} | Key: {r.menu_key} | Label: {r.menu_label} | Active: {r.is_active} | Deleted: {r.is_deleted}")
        if r.menu_config:
            try:
                cfg = json.loads(r.menu_config)
                # Let's print the keys inside menu_config
                print(f"  Config keys: {list(cfg.keys())}")
                # If there are sidebar_sections, let's list them
                if "sidebar_sections" in cfg:
                    print("  Sidebar Sections:")
                    for sec in cfg["sidebar_sections"]:
                        print(f"    - Key: {sec.get('key')} | Label: {sec.get('label')} | Scope: {sec.get('visibility_scope_mode')} | Status: {sec.get('status') or sec.get('section_status')}")
                if "entity_scopes" in cfg:
                    print("  Entity Scopes in Config:")
                    for entity_id, scope_data in cfg["entity_scopes"].items():
                        print(f"    Entity ID: {entity_id}")
                        if "sidebar_sections" in scope_data:
                            for sec in scope_data["sidebar_sections"]:
                                print(f"      - Key: {sec.get('key')} | Label: {sec.get('label')} | Scope: {sec.get('visibility_scope_mode')} | Status: {sec.get('status') or sec.get('section_status')}")
            except Exception as e:
                print(f"  Failed to parse config: {e}")
        print("-" * 50)
