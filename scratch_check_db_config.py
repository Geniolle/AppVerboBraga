import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text("SELECT menu_key, menu_config FROM sidebar_menu_settings WHERE menu_key IN ('administrativo', 'sessoes')")).all()
    for r in rows:
        cfg = json.loads(r.menu_config)
        print(r.menu_key, "->", cfg.get('process_lists'))
