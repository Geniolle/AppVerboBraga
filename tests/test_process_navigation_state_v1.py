from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_navigation_state_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    module_snippet = '/static/js/modules/process_navigation_state_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert module_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(module_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage4_wrappers_for_process_navigation_state() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessNavigationStateV1 =" in script_text
    assert "appGenesisProcessNavigationStateV1.configure({" in script_text
    assert "function resolveAdminSelectedTargetV1({" in script_text
    assert (
        "return appGenesisProcessNavigationStateV1.resolveAdminSelectedTargetV1({"
        in script_text
    )
    assert "function getDefaultTargetForMenu(menuKey, config, options = {}) {" in script_text
    assert "return appGenesisProcessNavigationStateV1.getDefaultTargetForMenu(" in script_text
    assert "function hasExplicitAuthProfileContextV1() {" in script_text
    assert "return appGenesisProcessNavigationStateV1.hasExplicitAuthProfileContextV1();" in script_text
    assert "typeof appGenesisProcessNavigationStateV1.resolveStartupMenu === \"function\"" in script_text
    assert "window.__appgenesisGetActiveMenuKeyV1 = function () {" in script_text


def test_process_navigation_state_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_navigation_state_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessNavigationStateV1" in module_text
    assert "configure" in module_text
    assert "resolveAdminSelectedTargetV1" in module_text
    assert "getDefaultTargetForMenu" in module_text
    assert "hasExplicitAuthProfileContextV1" in module_text
    assert "resolveStartupMenu" in module_text
    assert 'menuKey === "perfil_de_autorizacao"' in module_text
    assert 'return "#menu-subprocess-card-active";' in module_text
