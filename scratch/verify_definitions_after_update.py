from appverbo.db.session import SessionLocal
from appverbo.services.admin_definition_scope import list_admin_definitions_in_scope_v1

def main():
    with SessionLocal() as session:
        # Check for Entity 8 (1000)
        print("=== DEFINITIONS FOR ENTITY 8 (1000) ===")
        defs8 = list_admin_definitions_in_scope_v1(session, selected_entity_id=8)
        print(f"Total definitions in scope: {len(defs8)}")
        # Check how many belong to Dados gerais or Igreja
        count_dados_gerais_igreja8 = sum(1 for d in defs8 if d.process_name in ('Dados gerais', 'Igreja'))
        print(f"Definitions belonging to Dados gerais or Igreja: {count_dados_gerais_igreja8}")
        
        print("\n" + "=" * 50 + "\n")
        
        # Check for Entity 19 (1001)
        print("=== DEFINITIONS FOR ENTITY 19 (1001) ===")
        defs19 = list_admin_definitions_in_scope_v1(session, selected_entity_id=19)
        print(f"Total definitions in scope: {len(defs19)}")
        # Check how many belong to Dados gerais or Igreja
        count_dados_gerais_igreja19 = sum(1 for d in defs19 if d.process_name in ('Dados gerais', 'Igreja'))
        print(f"Definitions belonging to Dados gerais or Igreja: {count_dados_gerais_igreja19}")
        for d in defs19:
            if d.process_name in ('Dados gerais', 'Igreja'):
                print(f"  ID: {d.id} | Process: {d.process_name} | Subprocess: {d.subprocess_name} | Entity ID: {d.entity_id}")

if __name__ == '__main__':
    main()
