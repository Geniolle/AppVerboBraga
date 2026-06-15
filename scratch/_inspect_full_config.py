from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as s:
    for mk in ["sessoes", "administrativo"]:
        row = s.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = :k"), {"k": mk}).scalar()
        if not row:
            print(f"{mk}: no config\n")
            continue
        cfg = json.loads(row) if isinstance(row, str) else row
        print(f"=== FULL CONFIG: {mk} ===")
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        print()
