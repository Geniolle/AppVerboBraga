# ###################################################################################
# INSPECT SESSOES MENU DETAILED SECTIONS AND LABELS
# ###################################################################################
from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def print_sections(cfg_dict):
    sections = cfg_dict.get("sections") or []
    for s in sections:
        print(f"  Section Key: {s.get('key')}")
        print(f"    Label: {s.get('label')}")
        fields = s.get("fields") or []
        print(f"    Fields: {[f.get('key') for f in fields]}")
        # print details of headers / sub-headers
        for f in fields:
            if f.get("field_type") == "header":
                print(f"      - Header Key: {f.get('key')}, Label: {f.get('label')}")

def main():
    with SessionLocal() as session:
        # Get sessoes row
        row = session.execute(text("select menu_config from sidebar_menu_settings where menu_key='sessoes'")).scalar()
        if not row:
            print("Sessoes menu config not found.")
            return
            
        cfg = json.loads(row) if isinstance(row, str) else row
        print("=== DEFAULT SESSOES CONFIG ===")
        print_sections(cfg)
        
        # Check overrides
        overrides = cfg.get("entity_scoped_overrides_v1") or {}
        for ent_id, o_cfg in overrides.items():
            print(f"\n=== OVERRIDE FOR ENTITY ID: {ent_id} ===")
            print_sections(o_cfg)

if __name__ == "__main__":
    main()
