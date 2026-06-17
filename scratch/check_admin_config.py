from appverbo.db.session import SessionLocal
from sqlalchemy import text
import json

with SessionLocal() as s:
    # Check what sidebar_menus_by_section resolves to
    from appverbo.menu_settings import _load_process_list_sidebar_menus_by_section_source_rows_v1
    rows = _load_process_list_sidebar_menus_by_section_source_rows_v1(s)
    print(f"Total sidebar_menus_by_section rows: {len(rows)}")
    for r in rows[:10]:
        print(f"  {r}")
