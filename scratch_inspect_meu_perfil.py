from appverbo.core import SessionLocal
from appverbo.use_cases.menu.get_menu_edit import execute_get_menu_edit_v1
import json

def run():
    with SessionLocal() as session:
        edit_data = execute_get_menu_edit_v1(session=session, menu_key="meu_perfil")
        print("Subsequent rules:")
        print(json.dumps(edit_data.get("process_subsequent_rules", []), indent=2, ensure_ascii=False))
        print("Subsequent fields:")
        print(json.dumps(edit_data.get("process_subsequent_fields", []), indent=2, ensure_ascii=False))
        print("process_visible_field_rows:")
        print(json.dumps(edit_data.get("process_visible_field_rows", []), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
