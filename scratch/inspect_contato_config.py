"""Inspect the full config for contato/contacto_geral in sidebar_menu_settings."""
import json
from appverbo.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    for key in ("contacto_geral", "contato"):
        row = session.execute(text(
            f"SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = '{key}' LIMIT 1"
        )).scalar()
        if row:
            cfg = json.loads(row) if isinstance(row, str) else row
            print(f"=== {key} config ===")
            add_fields = cfg.get("additional_fields") or []
            print(f"additional_fields ({len(add_fields)} entries):")
            for f in add_fields:
                ftype = f.get("field_type", "")
                fkey = f.get("key", "")
                flabel = f.get("label", "")
                print(f"  [{ftype}] key={fkey!r} label={flabel!r}")
            print()
            pvfr = cfg.get("process_visible_field_rows") or []
            print(f"process_visible_field_rows ({len(pvfr)} entries):")
            for r in pvfr:
                print(f"  field_key={r.get('field_key')!r} header_key={r.get('header_key')!r}")
            print()
        else:
            print(f"No config for key={key!r}")
            print()
