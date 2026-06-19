"""Inspect all members' process_records to find where 1001 contacto_geral records live."""
import json
from appverbo.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as s:
    rows = s.execute(text("""
        SELECT id, full_name, profile_custom_fields
        FROM members
        WHERE profile_custom_fields IS NOT NULL
          AND profile_custom_fields != '{}'
          AND profile_custom_fields::text != 'null'
        ORDER BY id
    """)).fetchall()
    print(f"Members with profile_custom_fields: {len(rows)}")
    for r in rows:
        raw = r[2]
        try:
            fields = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except Exception:
            fields = {}
        proc_keys = [k for k in fields if "process_records" in k]
        if not proc_keys:
            continue
        print(f"  member_id={r[0]} name={r[1]!r} proc_keys={proc_keys}")
        for k in proc_keys:
            recs_raw = fields[k]
            if isinstance(recs_raw, str):
                try:
                    recs = json.loads(recs_raw)
                except Exception:
                    recs = []
            elif isinstance(recs_raw, list):
                recs = recs_raw
            else:
                recs = []
            print(f"    key={k!r} count={len(recs)}")
            for rec in recs:
                vals = rec.get("values", {}) if isinstance(rec, dict) else {}
                n_cli = vals.get("custom_n_cliente", "N/A")
                n_usr = vals.get("custom_n_user", "N/A")
                print(f"      n_user={n_usr!r} n_cliente={n_cli!r} section={rec.get('section_key')!r}")
