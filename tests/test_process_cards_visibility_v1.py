from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_cards_visibility_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    module_snippet = '/static/js/modules/process_cards_visibility_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert module_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(module_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_keeps_stage5_wrappers_for_process_cards_visibility() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessCardsVisibilityV1 =" in script_text
    assert "appGenesisProcessCardsVisibilityV1.configure({" in script_text
    assert "function applyContentForMenu(menuKey) {" in script_text
    assert "return appGenesisProcessCardsVisibilityV1.applyContentForMenu(menuKey);" in script_text
    assert 'function applyContentForMenuTarget(menuKey, targetSelector, source = "unspecified") {' in script_text
    assert "return appGenesisProcessCardsVisibilityV1.applyContentForMenuTarget(" in script_text
    assert "window.activateSubprocessCardsV1 = function (menuKey, targetSelector, source) {" in script_text


def test_process_cards_visibility_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_cards_visibility_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessCardsVisibilityV1" in module_text
    assert "configure" in module_text
    assert "applyContentForMenu" in module_text
    assert "applyContentForMenuTarget" in module_text
    assert "setDynamicProcessCardsVisibility" in module_text
    assert 'card.getAttribute("data-admin-subprocess") === adminSubprocessKey' in module_text
    assert 'card.id === "admin-users-created-card"' in module_text
    assert 'targetSelector === "#dynamic-process-card"' in module_text
