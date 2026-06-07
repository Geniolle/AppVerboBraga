import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        # Load entities
        ent_rows = session.execute(text("SELECT id, name FROM entities")).all()
        ent_map = {r.id: r.name for r in ent_rows}
        
        # Load members and their linked entities
        member_rows = session.execute(text("SELECT id, full_name, profile_custom_fields FROM members")).all()
        for m in member_rows:
            # Get linked entities for this member
            links = session.execute(text(
                "SELECT entity_id FROM member_entities WHERE member_id = :mid"
            ), {"mid": m.id}).all()
            ent_names = [ent_map.get(l.entity_id, f"ID {l.entity_id}") for l in links]
            
            if m.profile_custom_fields:
                try:
                    custom_fields = json.loads(m.profile_custom_fields)
                    for key, val in custom_fields.items():
                        if key.startswith("process_records__"):
                            records = json.loads(val) if isinstance(val, str) else val
                            if records:
                                print("="*80)
                                print(f"Membro: {m.full_name} | Entidades: {ent_names}")
                                print(f"Processo (Chave Customizada): {key}")
                                print(json.dumps(records, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"Error parsing for member {m.full_name}: {e}")

if __name__ == '__main__':
    main()
