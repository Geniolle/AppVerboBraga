from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_menu_config_builder_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    builder_snippet = '/static/js/modules/process_menu_config_builder_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert builder_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(builder_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage3_wrappers_for_process_menu_builder() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessMenuConfigBuilderV1 =" in script_text
    assert "const dynamicProcessDataByMenu = appGenesisProcessMenuConfigBuilderV1" in script_text
    assert "const selectedDynamicSectionByMenu = appGenesisProcessMenuConfigBuilderV1" in script_text
    assert "const menuConfig = appGenesisProcessMenuConfigBuilderV1" in script_text
    assert "function buildStructuredProcessMenuItemsV1(menuKey, dynamicItems = []) {" in script_text
    assert (
        "return appGenesisProcessMenuConfigBuilderV1.buildStructuredProcessMenuItemsV1("
        in script_text
    )
    assert "function mergeDynamicProcessMenus() {" in script_text
    assert "return appGenesisProcessMenuConfigBuilderV1.mergeDynamicProcessMenus();" in script_text
    assert "appGenesisProcessMenuConfigBuilderV1.configure({" in script_text
    assert "appGenesisProcessMenuConfigBuilderV1.initializeMenuConfig();" in script_text


def test_process_menu_config_builder_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_menu_config_builder_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessMenuConfigBuilderV1" in module_text
    assert "configure" in module_text
    assert "initializeMenuConfig" in module_text
    assert "menuConfig" in module_text
    assert "dynamicProcessDataByMenu" in module_text
    assert "selectedDynamicSectionByMenu" in module_text
    assert "buildStructuredProcessMenuItemsV1" in module_text
    assert "mergeDynamicProcessMenus" in module_text
    assert "ensureAuthorizationProfileMenuConfig" in module_text
    assert 'title: "Perfil de autorização"' in module_text
    assert 'target: "#dynamic-process-card"' in module_text
