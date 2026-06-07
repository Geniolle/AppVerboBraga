import json
from appverbo.core import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        r = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key = 'administrativo'")).scalar()
        cfg = json.loads(r)
        print("Raw sidebar_sections in DB:")
        print(json.dumps(cfg.get("sidebar_sections"), indent=2, ensure_ascii=False))
        print("Raw overrides in DB:")
        print(json.dumps(cfg.get("entity_scoped_overrides_v1"), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
