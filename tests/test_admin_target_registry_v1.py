from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_admin_target_registry_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    registry_snippet = '/static/js/modules/admin_target_registry_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert registry_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(registry_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage2_wrappers_for_admin_target_registry() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisAdminTargetRegistryV1 =" in script_text
    assert "const NATIVE_ADMIN_TARGETS_V1 = appGenesisAdminTargetRegistryV1" in script_text
    assert "const ESTRUTURAS_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1" in script_text
    assert "const AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1 = appGenesisAdminTargetRegistryV1" in script_text
    assert "const AUTH_PROFILE_NATIVE_TARGETS_V1 = appGenesisAdminTargetRegistryV1" in script_text
    assert "function normalizeAuthorizationProfileTargetV1(value) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget(value);" in script_text
    assert "function authorizationProfileTargetsMatchV1(leftTarget, rightTarget) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch(leftTarget, rightTarget);" in script_text
    assert "function isNativeAdminTargetV1(value) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.isNativeAdminTarget(value);" in script_text
    assert "function isNativeTargetForMenuV1(menuKey, value) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.isNativeTargetForMenu(menuKey, value);" in script_text
    assert "function getAdminSubprocessKeyByTargetV1(target) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.getAdminSubprocessKeyByTarget(target);" in script_text
    assert "function normalizeSubmenuTargetAlias(targetSelector) {" in script_text
    assert "return appGenesisAdminTargetRegistryV1.normalizeSubmenuTargetAlias(targetSelector);" in script_text


def test_admin_target_registry_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "admin_target_registry_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisAdminTargetRegistryV1" in module_text
    assert "configure" in module_text
    assert "NATIVE_ADMIN_TARGETS_V1" in module_text
    assert "ESTRUTURAS_NATIVE_TARGETS_V1" in module_text
    assert "EMPRESA_NATIVE_TARGETS_V1" in module_text
    assert "AUTHORIZATION_PROFILE_TARGET_ALIAS_MAP_V1" in module_text
    assert "AUTH_PROFILE_NATIVE_TARGETS_V1" in module_text
    assert "normalizeAuthorizationProfileTarget" in module_text
    assert "authorizationProfileTargetsMatch" in module_text
    assert "isNativeAdminTarget" in module_text
    assert "isNativeTargetForMenu" in module_text
    assert "getAdminSubprocessKeyByTarget" in module_text
    assert "normalizeSubmenuTargetAlias" in module_text
