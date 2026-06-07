from appverbo.db.session import SessionLocal
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG

def main():
    repository = MenuAdminRepository(MENU_CONFIG)
    
    with SessionLocal() as session:
        # Check for Entity 8 (Deixa Estar Tech, 1000)
        print("=== LISTING FOR ENTITY 8 (1000) ===")
        res8 = repository.list_menus(session=session, filters=repository._normalize_filters_from_context({"entity_id": 8}))
        rows8 = res8.get("rows", [])
        print(f"Total menus: {len(rows8)}")
        for r in rows8:
            print(f"  Key: {r['key']} | Section: {r['menu_section']} | Scope Entity ID: {r['entity_scope_entity_id']}")
        
        print("\n" + "=" * 50 + "\n")
        
        # Check for Entity 19 (Verbo Braga, 1001)
        print("=== LISTING FOR ENTITY 19 (1001) ===")
        res19 = repository.list_menus(session=session, filters=repository._normalize_filters_from_context({"entity_id": 19}))
        rows19 = res19.get("rows", [])
        print(f"Total menus: {len(rows19)}")
        for r in rows19:
            print(f"  Key: {r['key']} | Section: {r['menu_section']} | Scope Entity ID: {r['entity_scope_entity_id']}")

if __name__ == '__main__':
    main()
