from appgenesis.services.process_settings.field_service import (
    get_menu_process_field_options,
    get_menu_process_header_options,
    get_menu_process_selectable_field_options,
)


def test_header_in_additional_fields_keeps_builtin_process_fields():
    menu_config = {
        "additional_fields": [
            {"key": "custom_dados_da_empresa", "label": "Dados da empresa", "field_type": "header", "is_required": False}
        ]
    }

    option_keys = [item["key"] for item in get_menu_process_field_options("empresa", menu_config)]
    selectable_keys = [item["key"] for item in get_menu_process_selectable_field_options("empresa", menu_config)]
    header_keys = [item["key"] for item in get_menu_process_header_options("empresa", menu_config)]

    assert option_keys == ["dados_gerais", "morada", "custom_dados_da_empresa"]
    assert selectable_keys == ["dados_gerais", "morada"]
    assert header_keys == ["custom_dados_da_empresa"]
