from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as session:
    all_keys = session.execute(text("SELECT menu_key FROM sidebar_menu_settings ORDER BY menu_key")).fetchall()
    print(f"=== sidebar_menu_settings: {len(all_keys)} rows ===")
    for r in all_keys:
        print(f"  {r.menu_key}")

    print()
    row = session.execute(text(
        "SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'contacto_geral' LIMIT 1"
    )).scalar()
    if row:
        cfg = json.loads(row) if isinstance(row, str) else row
        print("=== contacto_geral config ===")
        print(json.dumps(cfg, indent=2, ensure_ascii=False)[:3000])
    else:
        print("No contacto_geral config")

    print()
    members_with = session.execute(text(
        "SELECT id, full_name, profile_custom_fields FROM members "
        "WHERE profile_custom_fields LIKE '%process_records__contacto_geral%'"
    )).fetchall()
    print(f"=== Members with contacto_geral records: {len(members_with)} ===")
    for r in members_with:
        fields = json.loads(r.profile_custom_fields)
        cg_raw = fields.get("process_records__contacto_geral")
        records = json.loads(cg_raw) if cg_raw else []
        for rec in records:
            vals = rec.get("values", {})
            print(f"  member {r.id} ({r.full_name}): keys={sorted(vals.keys())}")
