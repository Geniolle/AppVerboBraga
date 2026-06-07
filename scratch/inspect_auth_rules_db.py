# ###################################################################################
# INSPECT DATABASE TABLE PROCESS_VIEW_AUTHORIZATION_RULES
# ###################################################################################
from appverbo.db.session import SessionLocal
from sqlalchemy import text

def main():
    with SessionLocal() as session:
        # Get active entities
        entities_row = session.execute(text("select id, name from entities")).all()
        entity_names = {r[0]: r[1] for r in entities_row}
        
        try:
            print("=== DATABASE TABLE: process_view_authorization_rules ===")
            rules = session.execute(text("select * from process_view_authorization_rules")).mappings().all()
            for r in rules:
                rule_dict = dict(r)
                ent_id = rule_dict.get("entity_id")
                ent_name = entity_names.get(ent_id, "GLOBAL / None")
                print(f"ID: {rule_dict.get('id')}")
                print(f"  Entity: {ent_name} (ID: {ent_id})")
                print(f"  Profile Name: {rule_dict.get('profile_name')}")
                print(f"  Process Key: {rule_dict.get('process_key')}")
                print(f"  Process Label: {rule_dict.get('process_label')}")
                print(f"  Subprocess Key: {rule_dict.get('subprocess_key')}")
                print(f"  Subprocess Label: {rule_dict.get('subprocess_label')}")
                print(f"  Status: {rule_dict.get('status')}")
                print("-" * 40)
        except Exception as e:
            print("Error querying process_view_authorization_rules:", e)

if __name__ == "__main__":
    main()
