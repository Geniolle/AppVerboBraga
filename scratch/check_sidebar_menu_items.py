from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    try:
        res = session.execute(text("SELECT * FROM sidebar_menu_items"))
        print("Columns:", list(res.keys()))
        r = res.all()
        print(f"Found {len(r)} rows:")
        for row in r:
            print(dict(row._mapping))
    except Exception as e:
        print(f"Error: {e}")
