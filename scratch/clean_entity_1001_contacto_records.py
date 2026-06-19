"""
Remove todos os registos contacto_geral/contato com custom_n_cliente = '1001'
de qualquer membro, independentemente da chave de armazenamento usada.
"""
from appverbo.db.session import SessionLocal
from appverbo.models import Member
from appverbo.services.profile import (
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_menu_process_records,
    serialize_member_profile_fields,
)
from sqlalchemy import select, text

TARGET_N_CLIENTE = "1001"

with SessionLocal() as session:
    # Check DB identity
    row = session.execute(text(
        "SELECT current_database(), inet_server_addr(), inet_server_port()"
    )).fetchone()
    print(f"DB: {row[0]} | Host: {row[1]} | Port: {row[2]}")
    print()

    # Find any member whose profile_custom_fields mentions '1001'
    all_members = session.scalars(
        select(Member).where(
            Member.profile_custom_fields.like('%"1001"%')
        )
    ).all()
    print(f"Membros com referência a '1001' no profile_custom_fields: {len(all_members)}")
    print()

    cleaned_total = 0
    for m in all_members:
        fields = parse_member_profile_fields(m.profile_custom_fields)
        changed = False
        updated_fields = dict(fields)

        # Check every process_records__* key
        for key in list(fields.keys()):
            if not key.startswith("process_records__"):
                continue
            records = parse_menu_process_records(fields.get(key))
            kept = [
                r for r in records
                if str((r.get("values") or {}).get("custom_n_cliente") or "").strip() != TARGET_N_CLIENTE
            ]
            removed = len(records) - len(kept)
            if removed > 0:
                print(f"  member_id={m.id} ({m.full_name!r}) key={key!r}: removendo {removed} registo(s)")
                if kept:
                    updated_fields[key] = serialize_menu_process_records(kept)
                else:
                    updated_fields.pop(key, None)
                changed = True

        if changed:
            m.profile_custom_fields = serialize_member_profile_fields(updated_fields)
            cleaned_total += 1

    session.commit()
    print()
    print(f"Concluído. {cleaned_total} membro(s) limpos de registos com n_cliente=1001.")
