from appverbo.core import SessionLocal
from appverbo.use_cases.menu.get_menu_edit import execute_get_menu_edit_v1
import json

def run():
    with SessionLocal() as session:
        edit_data = execute_get_menu_edit_v1(session=session, menu_key="meu_perfil")
        print("--- process_selectable_field_options ---")
        for item in edit_data.get("process_selectable_field_options", []):
            if "whatsapp" in item["key"]:
                print(item)
        print("\n--- process_visible_field_rows ---")
        for item in edit_data.get("process_visible_field_rows", []):
            if "whatsapp" in item["field_key"]:
                print(item)

if __name__ == '__main__':
    run()
