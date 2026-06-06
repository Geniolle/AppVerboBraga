# ###################################################################################
# (1) DETAILED QUERY OF SESSIONS (SIDEBAR SECTIONS) & OVERRIDES BY ENTITY
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    # 1. Load entities database mapping
    entity_rows = session.execute(text("SELECT id, name, internal_number, profile_scope, is_active FROM entities")).all()
    entity_map = {r.id: {"name": r.name, "internal_number": r.internal_number, "profile_scope": r.profile_scope, "is_active": r.is_active} for r in entity_rows}
    
    print("=== MAPA DE ENTIDADES NO BANCO ===")
    for eid, info in entity_map.items():
        print(f"ID: {eid} | Nome: {info['name']} | Nº Cliente: {info['internal_number']} | Scope: {info['profile_scope']} | Active: {info['is_active']}")
    print("=" * 60)
    
    # 2. Query administrative menu config
    row = session.execute(text(
        "SELECT menu_config FROM sidebar_menu_settings WHERE lower(trim(menu_key)) = 'administrativo' LIMIT 1"
    )).fetchone()
    
    if not row or not row[0]:
        print("Configuração de menu 'administrativo' não encontrada!")
        exit(1)
        
    cfg = json.loads(row[0])
    
    # 3. Print Global Sidebar Sections
    print("\n=== SESSÕES GLOBAIS (DEFAULT) ===")
    if "sidebar_sections" in cfg:
        for sec in cfg["sidebar_sections"]:
            print(f"Chave: {sec.get('key')} | Nome: {sec.get('label')} | Scope: {sec.get('visibility_scope_mode')} | Status: {sec.get('status') or sec.get('section_status')}")
    else:
        print("Sem sessões globais.")
    print("=" * 60)
    
    # 4. Print Entity-Scoped Sidebar Sections (Overrides)
    print("\n=== SESSÕES POR ENTIDADE (OVERRIDES) ===")
    overrides = cfg.get("entity_scoped_overrides_v1")
    if overrides and isinstance(overrides, dict):
        for ent_id_str, scope_data in overrides.items():
            ent_id = int(ent_id_str) if ent_id_str.isdigit() else None
            info = entity_map.get(ent_id, {"name": f"Desconhecida (ID {ent_id})", "internal_number": "-", "profile_scope": "-", "is_active": "-"})
            print(f"\nEntidade: {info['name']} | ID: {ent_id} | Nº Cliente: {info['internal_number']} | Scope: {info['profile_scope']} | Active: {info['is_active']}")
            
            if "sidebar_sections" in scope_data:
                for sec in scope_data["sidebar_sections"]:
                    print(f"  - Chave: {sec.get('key')} | Nome: {sec.get('label')} | Scope: {sec.get('visibility_scope_mode')} | Status: {sec.get('status') or sec.get('section_status')}")
            else:
                print("  (Sem sessões específicas configuradas)")
    else:
        print("Sem overrides por entidade no JSON.")
    print("=" * 60)
