from appverbo.core import SessionLocal
from sqlalchemy import text
import json

def run():
    new_config = {
      "requires_admin": True,
      "visibility_scopes": [
        "owner",
        "legado"
      ],
      "display_order": 17,
      "menu_section": "igreja",
      "sidebar_section": "definicoes",
      "process_fields_seeded_all_v1": True,
      "entity_scoped_overrides_v1": {},
      "additional_fields": [
        {
          "key": "custom_perfil",
          "label": "Perfil",
          "field_type": "list",
          "is_required": True,
          "list_key": "list_perfil",
          "shared_value_key": "list_perfil"
        },
        {
          "key": "custom_objeto_de_autorizacao",
          "label": "Objeto de autorização",
          "field_type": "header",
          "is_required": False
        },
        {
          "key": "custom_processo",
          "label": "Processo",
          "field_type": "list",
          "is_required": True,
          "list_key": "list_processo",
          "shared_value_key": "list_processo"
        },
        {
          "key": "custom_subprocesso",
          "label": "Subprocesso",
          "field_type": "list",
          "is_required": True,
          "list_key": "list_subprocesso",
          "shared_value_key": "list_subprocesso"
        },
        {
          "key": "custom_departamento",
          "label": "Departamento",
          "field_type": "list",
          "is_required": True,
          "list_key": "list_departamento",
          "shared_value_key": "list_departamento"
        }
      ],
      "process_lists": [
        {
          "key": "list_perfil",
          "label": "Perfil",
          "items": [
            "Pastor",
            "Líder de Departamento",
            "Colaborador",
            "Membresia"
          ],
          "items_csv": "Pastor, Líder de Departamento, Colaborador, Membresia",
          "source_key": "manual",
          "source_label": "Manual"
        },
        {
          "key": "list_processo",
          "items": [],
          "label": "Processo",
          "items_csv": "",
          "source_key": "sidebar_sections",
          "source_label": "Sessões (automático)"
        },
        {
          "key": "list_subprocesso",
          "items": [],
          "label": "Subprocesso",
          "items_csv": "",
          "source_key": "sidebar_menus_by_section",
          "source_label": "Subprocesso/Menu por sessão (automático)"
        },
        {
          "key": "list_departamento",
          "items": [],
          "label": "Departamento",
          "items_csv": "",
          "source_key": "table:departments",
          "source_label": "Tabela: Departments (automático)"
        }
      ],
      "process_visible_fields": [
        "custom_perfil",
        "custom_processo",
        "custom_subprocesso",
        "custom_departamento"
      ],
      "process_visible_field_header_map": {
        "custom_perfil": "custom_objeto_de_autorizacao",
        "custom_processo": "custom_objeto_de_autorizacao",
        "custom_subprocesso": "custom_objeto_de_autorizacao",
        "custom_departamento": "custom_objeto_de_autorizacao"
      },
      "process_visible_field_rows": [
        {
          "field_key": "custom_perfil",
          "header_key": "custom_objeto_de_autorizacao"
        },
        {
          "field_key": "custom_processo",
          "header_key": "custom_objeto_de_autorizacao"
        },
        {
          "field_key": "custom_subprocesso",
          "header_key": "custom_objeto_de_autorizacao"
        },
        {
          "field_key": "custom_departamento",
          "header_key": "custom_objeto_de_autorizacao"
        }
      ],
      "process_visible_fields_configured": True,
      "visible_fields": [
        "custom_objeto_de_autorizacao",
        "custom_perfil",
        "custom_processo",
        "custom_subprocesso",
        "custom_departamento"
      ],
      "visible_field_headers": {
        "custom_perfil": "custom_objeto_de_autorizacao",
        "custom_processo": "custom_objeto_de_autorizacao",
        "custom_subprocesso": "custom_objeto_de_autorizacao",
        "custom_departamento": "custom_objeto_de_autorizacao"
      }
    }
    
    with SessionLocal() as session:
        session.execute(
            text("UPDATE sidebar_menu_settings SET menu_config = :config WHERE menu_key = 'perfil_de_autorizacao'"),
            {"config": json.dumps(new_config, ensure_ascii=False)}
        )
        session.commit()
        print("Updated perfil_de_autorizacao settings successfully!")

if __name__ == '__main__':
    run()
