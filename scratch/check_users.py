# ###################################################################################
# (1) QUERY DATABASE FOR USERS WITH NAME FROM MEMBERS
# ###################################################################################
import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    rows = session.execute(text(
        "SELECT u.id, u.login_email, m.full_name, u.password_hash "
        "FROM users u "
        "JOIN members m ON u.member_id = m.id"
    )).all()
    for r in rows:
        print(f"ID: {r.id} | Email: {r.login_email} | Name: {r.full_name} | Hash: {r.password_hash}")
