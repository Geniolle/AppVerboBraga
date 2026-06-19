from appverbo.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as s:
    row = s.execute(text("SELECT current_database(), inet_server_addr(), inet_server_port()")).fetchone()
    print(f"DB: {row[0]} | Host: {row[1]} | Port: {row[2]}")
    count = s.execute(text("SELECT COUNT(*) FROM members")).scalar()
    print(f"Total members: {count}")
    row1001 = s.execute(text("""
        SELECT COUNT(*) FROM member_entities me
        JOIN entities e ON e.id = me.entity_id
        WHERE e.internal_number = '1001'
    """)).scalar()
    print(f"Members em entity 1001: {row1001}")
    # List them
    rows = s.execute(text("""
        SELECT m.id, m.full_name, u.login_email
        FROM member_entities me
        JOIN entities e ON e.id = me.entity_id
        JOIN members m ON m.id = me.member_id
        LEFT JOIN users u ON u.member_id = m.id
        WHERE e.internal_number = '1001'
        ORDER BY m.id
    """)).fetchall()
    for r in rows:
        print(f"  member_id={r[0]} name={r[1]!r} email={r[2]!r}")
