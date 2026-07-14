from pathlib import Path

from test_new_user_runtime_functional_v1 import (
    _build_chrome_driver_v1,
    _inject_js_file_v1,
    _load_blank_page_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O CONTRATO DE POS-SAVE DEVE EXPOR A CONSTANTE E OS HELPERS CANONICOS
####################################################################################


def test_post_save_context_contract_v1_exposes_expected_api() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(driver, "<html><body></body></html>")
        _inject_js_file_v1(driver, "static/js/modules/post_save_context_contract_v1.js")

        api = driver.execute_script(
            """
            const contract = window.AppGenesisPostSaveContextContractV1 || {};
            return {
              storageKey: contract.storageKey,
              maxAgeMs: contract.maxAgeMs,
              getCurrentUrl: typeof contract.getCurrentUrl,
              isFeedbackUrl: typeof contract.isFeedbackUrl,
              copyFeedbackParams: typeof contract.copyFeedbackParams,
              clearFeedbackMarkersFromUrl: typeof contract.clearFeedbackMarkersFromUrl,
              hasProtectedReloadContext: typeof contract.hasProtectedReloadContext,
              readStoredContext: typeof contract.readStoredContext,
              storeContext: typeof contract.storeContext
            };
            """
        )

        assert api["storageKey"] == "appgenesis:post-save-context-v3"
        assert api["maxAgeMs"] == 120000
        assert api["getCurrentUrl"] == "function"
        assert api["isFeedbackUrl"] == "function"
        assert api["copyFeedbackParams"] == "function"
        assert api["clearFeedbackMarkersFromUrl"] == "function"
        assert api["hasProtectedReloadContext"] == "function"
        assert api["readStoredContext"] == "function"
        assert api["storeContext"] == "function"
    finally:
        driver.quit()


####################################################################################
# (2) O CAPTURE DE POS-SAVE DEVE REUTILIZAR O CONTRATO PARTILHADO
####################################################################################


def test_post_save_context_capture_v1_reuses_shared_contract() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(driver, "<html><body></body></html>")
        _inject_js_file_v1(driver, "static/js/modules/post_save_context_contract_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/post_save_context_capture_v1.js")

        api = driver.execute_script(
            """
            const capture = window.AppGenesisPostSaveContextCaptureV1 || {};
            return {
              buildCapturedContext: typeof capture.buildCapturedContext,
              captureForm: typeof capture.captureForm,
              bindForm: typeof capture.bindForm,
              initialize: typeof capture.initialize,
              destroy: typeof capture.destroy
            };
            """
        )

        assert api["buildCapturedContext"] == "function"
        assert api["captureForm"] == "function"
        assert api["bindForm"] == "function"
        assert api["initialize"] == "function"
        assert api["destroy"] == "function"
    finally:
        driver.quit()


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

    contract_index = template_text.index('src="/static/js/modules/post_save_context_contract_v1.js?v=20260714-post-save-context-contract-v2"')
    capture_index = template_text.index('src="/static/js/modules/post_save_context_capture_v1.js?v=20260714-post-save-context-contract-v2"')
    guard_index = template_text.index('src="/static/js/modules/navigation_reload_guard_v1.js?v=20260714-post-save-context-contract-v2"')

    assert contract_index < capture_index < guard_index
