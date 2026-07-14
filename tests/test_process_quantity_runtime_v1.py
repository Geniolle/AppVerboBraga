from pathlib import Path

from test_new_user_runtime_functional_v1 import (
    _build_chrome_driver_v1,
    _inject_js_file_v1,
    _load_blank_page_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O RUNTIME DE QUANTIDADE DEVE EXPOR A API CANONICA EM EXECUCAO
####################################################################################


def test_process_quantity_runtime_v1_exposes_expected_api() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(driver, "<html><body></body></html>")
        _inject_js_file_v1(driver, "static/js/modules/profile_field_registry_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_quantity_runtime_v1.js")

        api = driver.execute_script(
            """
            const runtime = window.AppGenesisProcessQuantityRuntimeV1 || {};
            return {
              initialize: typeof runtime.initialize,
              render: typeof runtime.render,
              sync: typeof runtime.sync,
              getValues: typeof runtime.getValues,
              destroy: typeof runtime.destroy,
              createMeuPerfilQuantityAdapterV1: typeof runtime.createMeuPerfilQuantityAdapterV1,
              createDynamicProcessQuantityAdapterV1: typeof runtime.createDynamicProcessQuantityAdapterV1
            };
            """
        )

        assert api == {
            "initialize": "function",
            "render": "function",
            "sync": "function",
            "getValues": "function",
            "destroy": "function",
            "createMeuPerfilQuantityAdapterV1": "function",
            "createDynamicProcessQuantityAdapterV1": "function",
        }
    finally:
        driver.quit()


####################################################################################
# (2) O TEMPLATE DEVE CARREGAR O RUNTIME DE QUANTIDADE ANTES DO NEW_USER.JS
####################################################################################

def test_new_user_template_loads_quantity_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    runtime_index = template_text.index('src="/static/js/modules/process_quantity_runtime_v1.js?v=20260714-process-quantity-runtime-v2"')
    new_user_index = template_text.index('src="/static/js/new_user.js')

    assert runtime_index < new_user_index
