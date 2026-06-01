from appverbo.core import SessionLocal, templates
from appverbo.services.menu_admin_context import build_menu_admin_context_v1, build_menu_admin_page_payload_v1
import json

def run():
    with SessionLocal() as session:
        # Fetching context as a mock admin user
        menu_admin_context = build_menu_admin_context_v1(
            session=session,
            actor_user_id=1,  # Assuming user ID 1 exists and is admin
            actor_login_email="admin@example.com",
            selected_entity_id=1,
            menu_edit_key="meu_perfil",
        )
        payload = build_menu_admin_page_payload_v1(menu_admin_context)
        
        settings_edit_data = None
        candidate_menu_edit_data = dict(payload.get("menu_edit_data", {}))
        if str(candidate_menu_edit_data.get("key") or "").strip():
            settings_edit_data = candidate_menu_edit_data
        else:
            for row in payload.get("menu_settings", []):
                row_key = str(row.get("key", "")).strip().lower()
                if row_key == "meu_perfil":
                    settings_edit_data = dict(row)
                    break
        
        if not settings_edit_data:
            print("ERROR: settings_edit_data not found")
            return

        # Render process fields config block
        # simulated render
        settings_process_select_options = settings_edit_data.get("process_selectable_field_options", [])
        settings_process_visible_field_rows = settings_edit_data.get("process_visible_field_rows", [])
        settings_process_field_options = settings_edit_data.get("process_field_options", [])
        
        print("--- settings_process_visible_field_rows count:", len(settings_process_visible_field_rows))
        found_row = False
        for field_row in settings_process_visible_field_rows:
            config_field_key = field_row.get("field_key")
            config_header_key = field_row.get("header_key")
            if config_field_key == "autorizacao_whatsapp":
                found_row = True
                print(f"Found config row in HTML: field_key={config_field_key}, header_key={config_header_key}")
        
        if not found_row:
            print("ERROR: autorizacao_whatsapp not found in settings_process_visible_field_rows!")

        print("\n--- settings_process_select_options count:", len(settings_process_select_options))
        found_option = False
        for option in settings_process_select_options:
            if option["key"] == "autorizacao_whatsapp":
                found_option = True
                print(f"Found option in dropdown: key={option['key']}, label={option['label']}")
        
        if not found_option:
            print("ERROR: autorizacao_whatsapp not found in settings_process_select_options!")

if __name__ == '__main__':
    run()
