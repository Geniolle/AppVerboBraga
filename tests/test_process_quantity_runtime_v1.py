from pathlib import Path

from tests.test_new_user_runtime_functional_v1 import (
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
# (2) O RUNTIME DE QUANTIDADE DEVE USAR DELEGACAO E SUPORTAR MULTIPLAS REGRAS
####################################################################################


def test_process_quantity_runtime_v1_delegates_events_and_handles_multiple_rules_v1() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <section id="perfil-pessoal-card">
                  <div class="profile-readonly">
                    <div class="personal-grid"></div>
                  </div>
                  <form class="profile-edit-form" method="post" action="/users/profile/personal">
                    <div class="personal-grid">
                      <div class="field">
                        <label for="quantidade_a">Quantidade A</label>
                        <input id="quantidade_a" name="quantidade_a" type="number" value="1">
                      </div>
                      <div class="field">
                        <label for="quantidade_b">Quantidade B</label>
                        <input id="quantidade_b" name="quantidade_b" type="number" value="1">
                      </div>
                    </div>
                  </form>
                </section>
              </body>
            </html>
            """,
        )
        driver.execute_script(
            """
            window.AppGenesisProfileFieldRegistryV1 = {
              resolveControlName(fieldKey) {
                return String(fieldKey || "");
              },
              collectProfileValues() {
                return {};
              },
              getCurrentProfileSection() {
                return "dados";
              }
            };
            """
        )
        _inject_js_file_v1(driver, "static/js/modules/process_quantity_runtime_v1.js")

        driver.execute_script(
            """
            const setting = {
              process_quantity_fields: [
                {
                  key: "rule_a",
                  quantity_field_key: "quantidade_a",
                  repeated_field_keys: ["telefone_a"],
                  header_key: "dados",
                  max_items: 3,
                  item_label: "Contacto A"
                },
                {
                  key: "rule_b",
                  quantity_field_key: "quantidade_b",
                  repeated_field_keys: ["telefone_b"],
                  header_key: "dados",
                  max_items: 3,
                  item_label: "Contacto B"
                }
              ],
              process_field_options: [
                { key: "quantidade_a", label: "Quantidade A", field_type: "number" },
                { key: "quantidade_b", label: "Quantidade B", field_type: "number" },
                { key: "telefone_a", label: "Telefone A", field_type: "text" },
                { key: "telefone_b", label: "Telefone B", field_type: "text" }
              ]
            };
            const form = document.querySelector(".profile-edit-form");
            const readonlyGridEl = document.querySelector(".profile-readonly .personal-grid");
            const editGridEl = document.querySelector(".profile-edit-form .personal-grid");
            window.__quantityContextV1 = {
              mode: "profile",
              adapterName: "profile",
              root: document,
              formEl: form,
              readonlyGridEl,
              editGridEl,
              setting,
              rules: setting.process_quantity_fields,
              valuesByRule: {
                rule_a: [{ telefone_a: "111" }],
                rule_b: [{ telefone_b: "222" }]
              },
              getSetting: () => setting,
              getValues() {
                return {
                  rule_a: [{ telefone_a: "111" }],
                  rule_b: [{ telefone_b: "222" }]
                };
              },
              getCurrentSection: () => "dados"
            };
            window.AppGenesisProcessQuantityRuntimeV1.initialize(window.__quantityContextV1);
            """
        )

        initial_state = driver.execute_script(
            """
            const state = window.__quantityContextV1.__appGenesisProcessQuantityRuntimeV1 || {};
            const hiddenA = document.querySelector("input[name='process_quantity_payload__rule_a']");
            const hiddenB = document.querySelector("input[name='process_quantity_payload__rule_b']");
            return {
              listenerCount: Array.isArray(state.listeners) ? state.listeners.length : -1,
              ruleACount: document.querySelectorAll("[data-process-quantity-rule-key='rule_a'] .profile-quantity-item-v1").length,
              ruleBCount: document.querySelectorAll("[data-process-quantity-rule-key='rule_b'] .profile-quantity-item-v1").length,
              hiddenA: hiddenA ? hiddenA.value : null,
              hiddenB: hiddenB ? hiddenB.value : null
            };
            """
        )

        assert initial_state["listenerCount"] == 3
        assert initial_state["ruleACount"] == 1
        assert initial_state["ruleBCount"] == 1
        assert initial_state["hiddenA"] == '[{"telefone_a":"111"}]'
        assert initial_state["hiddenB"] == '[{"telefone_b":"222"}]'

        driver.execute_script(
            """
            const hidden = document.querySelector("input[name='process_quantity_payload__rule_a']");
            let writes = 0;
            let stored = hidden.value;
            Object.defineProperty(hidden, "value", {
              configurable: true,
              get() {
                return stored;
              },
              set(next) {
                writes += 1;
                stored = String(next);
              }
            });
            window.__hiddenWritesRuleA = () => writes;
            const control = document.getElementById("quantidade_a");
            control.value = "2";
            control.dispatchEvent(new Event("input", { bubbles: true }));
            """
        )

        after_single_event = driver.execute_script(
            """
            return {
              ruleACount: document.querySelectorAll("[data-process-quantity-rule-key='rule_a'] .profile-quantity-item-v1").length,
              hiddenWritesRuleA: window.__hiddenWritesRuleA()
            };
            """
        )

        assert after_single_event["hiddenWritesRuleA"] == 1
        assert after_single_event["ruleACount"] == 2

        driver.execute_script(
            """
            const control = document.getElementById("quantidade_b");
            control.value = "2";
            control.dispatchEvent(new Event("input", { bubbles: true }));
            """
        )

        after_multiple_rules = driver.execute_script(
            """
            return {
              ruleBCount: document.querySelectorAll("[data-process-quantity-rule-key='rule_b'] .profile-quantity-item-v1").length,
            };
            """
        )

        assert after_multiple_rules["ruleBCount"] == 2
    finally:
        driver.quit()


####################################################################################
# (2) O TEMPLATE DEVE CARREGAR O RUNTIME DE QUANTIDADE ANTES DO NEW_USER.JS
####################################################################################

def test_new_user_template_loads_quantity_runtime_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    runtime_index = template_text.index('src="/static/js/modules/process_quantity_runtime_v1.js?v=20260714-process-quantity-runtime-v3"')
    new_user_index = template_text.index('src="/static/js/new_user.js')

    assert runtime_index < new_user_index
