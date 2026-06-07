import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        row = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'sessoes'")).scalar()
        if row:
            cfg = json.loads(row) if isinstance(row, str) else row
            print(json.dumps(cfg, indent=2, ensure_ascii=False))
        else:
            print("No sessoes menu config found.")

if __name__ == '__main__':
    main()
