from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O RUNTIME DE QUANTIDADE DEVE EXPOR A API CANONICA
####################################################################################

def test_process_quantity_runtime_v1_exposes_expected_api() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "modules" / "process_quantity_runtime_v1.js").read_text(
        encoding="utf-8"
    )

    assert "window.AppGenesisProcessQuantityRuntimeV1" in script_text
    assert "initialize" in script_text
    assert "render" in script_text
    assert "sync" in script_text
    assert "getValues" in script_text
    assert "destroy" in script_text
    assert "normalizeRules" in script_text
    assert "normalizeItems" in script_text
    assert "calculateItemCount" in script_text
    assert "resizeItems" in script_text
    assert "buildFieldMetaMap" in script_text
    assert "serializeItems" in script_text
    assert "deserializeItems" in script_text
    assert "validateRule" in script_text
    assert "createMeuPerfilQuantityAdapterV1" in script_text
    assert "createDynamicProcessQuantityAdapterV1" in script_text


####################################################################################
# (2) O TEMPLATE DEVE CARREGAR O RUNTIME DE QUANTIDADE ANTES DO NEW_USER.JS
####################################################################################

def test_new_user_template_loads_quantity_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    runtime_index = template_text.index('src="/static/js/modules/process_quantity_runtime_v1.js?v=20260714-process-quantity-runtime-v1"')
    new_user_index = template_text.index('src="/static/js/new_user.js')

    assert runtime_index < new_user_index

