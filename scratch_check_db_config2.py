import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text("SELECT menu_key, menu_config FROM sidebar_menu_settings")).all()
    for r in rows:
        cfg = json.loads(r.menu_config) if r.menu_config else {}
        process_lists = cfg.get('process_lists')
        if process_lists:
            print(r.menu_key, "->", [p.get("key") for p in process_lists])
