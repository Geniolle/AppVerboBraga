from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_menu_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    module_snippet = '/static/js/modules/process_menu_runtime_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert module_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(module_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage7_wrappers_for_process_menu_runtime() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessMenuRuntimeV1 =" in script_text
    assert "appGenesisProcessMenuRuntimeV1.configure({" in script_text
    assert "function activateMenu(menuKey, options = {}) {" in script_text
    assert "return appGenesisProcessMenuRuntimeV1.activateMenu(menuKey, options);" in script_text
    assert 'function activateMenuTarget(menuKey, targetSelector, source = "unspecified") {' in script_text
    assert "return appGenesisProcessMenuRuntimeV1.activateMenuTarget(" in script_text
    assert "function handleHashNavigation(rawHash) {" in script_text
    assert "return appGenesisProcessMenuRuntimeV1.handleHashNavigation(rawHash);" in script_text
    assert "appGenesisProcessMenuRuntimeV1.bindMenuButtonListeners();" in script_text
    assert "appGenesisProcessMenuRuntimeV1.bindHashChangeListener();" in script_text
    assert "window.__appgenesisGetActiveMenuKeyV1 = function () {" in script_text


def test_process_menu_runtime_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_menu_runtime_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessMenuRuntimeV1" in module_text
    assert "configure" in module_text
    assert "activateMenu" in module_text
    assert "activateMenuTarget" in module_text
    assert "handleHashNavigation" in module_text
    assert "bindMenuButtonListeners" in module_text
    assert "bindHashChangeListener" in module_text
    assert '"#configuracao-account-status-card"' in module_text
    assert '"click:sidebar"' in module_text
