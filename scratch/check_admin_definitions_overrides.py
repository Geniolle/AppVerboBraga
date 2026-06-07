from appverbo.db.session import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        # Check rows where entity_id is not null
        rows = session.execute(text("SELECT id, entity_id, parameter_name, parameter_type, initial_value, process_name, subprocess_name, status FROM admin_definitions WHERE entity_id IS NOT NULL")).mappings().all()
        print(f"Total admin_definitions rows with entity_id: {len(rows)}")
        for r in rows:
            print(f"ID: {r['id']}")
            print(f"  Entity ID: {r['entity_id']}")
            print(f"  Parameter Name: {r['parameter_name']}")
            print(f"  Process Name: {r['process_name']}")
            print(f"  Subprocess Name: {r['subprocess_name']}")
            print(f"  Status: {r['status']}")
            print("-" * 40)

if __name__ == '__main__':
    main()
