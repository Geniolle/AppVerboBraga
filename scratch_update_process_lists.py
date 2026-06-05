import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text("SELECT id, menu_key, menu_config FROM sidebar_menu_settings WHERE menu_key IN ('administrativo', 'sessoes')")).all()
    
    admin_cfg = None
    sessoes_cfg = None
    admin_id = None
    sessoes_id = None
    
    for r in rows:
        cfg = json.loads(r.menu_config) if r.menu_config else {}
        if r.menu_key == 'administrativo':
            admin_cfg = cfg
            admin_id = r.id
        elif r.menu_key == 'sessoes':
            sessoes_cfg = cfg
            sessoes_id = r.id
            
    if admin_cfg and sessoes_cfg:
        admin_lists = admin_cfg.get('process_lists', [])
        
        # Find list_processo and list_subprocesso
        processo_item = next((item for item in admin_lists if item.get('key') == 'list_processo'), None)
        subprocesso_item = next((item for item in admin_lists if item.get('key') == 'list_subprocesso'), None)
        
        if processo_item:
            admin_lists.remove(processo_item)
        if subprocesso_item:
            admin_lists.remove(subprocesso_item)
            
        admin_cfg['process_lists'] = admin_lists
        
        sessoes_lists = sessoes_cfg.get('process_lists', [])
        # Only add if not already there
        if processo_item and not any(i.get('key') == 'list_processo' for i in sessoes_lists):
            sessoes_lists.append(processo_item)
        if subprocesso_item and not any(i.get('key') == 'list_subprocesso' for i in sessoes_lists):
            sessoes_lists.append(subprocesso_item)
            
        sessoes_cfg['process_lists'] = sessoes_lists
        
        session.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :cfg WHERE id = :id"),
            {"cfg": json.dumps(admin_cfg), "id": admin_id}
        )
        session.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :cfg WHERE id = :id"),
            {"cfg": json.dumps(sessoes_cfg), "id": sessoes_id}
        )
        session.commit()
        print("Updated DB successfully")
        
    print("Administrativo:", [p.get('key') for p in admin_cfg.get('process_lists', [])])
    print("Sessoes:", [p.get('key') for p in sessoes_cfg.get('process_lists', [])])
