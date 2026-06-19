"""
Backfill initial contacto_geral record for members who have none.
Creates a minimal custom_dados_membresia record per entity membership.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from appverbo.db.session import SessionLocal
from appverbo.models import Member, MemberEntity, Entity
from appverbo.services.profile import (
    build_menu_process_records_storage_key,
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_menu_process_records,
    serialize_member_profile_fields,
)
from sqlalchemy import select

RECORDS_KEY = build_menu_process_records_storage_key("contacto_geral")


def get_max_seq(session, entity_id: int, target_str: str) -> int:
    members = session.scalars(
        select(Member)
        .join(MemberEntity, MemberEntity.member_id == Member.id)
        .where(MemberEntity.entity_id == entity_id)
        .where(Member.profile_custom_fields.like(f'%"{RECORDS_KEY}"%'))
    ).all()
    max_seq = 0
    for m in members:
        m_fields = parse_member_profile_fields(m.profile_custom_fields)
        for r in parse_menu_process_records(m_fields.get(RECORDS_KEY)):
            if str(r.get("section_key") or "").strip() == "custom_dados_membresia":
                rv = r.get("values") or {}
                if str(rv.get("custom_n_cliente") or "").strip() == target_str:
                    val = str(rv.get("custom_n_user") or "").strip()
                    if val.isdigit():
                        max_seq = max(max_seq, int(val))
    return max_seq


def backfill():
    with SessionLocal() as session:
        # All members + their entity memberships
        rows = session.execute(
            select(Member.id, Member.full_name, MemberEntity.entity_id)
            .join(MemberEntity, MemberEntity.member_id == Member.id)
            .order_by(Member.id, MemberEntity.entity_id)
        ).fetchall()

        processed = 0
        for row in rows:
            member_id = row.id
            entity_id = row.entity_id

            entity_internal_number = session.scalar(
                select(Entity.internal_number).where(Entity.id == entity_id)
            )
            if entity_internal_number is None:
                print(f"  skip member={member_id} entity={entity_id}: no internal_number")
                continue

            target_str = str(entity_internal_number).strip()

            member = session.get(Member, member_id)
            existing_fields = parse_member_profile_fields(member.profile_custom_fields)
            existing_records = parse_menu_process_records(existing_fields.get(RECORDS_KEY))

            # Check if already has a record for this entity
            already_has = any(
                str(r.get("section_key") or "").strip() == "custom_dados_membresia"
                and str((r.get("values") or {}).get("custom_n_cliente") or "").strip() == target_str
                for r in existing_records
            )
            if already_has:
                print(f"  skip member={member_id} ({row.full_name}) entity={entity_id} ({target_str}): already has record")
                continue

            next_seq = get_max_seq(session, entity_id, target_str) + 1
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            new_record = {
                "section_key": "custom_dados_membresia",
                "created_at": now_str,
                "values": {
                    "custom_n_user": f"{next_seq:05d}",
                    "custom_n_cliente": target_str,
                },
            }

            updated_records = existing_records + [new_record]
            updated_fields = dict(existing_fields)
            serialized = serialize_menu_process_records(updated_records)
            if serialized:
                updated_fields[RECORDS_KEY] = serialized
                member.profile_custom_fields = serialize_member_profile_fields(updated_fields)
                session.flush()
                print(f"  created record for member={member_id} ({row.full_name}) entity={entity_id} ({target_str}) n_user={new_record['values']['custom_n_user']}")
                processed += 1

        session.commit()
        print(f"\nDone. {processed} records created.")


if __name__ == "__main__":
    backfill()
