"""Check contacto_geral records in Docker DB."""
import json
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://postgres:postgres@db:5432/app_igreja")
KEY = "process_records__contacto_geral"

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT id, full_name, profile_custom_fields FROM members "
        "WHERE profile_custom_fields IS NOT NULL AND profile_custom_fields::text != 'null' "
        "ORDER BY id"
    )).fetchall()
    for r in rows:
        fields = json.loads(r[2]) if r[2] else {}
        recs_raw = fields.get(KEY)
        if not recs_raw:
            continue
        recs = json.loads(recs_raw) if isinstance(recs_raw, str) else recs_raw
        print(f"member {r[0]} ({r[1]}): {len(recs)} contacto_geral record(s)")
        for rec in recs:
            vals = rec.get("values", {})
            print(
                f"  n_user={vals.get('custom_n_user')!r} "
                f"n_cliente={vals.get('custom_n_cliente')!r} "
                f"nome={vals.get('custom_nome')!r} "
                f"email={vals.get('custom_email')!r}"
            )

    # Also check sidebar_menu_settings for contacto_geral
    print()
    print("=== sidebar_menu_settings keys ===")
    rows2 = conn.execute(text("SELECT menu_key FROM sidebar_menu_settings ORDER BY menu_key")).fetchall()
    for r in rows2:
        print(f"  {r[0]}")

    # Check field options for contacto_geral
    print()
    for key in ("contacto_geral", "contato"):
        row = conn.execute(text(
            f"SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = '{key}' LIMIT 1"
        )).scalar()
        if row:
            cfg = json.loads(row) if isinstance(row, str) else row
            add_fields = cfg.get("additional_fields") or []
            print(f"=== {key} additional_fields ===")
            for f in add_fields:
                print(f"  [{f.get('field_type')}] key={f.get('key')!r} label={f.get('label')!r}")
