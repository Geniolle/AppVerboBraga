# ###################################################################################
# TEST DATABASE SEQUENCE GENERATION
# ###################################################################################
from appverbo.db.session import SessionLocal
from appverbo.models.member import Member, MemberEntity
from appverbo.services.profile import (
    parse_member_profile_fields,
    parse_menu_process_records,
    build_menu_process_records_storage_key,
)
from sqlalchemy import select

def test():
    with SessionLocal() as session:
        # Let's find an active entity
        from appverbo.models.entity import Entity
        active_entity_id = session.scalar(select(Entity.id).limit(1))
        if not active_entity_id:
            print("No entity found in database.")
            return
            
        active_entity_internal_number = session.scalar(
            select(Entity.internal_number).where(Entity.id == active_entity_id)
        )
        print("Active Entity ID:", active_entity_id)
        print("Active Entity Internal Number:", active_entity_internal_number)
        
        # Run our generation logic
        max_seq = 0
        if active_entity_id is not None and active_entity_internal_number is not None:
            records_storage_key = build_menu_process_records_storage_key("contacto_geral")
            members_of_entity = session.scalars(
                select(Member).join(MemberEntity, MemberEntity.member_id == Member.id)
                .where(MemberEntity.entity_id == active_entity_id)
                .where(Member.profile_custom_fields.like(f'%"{records_storage_key}"%'))
            ).all()
            
            print(f"Found {len(members_of_entity)} members with records.")
            target_str = str(active_entity_internal_number).strip()
            for m in members_of_entity:
                m_fields = parse_member_profile_fields(m.profile_custom_fields)
                m_records = parse_menu_process_records(m_fields.get(records_storage_key))
                for r in m_records:
                    r_section = str(r.get("section_key") or "").strip()
                    if r_section == "custom_dados_membresia":
                        r_values = r.get("values") or {}
                        if str(r_values.get("custom_n_cliente") or "").strip() == target_str:
                            val_str = str(r_values.get("custom_n_user") or "").strip()
                            if val_str.isdigit():
                                max_seq = max(max_seq, int(val_str))
        
        next_seq = max_seq + 1
        next_seq_str = f"{next_seq:05d}"
        print("Computed next sequence number:", next_seq_str)

if __name__ == "__main__":
    test()
