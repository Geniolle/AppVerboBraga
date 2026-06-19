from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as session:
    # All members + users + entities
    print("=== ALL members + their entities ===")
    rows = session.execute(text(
        "SELECT m.id as member_id, m.full_name, u.login_email, u.account_status,"
        " e.id as entity_id, e.name as entity_name, e.internal_number, e.profile_scope,"
        " me.status as me_status"
        " FROM members m"
        " LEFT JOIN users u ON u.member_id = m.id"
        " LEFT JOIN member_entities me ON me.member_id = m.id"
        " LEFT JOIN entities e ON e.id = me.entity_id"
        " ORDER BY m.id, e.id"
    )).fetchall()
    for r in rows:
        print("  member=" + str(r.member_id)
              + "  name=" + repr(r.full_name)
              + "  email=" + repr(r.login_email)
              + "  status=" + repr(r.account_status)
              + "  entity=" + repr(r.entity_name)
              + "  (" + str(r.internal_number) + "/" + str(r.profile_scope) + ")"
              + "  me_status=" + repr(r.me_status))

    print()
    print("=== profile_custom_fields summary (all members) ===")
    all_members = session.execute(text("SELECT id, full_name, profile_custom_fields FROM members ORDER BY id")).fetchall()
    for m in all_members:
        if m.profile_custom_fields:
            try:
                fields = json.loads(m.profile_custom_fields)
                cg_key = "process_records__contacto_geral"
                cg_raw = fields.get(cg_key)
                if cg_raw:
                    records = json.loads(cg_raw)
                    print("  member " + str(m.id) + " (" + str(m.full_name) + "): "
                          + str(len(records)) + " contacto_geral records")
                    for rec in records:
                        vals = rec.get("values", {})
                        print("    section=" + str(rec.get("section_key"))
                              + "  n_user=" + str(vals.get("custom_n_user"))
                              + "  n_cliente=" + str(vals.get("custom_n_cliente")))
                else:
                    other_keys = [k for k in fields if not k.startswith("process_records__")]
                    print("  member " + str(m.id) + " (" + str(m.full_name) + "): no contacto_geral | other keys=" + str(list(fields.keys())[:5]))
            except Exception as ex:
                print("  member " + str(m.id) + ": parse error: " + str(ex))
        else:
            print("  member " + str(m.id) + " (" + str(m.full_name) + "): NULL profile_custom_fields")
