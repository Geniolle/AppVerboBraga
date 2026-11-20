from appgenesis.services.process_settings.additional_field_service import (
    normalize_menu_process_additional_fields,
)
from appgenesis.services.process_settings.normalizers import (
    ADDITIONAL_FIELD_BUTTON_STYLE_DEFAULT,
    _normalize_additional_field_button_style,
)


def test_button_style_defaults_and_validates():
    assert _normalize_additional_field_button_style("radio") == "radio"
    assert _normalize_additional_field_button_style(" Segmented ") == "segmented"
    assert _normalize_additional_field_button_style("xpto") == ADDITIONAL_FIELD_BUTTON_STYLE_DEFAULT
    assert _normalize_additional_field_button_style(None) == ADDITIONAL_FIELD_BUTTON_STYLE_DEFAULT


def test_flag_keeps_button_style_and_other_types_do_not():
    items = normalize_menu_process_additional_fields([
        {"label": "Ativo", "field_type": "flag", "button_style": "confirm"},
        {"label": "Nome", "field_type": "text", "button_style": "radio"},
    ])
    flag = next(item for item in items if item["field_type"] == "flag")
    text = next(item for item in items if item["field_type"] == "text")
    assert flag["button_style"] == "confirm"
    assert "button_style" not in text
