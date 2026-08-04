from pathlib import Path

from tests.test_new_user_runtime_functional_v1 import (
    _build_chrome_driver_v1,
    _inject_js_file_v1,
    _load_blank_page_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O RUNTIME DE CAMPOS SUBSEQUENTES DEVE EXPOR A API CANONICA EM EXECUCAO
####################################################################################


def test_process_subsequent_visibility_runtime_v1_exposes_expected_api() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(driver, "<html><body></body></html>")
        _inject_js_file_v1(driver, "static/js/modules/profile_field_registry_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_subsequent_visibility_runtime_v1.js")

        api = driver.execute_script(
            """
            const runtime = window.AppGenesisProcessSubsequentVisibilityRuntimeV1 || {};
            return {
              initialize: typeof runtime.initialize,
              evaluate: typeof runtime.evaluate,
              apply: typeof runtime.apply,
              refresh: typeof runtime.refresh,
              destroy: typeof runtime.destroy,
              normalizeRules: typeof runtime.normalizeRules,
              normalizeOperator: typeof runtime.normalizeOperator,
              normalizeComparableValue: typeof runtime.normalizeComparableValue,
              evaluateRule: typeof runtime.evaluateRule,
              evaluateRules: typeof runtime.evaluateRules,
              getHiddenTargets: typeof runtime.getHiddenTargets,
              isEmptyValue: typeof runtime.isEmptyValue,
              collectProfileValues: typeof runtime.collectProfileValues,
              getProfileForm: typeof runtime.getProfileForm,
              getCurrentProfileSection: typeof runtime.getCurrentProfileSection,
              resolveControlName: typeof runtime.resolveControlName,
              readControlValue: typeof runtime.readControlValue
            };
            """
        )

        assert api["initialize"] == "function"
        assert api["evaluate"] == "function"
        assert api["apply"] == "function"
        assert api["refresh"] == "function"
        assert api["destroy"] == "function"
        assert api["normalizeRules"] == "function"
        assert api["normalizeOperator"] == "function"
        assert api["normalizeComparableValue"] == "function"
        assert api["evaluateRule"] == "function"
        assert api["evaluateRules"] == "function"
        assert api["getHiddenTargets"] == "function"
        assert api["isEmptyValue"] == "function"
        assert api["collectProfileValues"] == "function"
        assert api["getProfileForm"] == "function"
        assert api["getCurrentProfileSection"] == "function"
        assert api["resolveControlName"] == "function"
        assert api["readControlValue"] == "function"
    finally:
        driver.quit()


####################################################################################
# (2) O TEMPLATE DEVE CARREGAR O RUNTIME ANTES DO NEW_USER.JS
####################################################################################

def test_new_user_template_loads_subsequent_visibility_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    runtime_index = template_text.index('src="/static/js/modules/process_subsequent_visibility_runtime_v1.js?v=20260714-process-subsequent-visibility-v2"')
    new_user_index = template_text.index('src="/static/js/new_user.js')

    assert runtime_index < new_user_index
