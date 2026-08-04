from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_chrome_driver_v1() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1200")
    options.add_argument("--no-sandbox")
    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Selenium Chrome indisponivel neste ambiente: {exc}")


def _load_blank_page_v1(driver: webdriver.Chrome, html: str) -> None:
    driver.get("about:blank")
    driver.execute_script(
        """
        const html = arguments[0];
        document.open();
        document.write(html);
        document.close();
        """,
        html,
    )


def _inject_js_file_v1(driver: webdriver.Chrome, relative_path: str) -> None:
    script_text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    driver.execute_script(script_text)


def _install_fake_session_storage_v1(driver: webdriver.Chrome) -> None:
    driver.execute_script(
        """
        const store = new Map();
        Object.defineProperty(window, "sessionStorage", {
          configurable: true,
          value: {
            getItem(key) {
              return store.has(String(key)) ? store.get(String(key)) : null;
            },
            setItem(key, value) {
              store.set(String(key), String(value));
            },
            removeItem(key) {
              store.delete(String(key));
            },
            clear() {
              store.clear();
            }
          }
        });
        """
    )


####################################################################################
# (1) QUANTITY: O RUNTIME CANONICO DEVE RENDERIZAR E SINCRONIZAR O JSON REAL
####################################################################################


def test_process_quantity_runtime_renders_and_syncs_profile_payload_v1() -> None:
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
                      <div class="field" data-profile-field-key="nome">
                        <label for="full_name">Quantidade</label>
                        <input id="full_name" name="full_name" type="number" value="2">
                      </div>
                    </div>
                  </form>
                </section>
              </body>
            </html>
            """,
        )
        _inject_js_file_v1(driver, "static/js/modules/profile_field_registry_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_quantity_runtime_v1.js")

        driver.execute_script(
            """
            const setting = {
              process_quantity_fields: [
                {
                  key: "rule1",
                  quantity_field_key: "nome",
                  repeated_field_keys: ["telefone"],
                  header_key: "dados",
                  max_items: 3,
                  item_label: "Contacto",
                  label: "Contactos"
                }
              ],
              process_field_options: [
                { key: "telefone", label: "Telefone", field_type: "text" }
              ]
            };
            window.__quantityContextV1 = {
              mode: "profile",
              adapterName: "profile",
              root: document,
              formEl: document.querySelector(".profile-edit-form"),
              readonlyGridEl: document.querySelector(".profile-readonly .personal-grid"),
              editGridEl: document.querySelector(".profile-edit-form .personal-grid"),
              setting,
              rules: setting.process_quantity_fields,
              valuesByRule: { rule1: [{ telefone: "111" }, { telefone: "222" }] },
              getSetting: () => setting,
              getCurrentSection: () => "dados"
            };
            window.AppGenesisProcessQuantityRuntimeV1.initialize(window.__quantityContextV1);
            """
        )

        hidden_value = driver.execute_script(
            """
            const hidden = document.querySelector("input[name='process_quantity_payload__rule1']");
            return hidden ? hidden.value : null;
            """
        )
        generated_items = driver.execute_script(
            """
            return document.querySelectorAll("[data-process-quantity-generated='1'][data-process-quantity-rule-key='rule1'] .profile-quantity-item-v1").length;
            """
        )
        generated_controls = driver.execute_script(
            """
            return document.querySelectorAll("[data-process-quantity-field-key='telefone']").length;
            """
        )

        assert hidden_value == '[{"telefone":"111"},{"telefone":"222"}]'
        assert generated_items == 2
        assert generated_controls == 2

        driver.execute_script(
            """
            const control = document.querySelector("[data-process-quantity-field-key='telefone']");
            control.value = "333";
            control.dispatchEvent(new Event("input", { bubbles: true }));
            """
        )

        updated_value = driver.execute_script(
            """
            const hidden = document.querySelector("input[name='process_quantity_payload__rule1']");
            return hidden ? hidden.value : null;
            """
        )

        assert updated_value == '[{"telefone":"333"},{"telefone":"222"}]'
    finally:
        driver.quit()


####################################################################################
# (2) SUBSEQUENTS: O RUNTIME CANONICO DEVE ESCONDER E RESTAURAR CAMPOS
####################################################################################


def test_process_subsequent_visibility_runtime_hides_and_restores_profile_targets_v1() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <section id="perfil-pessoal-card">
                  <form class="profile-edit-form" method="post" action="/users/profile/personal">
                    <div class="field" data-profile-field-key="estado">
                      <label for="estado">Estado</label>
                      <input id="estado" name="estado" value="inativo">
                    </div>
                    <div class="field" data-profile-field-key="motivo">
                      <label for="motivo">Motivo</label>
                      <input id="motivo" name="motivo" value="Texto">
                    </div>
                  </form>
                </section>
              </body>
            </html>
            """,
        )
        _inject_js_file_v1(driver, "static/js/modules/profile_field_registry_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_subsequent_visibility_runtime_v1.js")

        driver.execute_script(
            """
            const setting = {
              process_subsequent_fields: [
                {
                  key: "subseq1",
                  trigger_field: "estado",
                  target_field: "motivo",
                  operator: "equals",
                  trigger_value: "ativo"
                }
              ],
              process_field_options: [
                { key: "estado", label: "Estado", field_type: "text" },
                { key: "motivo", label: "Motivo", field_type: "text" }
              ]
            };
            window.__subsequentContextV1 = {
              mode: "profile",
              root: document,
              formEl: document.querySelector(".profile-edit-form"),
              setting,
              rules: setting.process_subsequent_fields,
              valuesByField: { estado: "inativo" },
              getSetting: () => setting,
              getCurrentSection: () => "dados"
            };
            window.AppGenesisProcessSubsequentVisibilityRuntimeV1.initialize(window.__subsequentContextV1);
            window.AppGenesisProcessSubsequentVisibilityRuntimeV1.apply(window.__subsequentContextV1);
            """
        )

        hidden_before = driver.execute_script(
            """
            const wrapper = document.querySelector("[data-profile-field-key='motivo']");
            return wrapper ? wrapper.hidden === true : false;
            """
        )
        disabled_before = driver.execute_script(
            """
            const control = document.querySelector("[data-profile-field-key='motivo'] input");
            return control ? control.disabled === true : false;
            """
        )

        assert hidden_before is True
        assert disabled_before is True

        driver.execute_script(
            """
            window.__subsequentContextV1.valuesByField = { estado: "ativo" };
            window.AppGenesisProcessSubsequentVisibilityRuntimeV1.refresh(window.__subsequentContextV1);
            """
        )

        hidden_after = driver.execute_script(
            """
            const wrapper = document.querySelector("[data-profile-field-key='motivo']");
            return wrapper ? wrapper.hidden === true : false;
            """
        )
        disabled_after = driver.execute_script(
            """
            const control = document.querySelector("[data-profile-field-key='motivo'] input");
            return control ? control.disabled === true : false;
            """
        )

        assert hidden_after is False
        assert disabled_after is False
    finally:
        driver.quit()


