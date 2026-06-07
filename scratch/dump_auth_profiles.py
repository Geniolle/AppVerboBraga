import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        # Load entities
        ent_rows = session.execute(text("SELECT id, name FROM entities")).all()
        ent_map = {r.id: r.name for r in ent_rows}
        
        member_rows = session.execute(text("SELECT id, full_name, profile_custom_fields FROM members")).all()
        for m in member_rows:
            links = session.execute(text(
                "SELECT entity_id FROM member_entities WHERE member_id = :mid"
            ), {"mid": m.id}).all()
            ent_names = [ent_map.get(l.entity_id, f"ID {l.entity_id}") for l in links]
            
            if m.profile_custom_fields:
                custom_fields = json.loads(m.profile_custom_fields)
                for key in ["process_records__administrativo", "process_records__perfil_de_autorizacao"]:
                    val = custom_fields.get(key)
                    if val:
                        records = json.loads(val)
                        print("=" * 60)
                        print(f"Member: {m.full_name} | Entities: {ent_names}")
                        print(f"Key: {key}")
                        for r in records:
                            print(f"  Section: {r.get('section_key')}")
                            print(f"  Values: {r.get('values')}")

if __name__ == '__main__':
    main()
