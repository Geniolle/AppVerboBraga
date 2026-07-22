from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_submenu_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    module_snippet = '/static/js/modules/process_submenu_runtime_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert module_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(module_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage6_wrappers_for_process_submenu_runtime() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessSubmenuRuntimeV1 =" in script_text
    assert "let topSubmenuController = null;" in script_text
    assert "appGenesisProcessSubmenuRuntimeV1.createTopSubmenuController({" in script_text
    assert "appGenesisProcessSubmenuRuntimeV1.configure({" in script_text
    assert "function clearSubmenuActiveLinks(links) {" in script_text
    assert "return appGenesisProcessSubmenuRuntimeV1.clearSubmenuActiveLinks(links);" in script_text
    assert 'function setActiveSubmenu(targetSelector, selectedLinkEl = null) {' in script_text
    assert "appGenesisProcessSubmenuRuntimeV1.setActiveSubmenu(" in script_text
    assert "function renderSubmenu(menuKey) {" in script_text
    assert "return appGenesisProcessSubmenuRuntimeV1.renderSubmenu(menuKey);" in script_text


def test_process_submenu_runtime_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_submenu_runtime_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessSubmenuRuntimeV1" in module_text
    assert "configure" in module_text
    assert "createTopSubmenuController" in module_text
    assert "clearSubmenuActiveLinks" in module_text
    assert "setActiveSubmenu" in module_text
    assert "renderSubmenu" in module_text
    assert "AppGenesisTopSubmenu" in module_text
    assert '"click:submenu-tab"' in module_text
