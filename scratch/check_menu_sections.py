# ###################################################################################
# (1) CHECK SESSIONS OF MENU ITEMS IN THE DATABASE
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text(
        "SELECT id, menu_key, menu_label, menu_config FROM sidebar_menu_settings WHERE is_deleted = false"
    )).all()
    
    print("=== SEÇÕES DE CADA MENU (PER ROW) ===")
    for r in rows:
        section = "Não configurada"
        if r.menu_config:
            try:
                cfg = json.loads(r.menu_config)
                section = cfg.get("sidebar_section") or "Não configurada"
                # Check entity specific section overrides
                overrides = cfg.get("entity_scoped_overrides_v1")
                override_info = ""
                if overrides:
                    for ent_id, scope_data in overrides.items():
                        if "sidebar_section" in scope_data:
                            override_info += f" | Override Entidade {ent_id}: {scope_data['sidebar_section']}"
                print(f"Menu: {r.menu_label} (Chave: {r.menu_key}) -> Seção: {section}{override_info}")
            except Exception as e:
                print(f"Menu: {r.menu_label} (Chave: {r.menu_key}) -> Error: {e}")
        else:
            print(f"Menu: {r.menu_label} (Chave: {r.menu_key}) -> Sem config")
