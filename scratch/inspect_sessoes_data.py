# ###################################################################################
# INSPECT SESSOES CONFIG AND RECORDS
# ###################################################################################
import json
from appverbo.db.session import SessionLocal
from appverbo.models import Member, MemberEntity, Entity
from sqlalchemy import select, text

def main():
    with SessionLocal() as session:
        # 1. Get raw config for sessoes
        sessoes_row = session.execute(text("select menu_config from sidebar_menu_settings where menu_key='sessoes'")).scalar()
        if sessoes_row:
            cfg = json.loads(sessoes_row) if isinstance(sessoes_row, str) else sessoes_row
            print("=== sessoes default sections ===")
            sections = cfg.get("sections") or []
            for sec in sections:
                print(f"Section key: {sec.get('key')}, Label: {sec.get('label')}")
                # print first few fields
                fields = sec.get("fields") or []
                print(f"  Fields count: {len(fields)}")
                for f in fields[:3]:
                    print(f"    - Field key: {f.get('key')}, Label: {f.get('label')}, Type: {f.get('field_type')}")
        
        # 2. Get records for sessoes
        print("\n=== sessoes records in member profiles ===")
        members = session.scalars(select(Member).where(Member.profile_custom_fields.like('%process_records__sessoes%'))).all()
        print(f"Found {len(members)} members with sessoes records.")
        for m in members:
            # find entity of this member
            entities = session.execute(
                select(Entity.id, Entity.name)
                .join(MemberEntity, MemberEntity.entity_id == Entity.id)
                .where(MemberEntity.member_id == m.id)
            ).all()
            entity_str = ", ".join(f"{e.name} (ID: {e.id})" for e in entities)
            
            fields = json.loads(m.profile_custom_fields)
            records = json.loads(fields.get("process_records__sessoes", "[]"))
            print(f"Member: {m.full_name} (Email: {m.email}), Linked Entities: {entity_str}")
            for r in records:
                print(f"  Record ID: {r.get('record_id')}")
                print(f"    Created at: {r.get('created_at')}")
                print(f"    Section: {r.get('section_key')}")
                print(f"    Values: {r.get('values')}")

if __name__ == "__main__":
    main()
