from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O RUNTIME DE CAMPOS SUBSEQUENTES DEVE EXPOR A API CANONICA
####################################################################################

def test_process_subsequent_visibility_runtime_v1_exposes_expected_api() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "process_subsequent_visibility_runtime_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisProcessSubsequentVisibilityRuntimeV1" in script_text
    assert "initialize" in script_text
    assert "evaluate" in script_text
    assert "apply" in script_text
    assert "refresh" in script_text
    assert "destroy" in script_text
    assert "normalizeRules" in script_text
    assert "normalizeOperator" in script_text
    assert "normalizeComparableValue" in script_text
    assert "evaluateRule" in script_text
    assert "evaluateRules" in script_text
    assert "getHiddenTargets" in script_text
    assert "isEmptyValue" in script_text
    assert "collectProfileValues" in script_text
    assert "getProfileForm" in script_text
    assert "getCurrentProfileSection" in script_text
    assert "resolveControlName" in script_text
    assert "readControlValue" in script_text


####################################################################################
# (2) O NEW_USER.JS DEVE DELEGAR A RESOLUCAO DE SUBSEQUENTES AO RUNTIME
####################################################################################

def test_new_user_runtime_delegates_subsequent_visibility_to_runtime() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "window.AppGenesisProcessSubsequentVisibilityRuntimeV1" in script_text
    assert "normalizeProcessSubsequentOperator(value)" in script_text
    assert "appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeOperator(value)" in script_text
    assert "appGenesisProcessSubsequentVisibilityRuntimeV1.normalizeRules(rawRules)" in script_text
    assert "appGenesisProcessSubsequentVisibilityRuntimeV1.getHiddenTargets(rules, valuesByField)" in script_text
    assert "appGenesisProcessSubsequentVisibilityRuntimeV1.refresh({" in script_text


####################################################################################
# (3) O TEMPLATE DEVE CARREGAR O RUNTIME ANTES DO NEW_USER.JS
####################################################################################

def test_new_user_template_loads_subsequent_visibility_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    runtime_index = template_text.index('src="/static/js/modules/process_subsequent_visibility_runtime_v1.js?v=20260714-process-subsequent-visibility-v1"')
    new_user_index = template_text.index('src="/static/js/new_user.js')

    assert runtime_index < new_user_index
