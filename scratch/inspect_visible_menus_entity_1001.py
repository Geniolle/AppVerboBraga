from appverbo.db.session import SessionLocal
from appverbo.menu_settings import get_sidebar_menu_settings, get_visible_sidebar_menu_keys
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        settings = get_sidebar_menu_settings(session, selected_entity_id=19)
        print("=== DETAILED RESOLVED SETTINGS FOR ENTITY 1001 (19) ===")
        for s in settings:
            print(f"Key: {s['key']} | Label: {s['label']}")
            print(f"  sidebar_section_key: {s.get('sidebar_section_key')}")
            print(f"  sidebar_section_status: {s.get('sidebar_section_status')}")
            print(f"  sidebar_section_is_active: {s.get('sidebar_section_is_active')}")
            print(f"  sidebar_section_visibility_scopes: {s.get('sidebar_section_visibility_scopes')}")
            print(f"  entity_scope_entity_id: {s.get('entity_scope_entity_id')}")
            print(f"  visibility_scopes: {s.get('visibility_scopes')}")

if __name__ == '__main__':
    main()
