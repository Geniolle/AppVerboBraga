from appverbo.core import SessionLocal
from appverbo.models import SidebarMenuSetting
import json

db = SessionLocal()
sessoes = db.query(SidebarMenuSetting).filter_by(menu_key='sessoes').first()

old_json = """{
    "requires_admin": true, 
    "visibility_scopes": ["owner", "legado"], 
    "additional_fields": [
        {"key": "custom_menu_lateral", "label": "Menu lateral", "field_type": "header", "is_required": false}, 
        {"key": "custom_meu_perfil", "label": "Meu perfil", "field_type": "text", "is_required": true, "size": 255}, 
        {"key": "custom_entidade", "label": "Entidade", "field_type": "list", "is_required": true, "list_key": "list_entidade", "shared_value_key": "list_entidade"}
    ], 
    "visible_fields": ["custom_menu_lateral", "custom_meu_perfil", "custom_entidade", "sessoes", "menu"], 
    "visible_field_headers": {"custom_meu_perfil": "custom_menu_lateral", "custom_entidade": "custom_menu_lateral"}, 
    "display_order": 7, 
    "menu_section": "igreja", 
    "sidebar_section": "definicoes", 
    "process_fields_seeded_all_v1": true, 
    "visibility_scope_mode": "legado", 
    "visibility_scope_label": "Legado", 
    "process_additional_fields_refresh_version": "f1c5f8e4-b15a-4776-95a1-147587cae551", 
    "sidebar_global_refresh_version": "16939bfb-0082-4bd8-a821-79d9a9f48f64", 
    "process_visible_fields": ["custom_meu_perfil", "custom_entidade", "custom_menu_lateral", "sessoes", "menu"], 
    "process_visible_field_header_map": {"custom_meu_perfil": "custom_menu_lateral", "custom_entidade": "custom_menu_lateral"}, 
    "process_visible_field_rows": [
        {"field_key": "custom_menu_lateral", "header_key": ""},
        {"field_key": "custom_meu_perfil", "header_key": "custom_menu_lateral"}, 
        {"field_key": "custom_entidade", "header_key": "custom_menu_lateral"}, 
        {"field_key": "sessoes", "header_key": ""}, 
        {"field_key": "menu", "header_key": ""}
    ], 
    "process_visible_fields_configured": true, 
    "process_lists": [{"key": "list_entidade", "label": "Entidade", "items": [], "items_csv": "", "source_key": "table:entities", "source_label": "Tabela: Entities (automático)"}], 
    "entity_scoped_overrides_v1": {"8": {"menu_label": "Estruturas", "sidebar_section": "sistema"}}
}"""

config = json.loads(old_json)
sessoes.menu_config = json.dumps(config)
db.commit()
print("Restored and updated DB config for sessoes")
