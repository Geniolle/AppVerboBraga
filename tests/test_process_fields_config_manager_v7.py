from pathlib import Path

from tests.test_new_user_runtime_functional_v1 import (
    _build_chrome_driver_v1,
    _inject_js_file_v1,
    _load_blank_page_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) TESTAR LEITURA DO HEADER LEGADO NO MANAGER V7
####################################################################################

def test_process_fields_config_manager_v7_reads_legacy_header_key() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert 'valorLinhaLegacy_v7(row, "[data-process-config-header-key]")' in script_text
    assert "headerKey: explicitHeaderKey || currentHeaderKey" in script_text


####################################################################################
# (2) TESTAR TEMPLATE LEGADO COM HEADER KEY EXPLICITO
####################################################################################

def test_new_user_template_exposes_legacy_process_field_header_key() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert "data-process-config-header-key" in template_text


####################################################################################
# (3) REGRESSAO FUNCIONAL: a tabela da configuracao dos campos deve renderizar
# mesmo sem data-process-fields-config-total-label no template atual.
####################################################################################


def test_process_fields_config_manager_v7_renders_rows_without_total_label() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <section id="settings-menu-edit-card">
                  <form data-process-additional-fields-manager-v3="1">
                    <div data-additional-fields-legacy-container>
                      <div>
                        <input type="hidden" name="additional_field_key" value="custom_nome" disabled>
                        <input type="hidden" name="additional_field_label" value="Nome" disabled>
                        <input type="hidden" name="additional_field_type" value="text" disabled>
                      </div>
                      <div>
                        <input type="hidden" name="additional_field_key" value="custom_estado" disabled>
                        <input type="hidden" name="additional_field_label" value="Estado" disabled>
                        <input type="hidden" name="additional_field_type" value="text" disabled>
                      </div>
                    </div>
                    <div data-additional-fields-hidden-container></div>
                  </form>

                  <form data-process-fields-config-manager-v1="1">
                    <div data-process-fields-config-legacy-container>
                      <div data-process-config-field-row>
                        <input type="hidden" data-process-config-key value="custom_nome" disabled>
                        <input type="hidden" data-process-config-label value="Nome" disabled>
                        <input type="hidden" data-process-config-kind value="field" disabled>
                        <input type="hidden" data-process-config-header-key value="" disabled>
                      </div>
                      <div data-process-config-field-row>
                        <input type="hidden" data-process-config-key value="custom_estado" disabled>
                        <input type="hidden" data-process-config-label value="Estado" disabled>
                        <input type="hidden" data-process-config-kind value="field" disabled>
                        <input type="hidden" data-process-config-header-key value="" disabled>
                      </div>
                    </div>
                    <div data-process-fields-config-hidden-container></div>
                    <div data-process-fields-config-editor-block>
                      <select data-process-fields-config-editor-key>
                        <option value="">Selecione</option>
                        <option value="custom_nome" data-process-config-kind="field" data-process-config-label="Nome">Nome</option>
                        <option value="custom_estado" data-process-config-kind="field" data-process-config-label="Estado">Estado</option>
                      </select>
                      <select data-process-fields-config-header-editor-key>
                        <option value="">Sem cabeçalho</option>
                      </select>
                      <button type="button" data-process-fields-config-submit>Guardar</button>
                      <button type="button" data-process-fields-config-cancel>Cancelar</button>
                    </div>
                    <table data-process-fields-config-table>
                      <thead></thead>
                      <tbody data-process-fields-config-table-body></tbody>
                    </table>
                    <p data-process-fields-config-empty style="display: none;">Sem campos configurados.</p>
                    <select data-process-fields-config-page-size>
                      <option value="5" selected>5</option>
                    </select>
                    <div data-process-fields-config-pagination></div>
                  </form>
                </section>
              </body>
            </html>
            """,
        )
        _inject_js_file_v1(driver, "static/js/modules/configurable_items_manager_core_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_field_options_resolver_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_fields_config_manager_v7.js")

        driver.execute_script(
            """
            if (window.setupProcessFieldsConfigManagerV7) {
              window.setupProcessFieldsConfigManagerV7();
            }
            """
        )

        row_count = driver.execute_script(
            """
            const tbody = document.querySelector('[data-process-fields-config-table-body]');
            return tbody ? tbody.querySelectorAll('tr').length : -1;
            """
        )

        assert row_count == 2
    finally:
        driver.quit()


####################################################################################
# (4) REGRESSAO FUNCIONAL: os campos adicionais devem ser resolvidos via bootstrap
# mesmo antes do manager de campos adicionais sincronizar o DOM.
####################################################################################


def test_process_fields_config_manager_v7_uses_bootstrap_additional_fields_without_dom_manager() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <section id="settings-menu-edit-card">
                  <form data-process-fields-config-manager-v1="1">
                    <input type="hidden" name="menu_key" value="extrato">
                    <div data-process-fields-config-legacy-container></div>
                    <div data-process-fields-config-hidden-container></div>
                    <div data-process-fields-config-editor-block>
                      <select data-process-fields-config-editor-key>
                        <option value="">Selecione</option>
                        <option value="entidade" data-process-config-kind="field" data-process-config-label="Entidade">Entidade</option>
                        <option value="custom_campo_extra" data-process-config-kind="field" data-process-config-label="Campo extra">Campo extra</option>
                      </select>
                      <select data-process-fields-config-header-editor-key>
                        <option value="">Sem cabeçalho</option>
                      </select>
                      <button type="button" data-process-fields-config-submit>Guardar</button>
                      <button type="button" data-process-fields-config-cancel>Cancelar</button>
                    </div>
                    <table data-process-fields-config-table>
                      <thead></thead>
                      <tbody data-process-fields-config-table-body></tbody>
                    </table>
                    <p data-process-fields-config-empty style="display: none;">Sem campos configurados.</p>
                    <select data-process-fields-config-page-size>
                      <option value="5" selected>5</option>
                    </select>
                    <div data-process-fields-config-pagination></div>
                  </form>
                </section>
              </body>
            </html>
            """,
        )
        driver.execute_script(
            """
            window.__APPGENESIS_BOOTSTRAP__ = {
              sidebarMenuSettings: [
                {
                  key: "extrato",
                  process_additional_fields: [
                    { key: "custom_extratos_bancarios", label: "Extratos bancarios", field_type: "header" },
                    { key: "custom_campo_extra", label: "Campo extra", field_type: "text" }
                  ]
                }
              ]
            };
            """
        )
        _inject_js_file_v1(driver, "static/js/modules/configurable_items_manager_core_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_field_options_resolver_v1.js")
        _inject_js_file_v1(driver, "static/js/modules/process_fields_config_manager_v7.js")

        driver.execute_script(
            """
            if (window.setupProcessFieldsConfigManagerV7) {
              window.setupProcessFieldsConfigManagerV7();
            }
            """
        )

        options = driver.execute_script(
            """
            const select = document.querySelector('[data-process-fields-config-editor-key]');
            return select ? Array.from(select.options).map((option) => option.value) : [];
            """
        )
        row_count = driver.execute_script(
            """
            const tbody = document.querySelector('[data-process-fields-config-table-body]');
            return tbody ? tbody.querySelectorAll('tr').length : -1;
            """
        )

        assert "custom_campo_extra" in options
        assert row_count == 0
    finally:
        driver.quit()
