# ###################################################################################
# (1) LIST ALL USERS, THEIR EMAILS AND ENTITIES IN THE DB
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    # Query users, their members, and entities
    rows = session.execute(text(
        """
        SELECT u.id AS user_id, u.login_email, m.full_name, me.entity_id, e.name AS entity_name, e.internal_number AS entity_internal_number, me.status AS link_status
        FROM users u
        JOIN members m ON u.member_id = m.id
        LEFT JOIN member_entities me ON m.id = me.member_id
        LEFT JOIN entities e ON me.entity_id = e.id
        """
    )).all()
    
    print("=== USUÁRIOS E SUAS ENTIDADES ===")
    for r in rows:
        print(f"User ID: {r.user_id} | Email: {r.login_email} | Nome: {r.full_name} | Entity ID: {r.entity_id} | Entidade: {r.entity_name} | Nº Cliente: {r.entity_internal_number} | Status Link: {r.link_status}")
