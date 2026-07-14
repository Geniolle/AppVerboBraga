from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O CONTRATO DE POS-SAVE DEVE EXPOR A CONSTANTE E OS HELPERS CANONICOS
####################################################################################

def test_post_save_context_contract_v1_exposes_expected_api() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "post_save_context_contract_v1.js").read_text(
        encoding="utf-8"
    )

    assert 'storageKey: STORAGE_KEY' in script_text
    assert 'maxAgeMs: MAX_AGE_MS' in script_text
    assert 'getCurrentUrl' in script_text
    assert 'isFeedbackUrl' in script_text
    assert 'copyFeedbackParams' in script_text
    assert 'clearFeedbackMarkersFromUrl' in script_text
    assert 'hasProtectedReloadContext' in script_text
    assert 'readStoredContext' in script_text
    assert 'storeContext' in script_text


####################################################################################
# (2) O CAPTURE DE POS-SAVE DEVE REUTILIZAR O CONTRATO PARTILHADO
####################################################################################

def test_post_save_context_capture_v1_reuses_shared_contract() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "post_save_context_capture_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisPostSaveContextContractV1" in script_text
    assert "buildCapturedContext" in script_text
    assert "captureForm" in script_text
    assert "storeContext(context)" in script_text


####################################################################################
# (3) O RELOAD GUARD DEVE CONSEGUIR CONSUMIR O CONTRATO NOVO
####################################################################################

def test_navigation_reload_guard_consumes_post_save_contract_when_present() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "navigation_reload_guard_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisPostSaveContextContractV1" in script_text
    assert "appGenesisPostSaveContextContractV1" in script_text
    assert "readStoredContext()" in script_text
    assert "hasProtectedReloadContext(url)" in script_text


####################################################################################
# (4) O TEMPLATE DEVE CARREGAR O CONTRATO ANTES DO GUARD
####################################################################################

def test_new_user_template_loads_post_save_contract_before_navigation_guard() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    contract_index = template_text.index('src="/static/js/modules/post_save_context_contract_v1.js?v=20260714-post-save-context-contract-v1"')
    capture_index = template_text.index('src="/static/js/modules/post_save_context_capture_v1.js?v=20260714-post-save-context-contract-v1"')
    guard_index = template_text.index('src="/static/js/modules/navigation_reload_guard_v1.js?v=20260714-post-save-context-contract-v1"')

    assert contract_index < capture_index < guard_index

