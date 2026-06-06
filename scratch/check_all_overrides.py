# ###################################################################################
# (1) QUERY ALL OVERRIDES ACROSS ALL MENU SETTINGS
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text(
        "SELECT id, menu_key, menu_label, menu_config FROM sidebar_menu_settings WHERE is_deleted = false"
    )).all()
    
    for r in rows:
        if not r.menu_config:
            continue
        try:
            cfg = json.loads(r.menu_config)
            overrides = cfg.get("entity_scoped_overrides_v1")
            if overrides:
                print(f"Menu Key: {r.menu_key} | Label: {r.menu_label} | ID: {r.id}")
                for ent_id, scope_data in overrides.items():
                    print(f"  Entity ID: {ent_id}")
                    for k, v in scope_data.items():
                        if k == "sidebar_sections":
                            print(f"    - sidebar_sections:")
                            for sec in v:
                                print(f"      * Key: {sec.get('key')} | Label: {sec.get('label')} | Status: {sec.get('status') or sec.get('section_status')} | Scope Mode: {sec.get('visibility_scope_mode')}")
                        else:
                            print(f"    - {k}: {v}")
        except Exception as e:
            print(f"Error reading row {r.id}: {e}")
