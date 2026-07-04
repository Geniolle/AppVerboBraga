from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) CAMPOS QUANTIDADE DEVE USAR O CORE REUTILIZAVEL E O TEMPLATE GLOBAL
####################################################################################

def test_process_quantity_fields_manager_v1_uses_configurable_core_and_search_footer() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_quantity_fields_manager_v1.js"
    template_path = PROJECT_ROOT / "templates" / "new_user.html"

    script_text = script_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    assert 'core.createConfigurableItemsManager_v1({' in script_text
    assert 'searchInput: "[data-configurable-search]"' in script_text
    assert 'itemName: "regra"' in script_text
    assert 'itemNamePlural: "regras"' in script_text
    assert 'submitNative_v1(form);' in script_text

    assert 'aria-label="Pesquisar regras criadas"' in template_text
    assert 'data-process-quantity-total-label' in template_text
    assert 'class="appgenesis-load-more-footer-v1 configurable-items-pagination-footer-v1"' in template_text
