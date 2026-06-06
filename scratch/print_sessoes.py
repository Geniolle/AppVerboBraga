import json
from appverbo.core import SessionLocal
from sqlalchemy import text

with SessionLocal() as session:
    r = session.execute(text("SELECT menu_config FROM sidebar_menu_settings WHERE menu_key='administrativo'")).fetchone()
    if r:
        config = json.loads(r[0])
        sections = config.get("sidebar_sections", [])
        print("--- SIDEBAR SECTIONS ---")
        for s in sections:
            print(s)
    else:
        print("No administrativo menu setting found")