####################################################################################
# (3) POST-SAVE: O CAPTURE CANONICO DEVE GRAVAR CONTEXTO E INPUT HIDDEN
####################################################################################


def test_post_save_context_capture_binds_forms_and_persists_context_v1() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <form id="save-form" method="post" action="/users/new">
                  <button type="submit">Guardar</button>
                </form>
              </body>
            </html>
            """,
        )
        _install_fake_session_storage_v1(driver)
        _inject_js_file_v1(driver, "static/js/modules/post_save_context_contract_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/post_save_context_capture_v1.js")

        driver.execute_script(
            """
            window.AppGenesisPostSaveContextCaptureV1.initialize({ root: document });
            const form = document.getElementById("save-form");
            form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
            """
        )

        stored = driver.execute_script(
            """
            const contract = window.AppGenesisPostSaveContextContractV1;
            const raw = window.sessionStorage.getItem(contract.storageKey);
            const hidden = document.querySelector("input[name='appgenesis_after_save']");
            return {
              stored: raw ? JSON.parse(raw) : null,
              hiddenValue: hidden ? hidden.value : null
            };
            """
        )

        assert stored["stored"] is not None
        assert stored["stored"]["url"]
        assert "blank" in stored["stored"]["url"] or stored["stored"]["url"].startswith("data:")
        assert stored["hiddenValue"] == "1"
    finally:
        driver.quit()
