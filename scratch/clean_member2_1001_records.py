"""Remove contacto_geral records with custom_n_cliente=1001 from member 2."""
import json
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://postgres:postgres@db:5432/app_igreja")
KEY = "process_records__contacto_geral"

with engine.connect() as conn:
    row = conn.execute(text(
        "SELECT id, full_name, profile_custom_fields FROM members WHERE id = 2"
    )).fetchone()

    if not row:
        print("Member 2 not found")
    else:
        fields = json.loads(row[2]) if row[2] else {}
        recs_raw = fields.get(KEY)
        if not recs_raw:
            print("No contacto_geral records in member 2")
        else:
            recs = json.loads(recs_raw) if isinstance(recs_raw, str) else recs_raw
            print(f"Before: {len(recs)} record(s)")
            kept = [
                r for r in recs
                if str((r.get("values") or {}).get("custom_n_cliente") or "").strip() != "1001"
            ]
            removed = len(recs) - len(kept)
            print(f"Removing {removed} record(s) with n_cliente=1001")

            if kept:
                fields[KEY] = json.dumps(kept)
            else:
                fields.pop(KEY, None)

            conn.execute(
                text("UPDATE members SET profile_custom_fields = :v WHERE id = 2"),
                {"v": json.dumps(fields)}
            )
            conn.commit()
            print("Done.")

    # Verify
    row2 = conn.execute(text(
        "SELECT profile_custom_fields FROM members WHERE id = 2"
    )).scalar()
    fields2 = json.loads(row2) if row2 else {}
    recs2_raw = fields2.get(KEY)
    recs2 = json.loads(recs2_raw) if isinstance(recs2_raw, str) else (recs2_raw or [])
    print(f"\nAfter: {len(recs2)} contacto_geral record(s) in member 2")
    for r in recs2:
        vals = r.get("values", {})
        print(f"  n_user={vals.get('custom_n_user')!r} n_cliente={vals.get('custom_n_cliente')!r} nome={vals.get('custom_nome')!r}")
