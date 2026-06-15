from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as s:
    for mk in ["sessoes", "administrativo"]:
        row = s.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = :k"), {"k": mk}).scalar()
        if not row:
            print(f"{mk}: no config")
            continue
        cfg = json.loads(row) if isinstance(row, str) else row
        pvfr = cfg.get("process_visible_field_rows", [])
        pfo = cfg.get("process_field_options", [])
        print(f"=== {mk} ===")
        print(f"  process_visible_field_rows ({len(pvfr)} rows):")
        for r in pvfr:
            print(f"    field_key={str(r.get('field_key', '')):<40} header_key={r.get('header_key', '')!r}")
        print(f"  process_field_options ({len(pfo)} items):")
        for r in pfo:
            print(f"    key={str(r.get('key', '')):<35} label={r.get('label', '')!r}")
        print()
