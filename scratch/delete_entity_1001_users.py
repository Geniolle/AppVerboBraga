"""
Apaga todos os utilizadores/membros da entidade com internal_number = '1001'.
Também limpa os registos contacto_geral que referenciam '1001' em outros membros.
"""
import json
from appverbo.db.session import SessionLocal
from appverbo.models import Member, MemberEntity, Entity
from appverbo.models.user import User
from appverbo.services.profile import (
    parse_member_profile_fields,
    parse_menu_process_records,
    serialize_menu_process_records,
    serialize_member_profile_fields,
    build_menu_process_records_storage_key,
)
from sqlalchemy import select, text

ENTITY_INTERNAL_NUMBER = "1001"
RECORDS_KEY = build_menu_process_records_storage_key("contacto_geral")

with SessionLocal() as session:
    # Find entity via raw SQL (avoids ORM column mismatch)
    entity_row = session.execute(
        text("SELECT id, name, internal_number FROM entities WHERE internal_number = :n LIMIT 1"),
        {"n": ENTITY_INTERNAL_NUMBER},
    ).fetchone()
    if entity_row is None:
        print(f"Entidade {ENTITY_INTERNAL_NUMBER} não encontrada.")
        raise SystemExit(0)

    entity_id = int(entity_row.id)
    print(f"Entidade: id={entity_id} name={entity_row.name!r} internal_number={entity_row.internal_number}")
    print()

    # Find all members of this entity
    members = session.scalars(
        select(Member)
        .join(MemberEntity, MemberEntity.member_id == Member.id)
        .where(MemberEntity.entity_id == entity_id)
    ).all()

    print(f"Membros a apagar ({len(members)}):")
    member_ids_to_delete = set()
    for m in members:
        user = session.scalar(select(User).where(User.member_id == m.id))
        print(f"  member_id={m.id} name={m.full_name!r} user_id={getattr(user,'id',None)} email={getattr(user,'login_email',None)!r}")
        member_ids_to_delete.add(int(m.id))
    print()

    # --- Delete in correct order (FK constraints) ---

    # 1. Delete User records
    deleted_users = 0
    for m in members:
        user = session.scalar(select(User).where(User.member_id == m.id))
        if user:
            session.delete(user)
            deleted_users += 1
    session.flush()
    print(f"Utilizadores apagados: {deleted_users}")

    # 2. Delete MemberEntity records for this entity
    me_rows = session.scalars(
        select(MemberEntity).where(MemberEntity.entity_id == entity_id)
    ).all()
    for me in me_rows:
        session.delete(me)
    session.flush()
    print(f"MemberEntity links apagados: {len(me_rows)}")

    # 3. Delete Member records (only those who were exclusively in this entity)
    deleted_members = 0
    for m in members:
        # Check if member still has other entity links
        other_links = session.scalar(
            select(MemberEntity).where(MemberEntity.member_id == m.id).limit(1)
        )
        if other_links is None:
            session.delete(m)
            deleted_members += 1
        else:
            print(f"  member_id={m.id} mantido (tem outras entidades)")
    session.flush()
    print(f"Members apagados: {deleted_members}")

    # 4. Clean contacto_geral records referencing this entity from OTHER members
    all_members = session.scalars(
        select(Member).where(Member.profile_custom_fields.like(f'%"{RECORDS_KEY}"%'))
    ).all()
    cleaned = 0
    for m in all_members:
        if int(m.id) in member_ids_to_delete:
            continue
        fields = parse_member_profile_fields(m.profile_custom_fields)
        records = parse_menu_process_records(fields.get(RECORDS_KEY))
        kept = [
            r for r in records
            if str((r.get("values") or {}).get("custom_n_cliente") or "").strip() != ENTITY_INTERNAL_NUMBER
        ]
        if len(kept) < len(records):
            updated = dict(fields)
            if kept:
                updated[RECORDS_KEY] = serialize_menu_process_records(kept)
            else:
                updated.pop(RECORDS_KEY, None)
            m.profile_custom_fields = serialize_member_profile_fields(updated)
            print(f"  member_id={m.id} ({m.full_name}): removidos {len(records)-len(kept)} registo(s) contacto_geral para entity 1001")
            cleaned += 1

    session.commit()
    print()
    print(f"Concluído. {deleted_users} user(s), {deleted_members} member(s) apagados, {cleaned} membro(s) limpos de referências à entity 1001.")
