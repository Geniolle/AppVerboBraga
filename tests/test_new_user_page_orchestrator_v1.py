from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_runtime_exposes_page_orchestrator_contract() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "function collectNewUserDomReferencesV1(" in script_text
    assert "function initializeNavigationRuntimeV1(" in script_text
    assert "function initializeProfileRuntimeV1(" in script_text
    assert "function initializeDynamicProcessRuntimeV1(" in script_text
    assert "function initializeAdminRuntimeV1(" in script_text
    assert "function initializeTableRuntimeV1(" in script_text
    assert "function initializeInviteRuntimeV1(" in script_text
    assert "function initializeProcessSettingsRuntimeV1(" in script_text
    assert "function initializePostSaveRuntimeV1(" in script_text
    assert "function initializeNewUserPageV1(" in script_text
    assert "newUserPageBootstrapStateV1.initialized" in script_text
    assert 'window.AppGenesisNewUserPageV1 = Object.freeze({' in script_text
    assert 'appgenesis:new-user-page-ready' in script_text
    assert 'document.addEventListener("DOMContentLoaded", initializeNewUserPageV1, { once: true });' in script_text
