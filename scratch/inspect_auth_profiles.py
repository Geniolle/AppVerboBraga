# ###################################################################################
# INSPECT AUTHORIZATION PROFILES AND THEIR ENTITY ASSOCIATIONS
# ###################################################################################
from appverbo.db.session import SessionLocal
from appverbo.models import Member, MemberEntity, Entity
from sqlalchemy import select, text
import json

def main():
    with SessionLocal() as session:
        # Get active entities
        entities_row = session.execute(text("select id, name from entities")).all()
        entity_names = {r[0]: r[1] for r in entities_row}
        
        print("=== AUTHORIZATION PROFILES ===")
        members = session.scalars(select(Member).where(Member.profile_custom_fields.like('%process_records__administrativo%'))).all()
        for m in members:
            # find entity of this member
            ent_rows = session.execute(
                select(Entity.id, Entity.name)
                .join(MemberEntity, MemberEntity.entity_id == Entity.id)
                .where(MemberEntity.member_id == m.id)
            ).all()
            entity_str = ", ".join(f"{e.name} (ID: {e.id})" for e in ent_rows)
            
            fields = json.loads(m.profile_custom_fields)
            records = json.loads(fields.get("process_records__administrativo", "[]"))
            print(f"Member: {m.full_name} (Email: {m.email}), Member Entities: {entity_str}")
            for r in records:
                section = r.get("section_key")
                if section == "custom_perfil_de_autorizacao":
                    print(f"  Record ID: {r.get('record_id')}")
                    print(f"    Section: {section}")
                    print(f"    Values: {r.get('values')}")
                    # Let's inspect which entity_id this rule is created under.
                    # Wait, is there a custom_n_cliente (Nº Entidade) or other fields?
                    # Let's print out all keys and values in the record
                    for k, v in r.get("values", {}).items():
                        print(f"      - {k}: {v}")

if __name__ == "__main__":
    main()
