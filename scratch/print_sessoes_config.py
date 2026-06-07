from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

def main():
    with SessionLocal() as session:
        row = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key='sessoes'")).scalar()
        if row:
            parsed = json.loads(row) if isinstance(row, str) else row
            print(json.dumps(parsed, indent=2))
        else:
            print("Not found")

if __name__ == '__main__':
    main()
