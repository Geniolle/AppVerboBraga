import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        row = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'administrativo'")).scalar()
        if row:
            cfg = json.loads(row) if isinstance(row, str) else row
            print("=== SIDEBAR SECTIONS IN ADMINISTRATIVO ===")
            print(json.dumps(cfg.get("sidebar_sections"), indent=2, ensure_ascii=False))
            print("=== OVERRIDES IN ADMINISTRATIVO ===")
            print(json.dumps(cfg.get("entity_scoped_overrides_v1"), indent=2, ensure_ascii=False))
        else:
            print("No administrativo menu config found.")

if __name__ == '__main__':
    main()
