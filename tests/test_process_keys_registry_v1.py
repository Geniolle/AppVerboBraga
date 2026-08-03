from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_keys_registry_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    registry_snippet = '/static/js/modules/process_keys_registry_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert registry_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(registry_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage1_wrappers_for_process_keys_registry() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const MEU_PERFIL_MENU_KEY = appGenesisProcessKeysRegistryV1" in script_text
    assert "const LEGACY_DOCUMENTOS_MENU_KEY = appGenesisProcessKeysRegistryV1" in script_text
    assert "const ESTRUTURAS_MENU_KEY_V1 = appGenesisProcessKeysRegistryV1" in script_text
    assert "const EMPRESA_MENU_KEY_V1 = appGenesisProcessKeysRegistryV1" in script_text
    assert "function normalizeMenuKey(value) {" in script_text
    assert "return appGenesisProcessKeysRegistryV1.normalizeMenuKey(value);" in script_text
    assert "function normalizeSettingsTabKey(value) {" in script_text
    assert "return appGenesisProcessKeysRegistryV1.normalizeSettingsTabKey(value);" in script_text
    assert "function normalizeTargetV1(value) {" in script_text
    assert "return appGenesisProcessKeysRegistryV1.normalizeTarget(value);" in script_text


def test_process_keys_registry_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_keys_registry_v1.js"
    ).read_text(encoding="utf-8")

    assert "window.AppGenesisProcessKeysRegistryV1".replace("window.", "global.") in module_text
    assert "MEU_PERFIL_MENU_KEY" in module_text
    assert "LEGACY_DOCUMENTOS_MENU_KEY" in module_text
    assert "ESTRUTURAS_MENU_KEY_V1" in module_text
    assert "EMPRESA_MENU_KEY_V1" in module_text
    assert "normalizeMenuKey" in module_text
    assert "normalizeSettingsTabKey" in module_text
    assert "normalizeTarget" in module_text
