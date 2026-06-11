from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository


# ###################################################################################
# (1) DADOS PADRÃO DE EDIÇÃO
# ###################################################################################


def get_menu_edit_defaults_v1() -> dict[str, Any]:
    return {
        "key": "",
        "menu_key": "",
        "label": "",
        "menu_label": "",
        "status": "active",
        "status_label": "Ativo",
        "visibility_scope_mode": "all",
        "visibility_scope_label": "Default",
        "menu_section": "",
        "menu_section_label": "",
        "menu_config": {},
        "process_additional_fields": [],
        "process_visible_fields": [],
        "process_visible_field_header_map": {},
        "process_visible_field_rows": [],
        "process_field_options": [],
        "process_selectable_field_options": [],
        "process_header_options": [],
        "additional_field_type_options": [],
        "process_owner_fields_enabled": False,
        "process_additional_fields_can_view": False,
        "process_additional_fields_can_edit": False,
        "process_additional_fields_readonly": False,
        "process_additional_fields_source_entity_id": None,
        "process_additional_fields_source_entity_label": "",
        "process_additional_fields_selected_entity_id": None,
        "process_additional_fields_selected_entity_label": "",
        "process_lists": [],
        "process_list_options": [],
        "process_list_source_options": [],
        "process_list_source_tables": [],
        "process_quantity_fields": [],
        "process_subsequent_fields": [],
        "is_active": True,
        "can_delete": False,
        "can_move_up": False,
        "can_move_down": False,
    }


# ###################################################################################
# (2) USE CASE DE OBTENÇÃO PARA EDIÇÃO
# ###################################################################################


def execute_get_menu_edit_v1(
    *,
    session: Session,
    menu_key: str,
    selected_entity_id: object = None,
) -> dict[str, Any]:
    clean_menu_key = str(menu_key or "").strip().lower()

    if not clean_menu_key:
        return get_menu_edit_defaults_v1()

    repository = MenuAdminRepository(MENU_CONFIG)
    row = repository.get_for_edit(
        session=session,
        edit_key=clean_menu_key,
        context={"selected_entity_id": selected_entity_id},
    )

    if row is None:
        return get_menu_edit_defaults_v1()

    return dict(row)
