"""
Remove contacto_geral records that only have custom_n_user + custom_n_cliente
(the empty bootstrap records). The aggregate will re-create them with full member
data on the next page load.
"""
from appverbo.db.session import SessionLocal
from appverbo.models import Member
from appverbo.services.profile import (
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_menu_process_records,
    serialize_member_profile_fields,
    build_menu_process_records_storage_key,
)
from sqlalchemy import select, text

RECORDS_KEY = build_menu_process_records_storage_key("contacto_geral")
BOOTSTRAP_ONLY_KEYS = {"custom_n_user", "custom_n_cliente"}

with SessionLocal() as session:
    members = session.scalars(
        select(Member).where(Member.profile_custom_fields.like(f'%"{RECORDS_KEY}"%'))
    ).all()

    fixed = 0
    for m in members:
        existing_fields = parse_member_profile_fields(m.profile_custom_fields)
        existing_records = parse_menu_process_records(existing_fields.get(RECORDS_KEY))

        kept = []
        removed = []
        for rec in existing_records:
            vals = rec.get("values") or {}
            val_keys = set(vals.keys())
            # Keep if it has more than just the two bootstrap keys
            if val_keys - BOOTSTRAP_ONLY_KEYS:
                kept.append(rec)
            else:
                removed.append(rec)

        if not removed:
            continue

        print(f"  member {m.id} ({m.full_name}): removing {len(removed)} empty record(s), keeping {len(kept)}")
        updated_fields = dict(existing_fields)
        if kept:
            serialized = serialize_menu_process_records(kept)
            updated_fields[RECORDS_KEY] = serialized
        else:
            updated_fields.pop(RECORDS_KEY, None)

        result = serialize_member_profile_fields(updated_fields)
        m.profile_custom_fields = result
        fixed += 1

    session.commit()
    print(f"\nDone. Cleaned {fixed} member(s).")
