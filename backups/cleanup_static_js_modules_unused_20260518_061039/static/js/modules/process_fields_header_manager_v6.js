(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizeText_v6(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function isHeaderOption_v6(option) {
    if (!option || !String(option.value || "").trim()) {
      return false;
    }

    const dataType = normalizeText_v6(
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v6(option.textContent);
    const optionValue = normalizeText_v6(option.value);

    return (
      dataType === "header" ||
      optionText.includes("cabecalho") ||
      optionText.includes("cabeçalho") ||
      optionValue.includes("cabecalho") ||
      optionValue.includes("cabeçalho")
    );
  }

  function createOption_v6(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO E CAMPOS
  //###################################################################################

  function isProcessFieldsForm_v6(form) {
    const action = String(form.getAttribute("action") || "");
    const text = normalizeText_v6(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos")
    );
  }

  function findProcessFieldsForms_v6() {
    return Array.from(document.querySelectorAll("form")).filter(isProcessFieldsForm_v6);
  }

  function findSelectByLabel_v6(form, labelTexts) {
    const labels = Array.from(form.querySelectorAll("label"));

    for (const label of labels) {
      const labelText = normalizeText_v6(label.textContent);

      if (!labelTexts.some((text) => labelText.includes(text))) {
        continue;
      }

      const forId = String(label.getAttribute("for") || "").trim();

      if (forId) {
        const byId = form.querySelector("#" + CSS.escape(forId));

        if (byId && byId.tagName && byId.tagName.toLowerCase() === "select") {
          return byId;
        }
      }

      const inside = label.parentElement?.querySelector("select");

      if (inside) {
        return inside;
      }
    }

    return null;
  }

  function findNameSelect_v6(form) {
    const byLabel = findSelectByLabel_v6(form, [
      "nome do campo",
      "campo do processo"
    ]);

    if (byLabel) {
      return byLabel;
    }

    return Array.from(form.querySelectorAll("select")).find((select) => {
      const name = normalizeText_v6(select.name);
      const id = normalizeText_v6(select.id);

      if (select.dataset.processFieldHeaderSelectV6 === "1") {
        return false;
      }

      if (name.includes("header") || id.includes("header")) {
        return false;
      }

      return select.options.length > 0;
    }) || null;
  }

  //###################################################################################
  // (3) LER BOOTSTRAP DO MENU
  //###################################################################################

  function getBootstrap_v6() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getCurrentMenuKey_v6(form) {
    const menuInput = form.querySelector('input[name="menu_key"]');
    const fromInput = String(menuInput?.value || "").trim().toLowerCase();

    if (fromInput) {
      return fromInput;
    }

    const bootstrap = getBootstrap_v6();

    return String(
      bootstrap.settingsEditKey ||
      bootstrap.settings_edit_key ||
      new URLSearchParams(window.location.search).get("settings_edit_key") ||
      ""
    ).trim().toLowerCase();
  }

  function getCurrentMenuSetting_v6(form) {
    const menuKey = getCurrentMenuKey_v6(form);
    const bootstrap = getBootstrap_v6();
    const settings = Array.isArray(bootstrap.sidebarMenuSettings)
      ? bootstrap.sidebarMenuSettings
      : [];

    return settings.find((setting) => {
      return String(setting?.key || "").trim().toLowerCase() === menuKey;
    }) || null;
  }

  function collectOptionsFromBootstrap_v6(form) {
    const setting = getCurrentMenuSetting_v6(form);
    const options = Array.isArray(setting?.process_field_options)
      ? setting.process_field_options
      : [];

    return options
      .map((item) => {
        const key = String(item?.key || "").trim().toLowerCase();
        const label = String(item?.label || item?.key || "").trim();
        const type = normalizeText_v6(item?.field_type || item?.fieldType || item?.type || "");

        if (!key || !label) {
          return null;
        }

        return {
          key,
          label,
          isHeader: type === "header"
        };
      })
      .filter(Boolean);
  }

  function collectOptionsFromSelect_v6(nameSelect) {
    return Array.from(nameSelect.options)
      .map((option) => {
        const key = String(option.value || "").trim().toLowerCase();
        let label = String(option.textContent || "").trim();

        if (!key || !label) {
          return null;
        }

        const isHeader = isHeaderOption_v6(option);

        label = label.replace(/\s*-\s*Cabeçalho\s*$/i, "");
        label = label.replace(/\s*-\s*Cabecalho\s*$/i, "");

        return {
          key,
          label,
          isHeader
        };
      })
      .filter(Boolean);
  }

  function collectConfiguredKeys_v6(form) {
    const configured = new Set();

    Array.from(form.querySelectorAll('[name="visible_fields"]')).forEach((input) => {
      const key = String(input.value || "").trim().toLowerCase();

      if (key) {
        configured.add(key);
      }
    });

    const setting = getCurrentMenuSetting_v6(form);

    if (Array.isArray(setting?.process_visible_fields)) {
      setting.process_visible_fields.forEach((key) => {
        const cleanKey = String(key || "").trim().toLowerCase();

        if (cleanKey) {
          configured.add(cleanKey);
        }
      });
    }

    if (Array.isArray(setting?.process_visible_field_rows)) {
      setting.process_visible_field_rows.forEach((row) => {
        const cleanKey = String(row?.field_key || "").trim().toLowerCase();

        if (cleanKey) {
          configured.add(cleanKey);
        }
      });
    }

    return configured;
  }

  function mergeOptions_v6(optionsList) {
    const merged = [];
    const seen = new Set();

    optionsList.flat().forEach((item) => {
      const key = String(item?.key || "").trim().toLowerCase();
      const label = String(item?.label || "").trim();

      if (!key || !label || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push({
        key,
        label,
        isHeader: Boolean(item.isHeader)
      });
    });

    return merged;
  }

  //###################################################################################
  // (4) RECONSTRUIR NOME DO CAMPO E CABEÇALHO
  //###################################################################################

  function rebuildNameSelect_v6(form, nameSelect, allOptions) {
    const configuredKeys = collectConfiguredKeys_v6(form);
    const previousValue = String(nameSelect.value || "").trim().toLowerCase();

    nameSelect.innerHTML = "";
    nameSelect.name = "selected_visible_field";

    nameSelect.appendChild(createOption_v6("", "Selecione", ""));

    allOptions
      .filter((item) => !item.isHeader)
      .filter((item) => !configuredKeys.has(item.key))
      .forEach((item) => {
        nameSelect.appendChild(createOption_v6(item.key, item.label, previousValue));
      });
  }

  function buildHeaderSelect_v6(allOptions, selectedValue) {
    const select = document.createElement("select");
    select.name = "selected_visible_header";
    select.dataset.processFieldHeaderSelectV6 = "1";

    select.appendChild(createOption_v6("", "Sem cabeçalho", selectedValue));

    allOptions
      .filter((item) => item.isHeader)
      .forEach((item) => {
        select.appendChild(createOption_v6(item.key, item.label, selectedValue));
      });

    return select;
  }

  function getFieldWrapper_v6(select) {
    return (
      select.closest(".field") ||
      select.closest(".form-field") ||
      select.closest(".form-group") ||
      select.parentElement
    );
  }

  function removeOldManagers_v6(form) {
    form.querySelectorAll(
      ".process-fields-picker-row-v3, .process-fields-picker-row-v4, .process-fields-picker-row-v5, .process-fields-picker-row-v6"
    ).forEach((element) => {
      const originalField = element.querySelector(".field");

      if (originalField && element.parentElement) {
        element.parentElement.insertBefore(originalField, element);
      }

      element.remove();
    });

    form.querySelectorAll(
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, .process-field-header-picker-v4, .process-field-header-picker-v5, .process-field-header-picker-v6"
    ).forEach((element) => element.remove());
  }

  function ensureSideBySideLayout_v6(form, nameSelect, allOptions) {
    const existing = form.querySelector('[data-main-header-select-v6="1"]');

    if (existing) {
      return existing;
    }

    const nameWrapper = getFieldWrapper_v6(nameSelect);
    const row = document.createElement("div");
    row.className = "process-fields-picker-row-v6";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-field-header-picker-v6";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const headerSelect = buildHeaderSelect_v6(allOptions, "");
    headerSelect.dataset.mainHeaderSelectV6 = "1";

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(headerSelect);

    if (nameWrapper && nameWrapper.parentElement) {
      nameWrapper.parentElement.insertBefore(row, nameWrapper);
      row.appendChild(nameWrapper);
      row.appendChild(headerWrapper);
    }

    return headerSelect;
  }

  function renameLabels_v6(root) {
    Array.from(root.querySelectorAll("label, th, strong, span, div")).forEach((element) => {
      const text = normalizeText_v6(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  //###################################################################################
  // (5) VALIDAÇÃO ANTES DE GRAVAR
  //###################################################################################

  function showMessage_v6(form, message, isError) {
    let box = form.querySelector("[data-process-fields-message-v6='1']");

    if (!box) {
      box = document.createElement("div");
      box.dataset.processFieldsMessageV6 = "1";
      box.style.marginTop = "8px";
      box.style.fontSize = "12px";
      box.style.fontWeight = "700";
      form.appendChild(box);
    }

    box.textContent = message;
    box.style.color = isError ? "#b42318" : "#1f6f43";
  }

  function validateSubmit_v6(event, form, nameSelect) {
    const selectedField = String(nameSelect.value || "").trim();

    if (!selectedField) {
      event.preventDefault();
      showMessage_v6(form, "Selecione um nome do campo antes de guardar.", true);
      return false;
    }

    showMessage_v6(form, "A guardar configuração dos campos...", false);
    return true;
  }

  //###################################################################################
  // (6) ESTILO
  //###################################################################################

  function injectStyle_v6() {
    if (document.getElementById("process-fields-header-manager-v6-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v6-style";
    style.textContent = `
      .process-fields-picker-row-v6 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        gap: 12px !important;
        align-items: end !important;
        width: 100% !important;
        max-width: 100% !important;
      }

      .process-fields-picker-row-v6 > * {
        min-width: 0 !important;
        width: 100% !important;
      }

      .process-fields-picker-row-v6 .field,
      .process-field-header-picker-v6 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }

      .process-fields-picker-row-v6 label,
      .process-field-header-picker-v6 label {
        min-height: 14px !important;
        line-height: 14px !important;
        margin: 0 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
      }

      .process-fields-picker-row-v6 select,
      .process-field-header-picker-v6 select {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 38px !important;
        min-height: 38px !important;
        box-sizing: border-box !important;
      }

      @media (max-width: 900px) {
        .process-fields-picker-row-v6 {
          grid-template-columns: 1fr !important;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (7) INICIALIZAR
  //###################################################################################

  function initForm_v6(form) {
    if (form.dataset.processFieldsHeaderManagerV6 === "1") {
      return;
    }

    const root = form.closest(".card") || form.closest("section") || form;
    const nameSelect = findNameSelect_v6(form);

    if (!nameSelect) {
      return;
    }

    form.dataset.processFieldsHeaderManagerV6 = "1";

    renameLabels_v6(root);

    const allOptions = mergeOptions_v6([
      collectOptionsFromSelect_v6(nameSelect),
      collectOptionsFromBootstrap_v6(form)
    ]);

    removeOldManagers_v6(form);
    rebuildNameSelect_v6(form, nameSelect, allOptions);
    ensureSideBySideLayout_v6(form, nameSelect, allOptions);

    form.addEventListener(
      "submit",
      (event) => validateSubmit_v6(event, form, nameSelect),
      true
    );
  }

  function initProcessFieldsHeaderManager_v6() {
    injectStyle_v6();

    findProcessFieldsForms_v6().forEach((form) => {
      initForm_v6(form);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v6);
  } else {
    initProcessFieldsHeaderManager_v6();
  }

  window.setTimeout(initProcessFieldsHeaderManager_v6, 300);
  window.setTimeout(initProcessFieldsHeaderManager_v6, 900);
})();
