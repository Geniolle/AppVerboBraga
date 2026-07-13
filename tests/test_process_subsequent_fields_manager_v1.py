from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) CAMPOS SUBSEQUENTES DEVE USAR O CORE REUTILIZAVEL E O TEMPLATE GLOBAL
####################################################################################

def test_process_subsequent_fields_manager_v1_uses_configurable_core_and_search_footer() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_subsequent_fields_manager_v1.js"
    template_path = PROJECT_ROOT / "templates" / "new_user.html"

    script_text = script_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    assert 'core.createConfigurableItemsManager_v1({' in script_text
    assert 'searchInput: "[data-configurable-search]"' in script_text
    assert 'itemName: "campo subsequente"' in script_text
    assert 'itemNamePlural: "campos subsequentes"' in script_text
    assert 'submitNative_v1(form);' in script_text
    assert '["subsequent_field_key", item.key]' in script_text
    assert '["subsequent_trigger_field", item.triggerField]' in script_text
    assert '["subsequent_field", item.fieldKey]' in script_text
    assert '["subsequent_operator", item.operator]' in script_text
    assert '["subsequent_trigger_value", item.triggerValue]' in script_text

    macro_path = PROJECT_ROOT / "templates" / "macros" / "configurable_items_pagination.html"
    macro_text = macro_path.read_text(encoding="utf-8")

    assert 'aria-label="Pesquisar campos subsequentes criados"' in template_text
    assert 'data-process-subsequent-fields-total-label' in template_text
    assert 'render_configurable_items_pagination_footer("data-process-subsequent-fields-page-size", "data-process-subsequent-fields-pagination")' in template_text
    assert 'class="appgenesis-load-more-footer-v1 configurable-items-pagination-footer-v1"' in macro_text
