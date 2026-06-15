from appverbo.db.session import SessionLocal
from sqlalchemy import text

with SessionLocal() as s:
    rows = s.execute(text("SELECT id, name, profile_scope, internal_number FROM entities ORDER BY id")).fetchall()
    print("Entities:")
    for r in rows:
        print(f"  id={r[0]} name={r[1]!r} profile_scope={r[2]!r} internal_number={r[3]!r}")
