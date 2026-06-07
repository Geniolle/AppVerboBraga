# ###################################################################################
# SCAN MENU SECTIONS AND FIELD LABELS FOR KEYWORDS
# ###################################################################################
from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def search_config(cfg_dict, source):
    # cfg_dict is a dictionary representing menu_config or override config
    sections = cfg_dict.get("sections") or []
    additional_fields = cfg_dict.get("additional_fields") or []
    
    found_matches = []
    
    # 1. Search in sections
    for sec in sections:
        sec_key = str(sec.get("key") or "").lower()
        sec_label = str(sec.get("label") or "").lower()
        if "sess" in sec_label or "sess" in sec_key or "dados gerais" in sec_label or "igreja" in sec_label or "menu" in sec_label:
            found_matches.append(f"Section under {source}: Key={sec.get('key')}, Label='{sec.get('label')}'")
            
    # 2. Search in additional fields
    for f in additional_fields:
        f_key = str(f.get("key") or "").lower()
        f_label = str(f.get("label") or "").lower()
        f_type = str(f.get("field_type") or "").lower()
        if "sess" in f_label or "sess" in f_key or "dados gerais" in f_label or "igreja" in f_label or "menu" in f_label:
            found_matches.append(f"Field under {source}: Key={f.get('key')}, Label='{f.get('label')}' ({f_type})")
            
    return found_matches

def main():
    with SessionLocal() as session:
        # Get active entities
        entities_row = session.execute(text("select id, name from entities")).all()
        entity_names = {r[0]: r[1] for r in entities_row}
        print("Entities:", entity_names)
        
        rows = session.execute(text("select id, menu_key, menu_label, menu_config from sidebar_menu_settings where is_active=true and is_deleted=false")).mappings().all()
        for r in rows:
            menu_key = r["menu_key"]
            menu_label = r["menu_label"]
            cfg = r["menu_config"]
            if not cfg:
                continue
            cfg_dict = json.loads(cfg) if isinstance(cfg, str) else cfg
            
            # Search default config
            matches = search_config(cfg_dict, f"Default Menu '{menu_label}' ({menu_key})")
            for m in matches:
                print(m)
                
            # Search entity overrides
            overrides = cfg_dict.get("entity_scoped_overrides_v1") or {}
            for ent_id_str, o_cfg in overrides.items():
                ent_id = int(ent_id_str)
                ent_name = entity_names.get(ent_id, f"Unknown Entity {ent_id}")
                matches_override = search_config(o_cfg, f"Override for Entity '{ent_name}' (ID: {ent_id}) under Menu '{menu_label}'")
                for mo in matches_override:
                    print(mo)
                    
        # Let's also check the actual records scoped to "sessoes" to see if they hold data
        print("\n=== RECORD CHECKS ===")
        members = session.execute(text("select id, full_name, profile_custom_fields from members")).mappings().all()
        for m in members:
            fields = m["profile_custom_fields"]
            if not fields:
                continue
            fields_dict = json.loads(fields)
            
            # Check custom records for sessoes
            sessoes_records = fields_dict.get("process_records__sessoes")
            if sessoes_records:
                parsed = json.loads(sessoes_records)
                print(f"Member: {m['full_name']} has process_records__sessoes:")
                for r in parsed:
                    print(f"  Record Section: {r.get('section_key')}, Values: {r.get('values')}")
                    
            # Check other process records
            for k, v in fields_dict.items():
                if k.startswith("process_records__") and k != "process_records__sessoes":
                    parsed = json.loads(v)
                    for r in parsed:
                        r_vals = r.get("values") or {}
                        # If any key/value contains keywords
                        for r_k, r_v in r_vals.items():
                            if any(x in str(r_v).lower() for x in ("sess", "dados gerais", "igreja", "menu")):
                                print(f"Member: {m['full_name']}, Process: {k}, Record Section: {r.get('section_key')} has matching value: {r_k}={r_v}")

if __name__ == "__main__":
    main()
