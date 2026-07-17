from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) LISTAS DEVE USAR O CORE REUTILIZAVEL E O TEMPLATE GLOBAL
####################################################################################

def test_process_lists_manager_v1_uses_configurable_core_and_search_footer() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_lists_manager_v1.js"
    template_path = PROJECT_ROOT / "templates" / "new_user.html"

    script_text = script_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    assert 'core.createConfigurableItemsManager_v1({' in script_text
    assert 'searchInput: "[data-configurable-search]"' in script_text
    assert 'itemName: "lista"' in script_text
    assert 'itemNamePlural: "listas"' in script_text
    assert 'submitNative_v1(form);' in script_text
    assert 'refreshAutomaticSourceOptions_v1' in script_text
    assert 'isHydratingEditor' in script_text
    assert 'readProcessListAllSessionsKey_v1' in script_text
    assert 'normalizeProcessListSourceSessionOptions_v1' in script_text
    assert 'filterProcessListSourceMenuOptions_v1' in script_text
    assert 'data-process-list-editor-source-session' in script_text
    assert 'data-process-list-editor-source-subprocess' in script_text
    assert 'data-process-list-source-subprocess-map' in script_text
    assert 'Subprocesso indisponível' in script_text
    assert 'processListAllSessionsKey' in template_text
    assert 'processListAllSessionsLabel' in template_text
    assert 'Todas as sessões' in template_text

    macro_path = PROJECT_ROOT / "templates" / "macros" / "configurable_items_pagination.html"
    macro_text = macro_path.read_text(encoding="utf-8")

    assert 'aria-label="Pesquisar listas criadas"' in template_text
    assert 'render_configurable_items_pagination_footer("data-process-lists-page-size", "data-process-lists-pagination")' in template_text
    assert 'class="appgenesis-load-more-footer-v1 configurable-items-pagination-footer-v1"' in macro_text
    assert 'data-process-lists-total-label' in template_text
    assert 'data-process-list-editor-source-session' in template_text
    assert 'process_list_source_subprocess_key' in template_text
    assert '<th>Subprocesso</th>' in template_text
