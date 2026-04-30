from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_V5_PATH = ROOT / "static" / "js" / "modules" / "process_fields_header_manager_v5.js"


def fail(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS
####################################################################################

if not TEMPLATE_PATH.exists():
    fail(f"ficheiro nao encontrado: {TEMPLATE_PATH}")


####################################################################################
# (2) LER TEMPLATE
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")


####################################################################################
# (3) AJUSTAR TEXTO DO CAMPO
####################################################################################

template = template.replace("CAMPO DO PROCESSO", "NOME DO CAMPO")
template = template.replace("Campo do processo", "Nome do campo")
template = template.replace("campo do processo", "nome do campo")


####################################################################################
# (4) CRIAR JS V5
####################################################################################

js_content = r'''(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizeText_v5(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v5(value) {
    return normalizeText_v5(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function isHeaderOption_v5(option) {
    if (!option || !String(option.value || "").trim()) {
      return false;
    }

    const dataType = normalizeText_v5(
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v5(option.textContent);
    const optionValue = normalizeText_v5(option.value);

    return (
      dataType === "header" ||
      optionText.includes("cabecalho") ||
      optionText.includes("cabeçalho") ||
      optionValue.includes("cabecalho") ||
      optionValue.includes("cabeçalho")
    );
  }

  function createOption_v5(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULARIO E SELECT NOME DO CAMPO
  //###################################################################################

  function isProcessFieldsForm_v5(form) {
    const action = String(form.getAttribute("action") || "");
    const text = normalizeText_v5(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos")
    );
  }

  function findProcessFieldsForms_v5() {
    return Array.from(document.querySelectorAll("form")).filter(isProcessFieldsForm_v5);
  }

  function findSelectByLabel_v5(form, labels) {
    const labelElements = Array.from(form.querySelectorAll("label"));

    for (const label of labelElements) {
      const text = normalizeText_v5(label.textContent);

      if (!labels.some((labelText) => text.includes(labelText))) {
        continue;
      }

      const forId = String(label.getAttribute("for") || "").trim();

      if (forId) {
        const byId = form.querySelector("#" + CSS.escape(forId));

        if (byId && byId.tagName && byId.tagName.toLowerCase() === "select") {
          return byId;
        }
      }

      const nearby = label.parentElement?.querySelector("select");

      if (nearby) {
        return nearby;
      }
    }

    return null;
  }

  function findNameFieldSelect_v5(form) {
    const byLabel = findSelectByLabel_v5(form, [
      "nome do campo",
      "campo do processo"
    ]);

    if (byLabel) {
      return byLabel;
    }

    return Array.from(form.querySelectorAll("select")).find((select) => {
      const name = normalizeText_v5(select.name);
      const id = normalizeText_v5(select.id);

      if (select.dataset.processFieldHeaderSelectV5 === "1") {
        return false;
      }

      if (name.includes("header") || id.includes("header")) {
        return false;
      }

      return select.options.length > 0;
    }) || null;
  }

  //###################################################################################
  // (3) LER BOOTSTRAP E OPCOES DO MENU
  //###################################################################################

  function getBootstrap_v5() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getCurrentMenuKey_v5(form) {
    const menuInput = form.querySelector('input[name="menu_key"]');
    const fromInput = String(menuInput?.value || "").trim().toLowerCase();

    if (fromInput) {
      return fromInput;
    }

    const bootstrap = getBootstrap_v5();
    return String(bootstrap.settingsEditKey || "").trim().toLowerCase();
  }

  function getCurrentMenuSetting_v5(form) {
    const menuKey = getCurrentMenuKey_v5(form);
    const bootstrap = getBootstrap_v5();
    const settings = Array.isArray(bootstrap.sidebarMenuSettings)
      ? bootstrap.sidebarMenuSettings
      : [];

    return settings.find((setting) => {
      return String(setting?.key || "").trim().toLowerCase() === menuKey;
    }) || null;
  }

  function getConfiguredFieldKeysFromBootstrap_v5(form) {
    const setting = getCurrentMenuSetting_v5(form);
    const keys = new Set();

    if (Array.isArray(setting?.process_visible_fields)) {
      setting.process_visible_fields.forEach((fieldKey) => {
        const cleanKey = String(fieldKey || "").trim().toLowerCase();

        if (cleanKey) {
          keys.add(cleanKey);
        }
      });
    }

    if (Array.isArray(setting?.process_visible_field_rows)) {
      setting.process_visible_field_rows.forEach((row) => {
        const cleanKey = String(row?.field_key || "").trim().toLowerCase();

        if (cleanKey) {
          keys.add(cleanKey);
        }
      });
    }

    return keys;
  }

  function getHeaderOptionsFromBootstrap_v5(form) {
    const setting = getCurrentMenuSetting_v5(form);
    const fieldOptions = Array.isArray(setting?.process_field_options)
      ? setting.process_field_options
      : [];

    return fieldOptions
      .filter((item) => normalizeText_v5(item?.field_type || item?.fieldType) === "header")
      .map((item) => {
        return {
          key: String(item?.key || "").trim().toLowerCase(),
          label: String(item?.label || item?.key || "").trim()
        };
      })
      .filter((item) => item.key && item.label);
  }

  //###################################################################################
  // (4) FILTRAR LISTAS
  //###################################################################################

  function getHeaderOptionsFromNameSelect_v5(nameSelect) {
    const headers = [];
    const seen = new Set();

    Array.from(nameSelect.options).forEach((option) => {
      if (!isHeaderOption_v5(option)) {
        return;
      }

      const key = String(option.value || "").trim().toLowerCase();
      let label = String(option.textContent || "").trim();

      label = label.replace(/\s*-\s*Cabeçalho\s*$/i, "");
      label = label.replace(/\s*-\s*Cabecalho\s*$/i, "");

      if (!key || !label || seen.has(key)) {
        return;
      }

      seen.add(key);
      headers.push({ key, label });
    });

    return headers;
  }

  function getHeaderOptions_v5(form, nameSelect) {
    const merged = [];
    const seen = new Set();

    getHeaderOptionsFromBootstrap_v5(form)
      .concat(getHeaderOptionsFromNameSelect_v5(nameSelect))
      .forEach((item) => {
        const key = String(item.key || "").trim().toLowerCase();
        const label = String(item.label || "").trim();

        if (!key || !label || seen.has(key)) {
          return;
        }

        seen.add(key);
        merged.push({ key, label });
      });

    return merged;
  }

  function filterNameFieldOptions_v5(form, nameSelect) {
    const configuredKeys = getConfiguredFieldKeysFromBootstrap_v5(form);

    Array.from(nameSelect.options).forEach((option) => {
      const value = String(option.value || "").trim().toLowerCase();

      if (!value) {
        return;
      }

      if (isHeaderOption_v5(option) || configuredKeys.has(value)) {
        option.remove();
      }
    });

    if (isHeaderOption_v5(nameSelect.selectedOptions[0])) {
      nameSelect.value = "";
    }
  }

  //###################################################################################
  // (5) LAYOUT ALINHADO
  //###################################################################################

  function getFieldWrapper_v5(select) {
    return (
      select.closest(".field") ||
      select.closest(".form-field") ||
      select.closest(".form-group") ||
      select.parentElement
    );
  }

  function buildHeaderSelect_v5(headerOptions, selectedValue) {
    const select = document.createElement("select");
    select.dataset.processFieldHeaderSelectV5 = "1";

    select.appendChild(createOption_v5("", "Sem cabeçalho", selectedValue));

    headerOptions.forEach((header) => {
      select.appendChild(createOption_v5(header.key, header.label, selectedValue));
    });

    return select;
  }

  function removeOldManagers_v5(form) {
    form.querySelectorAll(
      ".process-fields-picker-row-v3, .process-fields-picker-row-v4, .process-fields-picker-row-v5, " +
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, .process-field-header-picker-v4, .process-field-header-picker-v5"
    ).forEach((element) => {
      element.remove();
    });
  }

  function ensureSideBySideLayout_v5(form, nameSelect, headerOptions) {
    if (form.querySelector('[data-main-header-select-v5="1"]')) {
      return form.querySelector('[data-main-header-select-v5="1"]');
    }

    const nameWrapper = getFieldWrapper_v5(nameSelect);
    const row = document.createElement("div");
    row.className = "process-fields-picker-row-v5";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-field-header-picker-v5";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const headerSelect = buildHeaderSelect_v5(headerOptions, "");
    headerSelect.dataset.mainHeaderSelectV5 = "1";

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(headerSelect);

    if (nameWrapper && nameWrapper.parentElement) {
      nameWrapper.parentElement.insertBefore(row, nameWrapper);
      row.appendChild(nameWrapper);
      row.appendChild(headerWrapper);
    }

    return headerSelect;
  }

  function renameLabels_v5(root) {
    Array.from(root.querySelectorAll("label, th, strong, span, div")).forEach((element) => {
      const text = normalizeText_v5(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  //###################################################################################
  // (6) PAYLOAD PARA GRAVAR
  //###################################################################################

  function getExistingConfiguredRows_v5(form, nameSelect) {
    const controls = Array.from(form.querySelectorAll('[name="visible_fields"]')).filter((control) => {
      return control !== nameSelect && !control.dataset.generatedProcessFieldV5;
    });

    return controls
      .map((control, index) => {
        const fieldKey = String(control.value || "").trim().toLowerCase();

        if (!fieldKey) {
          return null;
        }

        const row = (
          control.closest("tr") ||
          control.closest(".configured-field-row") ||
          control.closest(".settings-row") ||
          control.closest(".field-row") ||
          control.parentElement
        );

        const rowHeader = row?.querySelector('[name="visible_headers"]');
        const allHeaders = Array.from(form.querySelectorAll('[name="visible_headers"]'));

        return {
          fieldKey,
          headerKey: String(rowHeader?.value || allHeaders[index]?.value || "").trim().toLowerCase()
        };
      })
      .filter(Boolean);
  }

  function getSelectedRow_v5(nameSelect, headerSelect) {
    const fieldKey = String(nameSelect.value || "").trim().toLowerCase();

    if (!fieldKey) {
      return null;
    }

    if (isHeaderOption_v5(nameSelect.selectedOptions[0])) {
      return null;
    }

    return {
      fieldKey,
      headerKey: String(headerSelect?.value || "").trim().toLowerCase()
    };
  }

  function buildPayloadRows_v5(form, nameSelect, headerSelect) {
    const rows = getExistingConfiguredRows_v5(form, nameSelect);
    const selectedRow = getSelectedRow_v5(nameSelect, headerSelect);

    if (selectedRow && !rows.some((row) => row.fieldKey === selectedRow.fieldKey)) {
      rows.push(selectedRow);
    }

    return rows;
  }

  function buildPostFormData_v5(form, nameSelect, headerSelect) {
    const formData = new FormData(form);
    const rows = buildPayloadRows_v5(form, nameSelect, headerSelect);

    formData.delete("visible_fields");
    formData.delete("visible_headers");
    formData.delete("process_field_header_picker");

    rows.forEach((row) => {
      formData.append("visible_fields", row.fieldKey);
      formData.append("visible_headers", row.headerKey);
    });

    return {
      formData,
      rows
    };
  }

  function showLocalMessage_v5(form, message, isError) {
    let messageBox = form.querySelector("[data-process-fields-message-v5='1']");

    if (!messageBox) {
      messageBox = document.createElement("div");
      messageBox.dataset.processFieldsMessageV5 = "1";
      messageBox.style.marginTop = "8px";
      messageBox.style.fontSize = "12px";
      messageBox.style.fontWeight = "700";
      form.appendChild(messageBox);
    }

    messageBox.textContent = message;
    messageBox.style.color = isError ? "#b42318" : "#1f6f43";
  }

  function submitProcessFields_v5(event, form, nameSelect, headerSelect) {
    event.preventDefault();

    const result = buildPostFormData_v5(form, nameSelect, headerSelect);

    if (!result.rows.length) {
      showLocalMessage_v5(form, "Selecione pelo menos um nome do campo antes de guardar.", true);
      return;
    }

    showLocalMessage_v5(form, "A guardar configuração dos campos...", false);

    fetch(form.action, {
      method: String(form.method || "POST").toUpperCase(),
      body: result.formData,
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "fetch"
      }
    })
      .then((response) => {
        if (!response.ok && !response.redirected) {
          throw new Error("Falha HTTP " + response.status);
        }

        window.location.assign(response.url || window.location.href);
      })
      .catch((error) => {
        console.error("Erro ao guardar configuração dos campos:", error);
        showLocalMessage_v5(form, "Erro ao guardar. Veja os logs e tente novamente.", true);
      });
  }

  //###################################################################################
  // (7) ESTILO
  //###################################################################################

  function injectStyle_v5() {
    if (document.getElementById("process-fields-header-manager-v5-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v5-style";
    style.textContent = `
      .process-fields-picker-row-v5 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        gap: 12px !important;
        align-items: end !important;
        width: 100% !important;
        max-width: 100% !important;
      }

      .process-fields-picker-row-v5 > * {
        min-width: 0 !important;
        width: 100% !important;
      }

      .process-fields-picker-row-v5 .field,
      .process-field-header-picker-v5 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }

      .process-fields-picker-row-v5 label,
      .process-field-header-picker-v5 label {
        min-height: 14px !important;
        line-height: 14px !important;
        margin: 0 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
      }

      .process-fields-picker-row-v5 select,
      .process-field-header-picker-v5 select {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 38px !important;
        min-height: 38px !important;
        box-sizing: border-box !important;
      }

      @media (max-width: 900px) {
        .process-fields-picker-row-v5 {
          grid-template-columns: 1fr !important;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (8) INICIALIZAR
  //###################################################################################

  function initForm_v5(form) {
    if (form.dataset.processFieldsHeaderManagerV5 === "1") {
      return;
    }

    const root = form.closest(".card") || form.closest("section") || form;

    renameLabels_v5(root);

    const nameSelect = findNameFieldSelect_v5(form);

    if (!nameSelect) {
      return;
    }

    form.dataset.processFieldsHeaderManagerV5 = "1";

    const headerOptions = getHeaderOptions_v5(form, nameSelect);

    filterNameFieldOptions_v5(form, nameSelect);
    removeOldManagers_v5(form);

    const headerSelect = ensureSideBySideLayout_v5(form, nameSelect, headerOptions);

    form.addEventListener("submit", (event) => {
      submitProcessFields_v5(event, form, nameSelect, headerSelect);
    }, true);
  }

  function initProcessFieldsHeaderManager_v5() {
    injectStyle_v5();

    findProcessFieldsForms_v5().forEach((form) => {
      initForm_v5(form);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v5);
  } else {
    initProcessFieldsHeaderManager_v5();
  }

  window.setTimeout(initProcessFieldsHeaderManager_v5, 300);
  window.setTimeout(initProcessFieldsHeaderManager_v5, 900);
})();
'''

JS_V5_PATH.write_text(js_content, encoding="utf-8")


####################################################################################
# (5) ATUALIZAR TEMPLATE PARA USAR SOMENTE V5
####################################################################################

for version in ["v1", "v2", "v3", "v4"]:
    template = re.sub(
        rf'\s*<script src="/static/js/modules/process_fields_header_manager_{version}\.js\?v=[^"]+"></script>',
        "",
        template,
    )

script_tag = '<script src="/static/js/modules/process_fields_header_manager_v5.js?v=20260430-fields-header-v5"></script>'

if "process_fields_header_manager_v5.js" not in template:
    scripts_block_pattern = re.compile(
        r"(?P<start>\{% block scripts %\}[\s\S]*?)(?P<end>\n\{% endblock %\})",
        re.S,
    )

    match = scripts_block_pattern.search(template)

    if match:
        template = (
            template[:match.end("start")]
            + "\n  "
            + script_tag
            + template[match.end("start"):]
        )
    else:
        template = template.rstrip() + "\n\n{% block scripts %}\n  " + script_tag + "\n{% endblock %}\n"
else:
    template = re.sub(
        r'/static/js/modules/process_fields_header_manager_v5\.js\?v=[^"]+',
        '/static/js/modules/process_fields_header_manager_v5.js?v=20260430-fields-header-v5',
        template,
    )

TEMPLATE_PATH.write_text(template, encoding="utf-8")

print("OK: process_fields_header_manager_v5.js criado.")
print("OK: new_user.html atualizado para carregar somente V5.")
print("OK: patch_process_fields_header_manager_v5 concluído.")
