import json
import uuid
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        # Load administrativo menu config
        row = session.execute(text(
            "SELECT id, menu_config FROM sidebar_menu_settings WHERE menu_key = 'administrativo'"
        )).fetchone()
        
        if not row:
            print("Administrativo menu not found!")
            return
            
        menu_id, menu_config_str = row
        cfg = json.loads(menu_config_str) if isinstance(menu_config_str, str) else menu_config_str
        
        print("=== BEFORE ===")
        print("Global Sections:")
        for s in cfg.get("sidebar_sections", []):
            print(f"  - Key: {s.get('key')}, Label: {s.get('label')}")
        print("Entity Overrides:")
        print(json.dumps(cfg.get("entity_scoped_overrides_v1"), indent=2, ensure_ascii=False))
        
        # Extract and remove 'dados_gerais' and 'igreja' from global list
        global_sections = cfg.get("sidebar_sections", [])
        new_global_sections = []
        extracted_sections = []
        
        for s in global_sections:
            if s.get("key") in ["dados_gerais", "igreja"]:
                extracted_sections.append(s)
            else:
                new_global_sections.append(s)
                
        cfg["sidebar_sections"] = new_global_sections
        
        # Prepare entity 19 override
        overrides = cfg.get("entity_scoped_overrides_v1")
        if not overrides:
            overrides = {}
            cfg["entity_scoped_overrides_v1"] = overrides
            
        if "19" not in overrides:
            overrides["19"] = {}
            
        # Add the extracted sections to entity 19 override
        # Make sure visibility_scope_mode is set appropriately (e.g. 'all')
        for s in extracted_sections:
            s["visibility_scope_mode"] = "all"
            s["visibility_scopes"] = ["owner", "legado"]
            s["visibility_scope_label"] = "Default"
            
        overrides["19"]["sidebar_sections"] = extracted_sections
        
        # Update refresh version
        cfg["sidebar_global_refresh_version"] = str(uuid.uuid4())
        
        print("\n=== AFTER ===")
        print("Global Sections:")
        for s in cfg.get("sidebar_sections", []):
            print(f"  - Key: {s.get('key')}, Label: {s.get('label')}")
        print("Entity Overrides:")
        print(json.dumps(cfg.get("entity_scoped_overrides_v1"), indent=2, ensure_ascii=False))
        
        # Persist back
        session.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :cfg WHERE id = :id"),
            {"cfg": json.dumps(cfg, ensure_ascii=False), "id": menu_id}
        )
        session.commit()
        print("\nSuccessfully updated administrativo menu_config!")

if __name__ == '__main__':
    main()
