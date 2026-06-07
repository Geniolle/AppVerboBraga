import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        rows = session.execute(text("SELECT id, menu_key, menu_label, menu_config FROM sidebar_menu_settings WHERE is_active=true AND is_deleted=false")).all()
        for r in rows:
            print("="*60)
            print(f"ID: {r.id} | Key: {r.menu_key} | Label: {r.menu_label}")
            if r.menu_config:
                try:
                    cfg = json.loads(r.menu_config)
                    # Let's clean or abbreviate huge arrays to keep output readable
                    if "sections" in cfg:
                        print(f"  Sections ({len(cfg['sections'])}):")
                        for s in cfg["sections"]:
                            print(f"    - Key: {s.get('key')}, Label: {s.get('label')}")
                            fields = s.get("fields") or []
                            print(f"      Fields ({len(fields)}):")
                            for f in fields:
                                print(f"        * Key: {f.get('key')}, Label: {f.get('label')}, Type: {f.get('field_type')}")
                    if "process_lists" in cfg:
                        print(f"  Process Lists: {cfg['process_lists']}")
                    if "entity_scoped_overrides_v1" in cfg:
                        print("  Entity Scopes Overrides:")
                        for k, v in cfg["entity_scoped_overrides_v1"].items():
                            print(f"    * Entity: {k}")
                            if "sections" in v:
                                for s in v["sections"]:
                                    print(f"      - Section Key: {s.get('key')}, Label: {s.get('label')}")
                                    fields = s.get("fields") or []
                                    for f in fields:
                                        print(f"        * Field Key: {f.get('key')}, Label: {f.get('label')}, Type: {f.get('field_type')}")
                            if "process_lists" in v:
                                print(f"      - Process Lists: {v['process_lists']}")
                except Exception as e:
                    print(f"  Error parsing: {e}")

if __name__ == '__main__':
    main()
