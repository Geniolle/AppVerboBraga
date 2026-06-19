"""
Test that _build_bootstrap_values_from_member_v1 matches field_key even when label is empty.
Simulates what happens when visible_rows provides the section_fields.
"""
import sys
sys.path.insert(0, "c:\\workspace\\AppVerboBraga")

from appverbo.db.session import SessionLocal
from appverbo.models import Member
from appverbo.services.page import (
    _build_bootstrap_values_from_member_v1,
    _aggregate_contacto_geral_for_entity_v1,
)
from sqlalchemy import select

# Simulate visible_rows that would come from process_visible_field_rows
# These field_keys are typical for a contacto_geral form
simulated_visible_rows = [
    {"field_key": "custom_n_user", "header_key": "custom_dados_membresia"},
    {"field_key": "custom_nome", "header_key": "custom_dados_membresia"},
    {"field_key": "custom_telefone", "header_key": "custom_dados_membresia"},
    {"field_key": "custom_email", "header_key": "custom_dados_membresia"},
    {"field_key": "custom_n_cliente", "header_key": "custom_dados_membresia"},
]

section_fields = [
    {"field_key": str(r.get("field_key") or "").strip().lower(), "label": ""}
    for r in simulated_visible_rows
    if isinstance(r, dict) and str(r.get("field_key") or "").strip()
]

print("=== section_fields from visible_rows ===")
for sf in section_fields:
    print(f"  {sf}")
print()

with SessionLocal() as session:
    member = session.get(Member, 2)  # Teste Web User
    if member:
        print(f"Member: {member.full_name}, phone={member.primary_phone}, email={member.email}")
        base_values = {"custom_n_user": "00001", "custom_n_cliente": "1001"}
        result = _build_bootstrap_values_from_member_v1(member, section_fields, base_values)
        print(f"Bootstrap result: {result}")
    else:
        print("Member 2 not found")
    print()

    # Now test the full aggregate with visible_rows
    # First, check entity 1001 members
    from appverbo.models import MemberEntity, Entity
    entity = session.scalar(
        select(Entity).where(Entity.internal_number == "1001").limit(1)
    )
    if entity:
        print(f"Entity 1001: id={entity.id}, name={entity.name}")
        history_storage_key = "process_records__contacto_geral"
        rows = _aggregate_contacto_geral_for_entity_v1(
            session, entity.id, history_storage_key, simulated_visible_rows
        )
        print(f"Aggregate returned {len(rows)} record(s):")
        for r in rows:
            vals = r.get("values", {})
            print(f"  section={r.get('section_key')} values_keys={sorted(vals.keys())}")
            for k, v in sorted(vals.items()):
                print(f"    {k} = {v!r}")
    else:
        print("Entity with internal_number 1001 not found")
