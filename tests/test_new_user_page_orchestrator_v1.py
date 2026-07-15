from pathlib import Path

from test_new_user_runtime_functional_v1 import (
    _build_chrome_driver_v1,
    _inject_js_file_v1,
    _load_blank_page_v1,
)


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


####################################################################################
# (2) O ORQUESTRADOR TEM DE INICIALIZAR OS RUNTIMES REAIS UMA VEZ
####################################################################################


def test_new_user_runtime_initializes_canonical_runtimes_in_order_v1() -> None:
    driver = _build_chrome_driver_v1()
    try:
        _load_blank_page_v1(
            driver,
            """
            <html>
              <body>
                <main data-appgenesis-new-user-page="1">
                  <div data-process-menu-root="1"></div>
                  <section id="perfil-pessoal-card">
                    <div class="profile-readonly">
                      <div class="personal-grid"></div>
                    </div>
                    <form class="profile-edit-form" method="post" action="/users/profile/personal">
                      <div class="personal-grid">
                        <div class="field">
                          <label for="profile-quantity">Quantidade</label>
                          <input id="profile-quantity" name="quantidade" type="number" value="1">
                        </div>
                      </div>
                    </form>
                  </section>
                  <section data-dynamic-process-card="1">
                    <form id="dynamic-process-edit-form" data-process-edit-form="1" method="post" action="/process/new">
                      <input id="dynamic-process-menu-key" value="dynamic_process">
                      <input id="dynamic-process-section-key" value="dados">
                      <div id="dynamic-process-readonly-grid"></div>
                      <div id="dynamic-process-edit-grid"></div>
                    </form>
                  </section>
                  <div id="process-additional-fields-builder-v3" data-process-additional-fields-manager-v3="1"></div>
                </main>
              </body>
            </html>
            """,
        )
        driver.execute_script(
            """
            window.__calls = [];
            window.__readyCount = 0;
            document.addEventListener("appgenesis:new-user-page-ready", () => {
              window.__readyCount += 1;
            });

            const storageFactory = () => {
              const store = new Map();
              return {
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
              };
            };

            Object.defineProperty(window, "localStorage", {
              configurable: true,
              value: storageFactory()
            });
            Object.defineProperty(window, "sessionStorage", {
              configurable: true,
              value: storageFactory()
            });

            window.appGenesisProcessKeysRegistryV1 = { MEU_PERFIL_MENU_KEY: "meu_perfil" };
            window.appGenesisProcessReferenceRegistryV1 = {
              HOME_MENU_KEY_V1: "home",
              PERFIL_MENU_KEY_V1: "perfil"
            };

            window.AppGenesisProcessMenuRuntimeV1 = {
              bindMenuButtonListeners() { window.__calls.push("menu.bindButtons"); },
              bindHashChangeListener() { window.__calls.push("menu.bindHash"); }
            };
            window.AppGenesisProcessQuantityRuntimeV1 = {
              createMeuPerfilQuantityAdapterV1() {
                window.__calls.push("quantity.profile.adapter");
                return { adapter: "profile" };
              },
              createDynamicProcessQuantityAdapterV1() {
                window.__calls.push("quantity.dynamic.adapter");
                return { adapter: "dynamic" };
              },
              initialize(context) {
                window.__calls.push("quantity.initialize:" + context.mode);
                return context;
              }
            };
            window.AppGenesisProcessSubsequentVisibilityRuntimeV1 = {
              initialize(context) {
                window.__calls.push("subseq.initialize:" + context.mode);
                return context;
              }
            };
            window.AppGenesisPostSaveContextCaptureV1 = {
              initialize(context) {
                window.__calls.push("postsave.initialize");
                return context;
              }
            };

            window.syncTrainingOutrosState = () => window.__calls.push("nav.syncTraining");
            window.renderHomeCharts = () => window.__calls.push("nav.renderCharts");
            window.setupReadOnlyCards = () => window.__calls.push("nav.readOnlyCards");
            window.setupProfileProcessTabs = () => window.__calls.push("nav.profileTabs");
            window.setupProcessFieldsBuilder = () => window.__calls.push("admin.fieldsBuilder");
            window.setupProcessAdditionalFieldsManagerV3 = () => window.__calls.push("admin.additionalFieldsV3");
            window.setupTableLimiter = (prefix) => window.__calls.push("table:" + prefix);
            window.setupGeneratedInviteLinkCopy = () => window.__calls.push("invite.copy");
            window.setupCreateUserGenerateLinkShortcut = () => window.__calls.push("invite.shortcut");
            window.setupProcessEditTabs = () => window.__calls.push("processSettings.tabs");
                window.appgenesisAutoDismissFlashMessages_v1 = () => window.__calls.push("postsave.dismiss");
                window.logAppGenesisProcessEditorDebugV1 = () => {};
                window.debugTabsLogV1 = () => {};
                window.logAppGenesisNavigationBootDebugV1 = () => {};
                window.__APPGENESIS_BOOTSTRAP__ = {
                  sidebarMenuSettings: [
                    {
                      key: "meu_perfil",
                      process_quantity_fields: [
                        {
                          key: "rule_profile",
                          quantity_field_key: "quantidade",
                          repeated_field_keys: ["telefone"],
                          header_key: "dados",
                          max_items: 3,
                          item_label: "Contacto"
                        }
                      ],
                      process_subsequent_fields: [
                        {
                          key: "sub_profile",
                          trigger_field: "estado",
                          target_field: "motivo",
                          operator: "equals",
                          trigger_value: "ativo"
                        }
                      ],
                      process_field_options: [
                        { key: "quantidade", label: "Quantidade", field_type: "number" },
                        { key: "telefone", label: "Telefone", field_type: "text" },
                        { key: "estado", label: "Estado", field_type: "text" },
                        { key: "motivo", label: "Motivo", field_type: "text" }
                      ]
                    },
                    {
                      key: "dynamic_process",
                      process_quantity_fields: [
                        {
                          key: "rule_dynamic",
                          quantity_field_key: "dynamic_quantity",
                          repeated_field_keys: ["dynamic_phone"],
                          header_key: "dados",
                          max_items: 2,
                          item_label: "Registo"
                        }
                      ],
                      process_subsequent_fields: [
                        {
                          key: "sub_dynamic",
                          trigger_field: "dynamic_state",
                          target_field: "dynamic_reason",
                          operator: "equals",
                          trigger_value: "ativo"
                        }
                      ],
                      process_field_options: [
                        { key: "dynamic_quantity", label: "Quantidade", field_type: "number" },
                        { key: "dynamic_phone", label: "Telefone", field_type: "text" },
                        { key: "dynamic_state", label: "Estado", field_type: "text" },
                        { key: "dynamic_reason", label: "Motivo", field_type: "text" }
                      ]
                    }
                  ]
                };
                window.getCurrentProfileSectionSubsequentV1 = () => "dados";
                window.getSidebarMenuSetting = (key) => {
              if (key === "meu_perfil") {
                return {
                  key: "meu_perfil",
                  process_quantity_fields: [
                    {
                      key: "rule_profile",
                      quantity_field_key: "quantidade",
                      repeated_field_keys: ["telefone"],
                      header_key: "dados",
                      max_items: 3,
                      item_label: "Contacto"
                    }
                  ],
                  process_subsequent_fields: [
                    {
                      key: "sub_profile",
                      trigger_field: "estado",
                      target_field: "motivo",
                      operator: "equals",
                      trigger_value: "ativo"
                    }
                  ],
                  process_field_options: [
                    { key: "quantidade", label: "Quantidade", field_type: "number" },
                    { key: "telefone", label: "Telefone", field_type: "text" },
                    { key: "estado", label: "Estado", field_type: "text" },
                    { key: "motivo", label: "Motivo", field_type: "text" }
                  ]
                };
              }

              if (key === "dynamic_process") {
                return {
                  key: "dynamic_process",
                  process_quantity_fields: [
                    {
                      key: "rule_dynamic",
                      quantity_field_key: "dynamic_quantity",
                      repeated_field_keys: ["dynamic_phone"],
                      header_key: "dados",
                      max_items: 2,
                      item_label: "Registo"
                    }
                  ],
                  process_subsequent_fields: [
                    {
                      key: "sub_dynamic",
                      trigger_field: "dynamic_state",
                      target_field: "dynamic_reason",
                      operator: "equals",
                      trigger_value: "ativo"
                    }
                  ],
                  process_field_options: [
                    { key: "dynamic_quantity", label: "Quantidade", field_type: "number" },
                    { key: "dynamic_phone", label: "Telefone", field_type: "text" },
                    { key: "dynamic_state", label: "Estado", field_type: "text" },
                    { key: "dynamic_reason", label: "Motivo", field_type: "text" }
                  ]
                };
              }

              return null;
            };
            """
        )
        _inject_js_file_v1(driver, "static/js/modules/profile_field_registry_v1.js")
        _inject_js_file_v1(driver, "static/js/new_user.js")
        driver.execute_script("window.AppGenesisNewUserPageV1.initializeNewUserPageV1();")

        calls = driver.execute_script("return window.__calls.slice();")
        ready_count = driver.execute_script("return window.__readyCount;")

        assert ready_count == 1
        assert "quantity.profile.adapter" in calls
        assert "quantity.dynamic.adapter" in calls
        assert calls.index("menu.bindButtons") < calls.index("menu.bindHash") < calls.index("quantity.initialize:profile")
        assert calls.index("quantity.initialize:profile") < calls.index("subseq.initialize:profile")
        assert calls.index("subseq.initialize:profile") < calls.index("quantity.initialize:dynamic")
        assert calls.index("quantity.initialize:dynamic") < calls.index("subseq.initialize:dynamic")
        assert calls.index("subseq.initialize:dynamic") < calls.index("postsave.initialize")

        driver.execute_script("window.AppGenesisNewUserPageV1.initializeNewUserPageV1();")
        assert driver.execute_script("return window.__calls.length;") == len(calls)
    finally:
        driver.quit()
