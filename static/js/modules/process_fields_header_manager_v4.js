(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizeText_v4(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v4(value) {
    return normalizeText_v4(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function isHeaderOption_v4(option) {
    if (!option || !String(option.value || "").trim()) {
      return false;
    }

    const dataType = normalizeText_v4(
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v4(option.textContent);
    const optionValue = normalizeText_v4(option.value);

    return (
      dataType === "header" ||
      optionText.includes("cabecalho") ||
      optionText.includes("cabeçalho") ||
      optionValue.includes("cabecalho") ||
      optionValue.includes("cabeçalho")
    );
  }

  function createOption_v4(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (2) LER BOOTSTRAP DO MENU
  //###################################################################################

  function getBootstrap_v4() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getCurrentSettingsMenuKey_v4(form) {
    const inputMenuKey = form.querySelector('input[name="menu_key"]');
    const fromInput = String(inputMenuKey?.value || "").trim().toLowerCase();

    if (fromInput) {
      return fromInput;
    }

    const bootstrap = getBootstrap_v4();
    return String(bootstrap.settingsEditKey || "").trim().toLowerCase();
  }

  function getCurrentMenuSetting_v4(form) {
    const menuKey = getCurrentSettingsMenuKey_v4(form);
    const bootstrap = getBootstrap_v4();
    const settings = Array.isArray(bootstrap.sidebarMenuSettings)
      ? bootstrap.sidebarMenuSettings
      : [];

    return settings.find((setting) => {
      return String(setting?.key || "").trim().toLowerCase() === menuKey;
    }) || null;
  }

  function getHeaderOptionsFromBootstrap_v4(form) {
    const setting = getCurrentMenuSetting_v4(form);
    const fieldOptions = Array.isArray(setting?.process_field_options)
      ? setting.process_field_options
      : [];

    return fieldOptions
      .filter((item) => normalizeText_v4(item?.field_type) === "header")
      .map((item) => {
        return {
          key: String(item?.key || "").trim().toLowerCase(),
          label: String(item?.label || item?.key || "").trim()
        };
      })
      .filter((item) => item.key && item.label);
  }

  //###################################################################################
  // (3) LOCALIZAR FORMULÁRIO E SELECTS
  //###################################################################################

  function isProcessFieldsForm_v4(form) {
    const action = String(form.getAttribute("action") || "");
    const text = normalizeText_v4(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos") ||
      Boolean(form.querySelector('[name="visible_fields"]'))
    );
  }

  function findProcessFieldsForms_v4() {
    return Array.from(document.querySelectorAll("form")).filter(isProcessFieldsForm_v4);
  }

  function findSelectByLabel_v4(form, labels) {
    const labelElements = Array.from(form.querySelectorAll("label"));

    for (const label of labelElements) {
      const text = normalizeText_v4(label.textContent);

      if (!labels.some((labelText) => text.includes(labelText))) {
        continue;
      }

      const forId = String(label.getAttribute("for") || "").trim();

      if (forId) {
        const byId = form.querySelector(`#${CSS.escape(forId)}`);

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

  function findNameFieldSelect_v4(form) {
    const byLabel = findSelectByLabel_v4(form, [
      "nome do campo",
      "campo do processo"
    ]);

    if (byLabel) {
      return byLabel;
    }

    return Array.from(form.querySelectorAll("select")).find((select) => {
      const name = normalizeText_v4(select.name);
      const id = normalizeText_v4(select.id);

      if (select.dataset.processFieldHeaderSelectV4 === "1") {
        return false;
      }

      if (name.includes("header") || id.includes("header")) {
        return false;
      }

      return select.options.length > 0;
    }) || null;
  }

  //###################################################################################
  // (4) FILTRAR NOME DO CAMPO E CABEÇALHO DO CAMPO
  //###################################################################################

  function getHeaderOptionsFromNameSelect_v4(nameSelect) {
    const headers = [];
    const seen = new Set();

    Array.from(nameSelect.options).forEach((option) => {
      if (!isHeaderOption_v4(option)) {
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

  function getHeaderOptions_v4(form, nameSelect) {
    const merged = [];
    const seen = new Set();

    getHeaderOptionsFromBootstrap_v4(form)
      .concat(getHeaderOptionsFromNameSelect_v4(nameSelect))
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

  function filterNameFieldOptions_v4(nameSelect) {
    const selectedWasHeader = isHeaderOption_v4(nameSelect.selectedOptions[0]);

    Array.from(nameSelect.options).forEach((option) => {
      if (isHeaderOption_v4(option)) {
        option.remove();
      }
    });

    if (selectedWasHeader) {
      nameSelect.value = "";
    }
  }

  //###################################################################################
  // (5) LAYOUT LADO A LADO
  //###################################################################################

  function getFieldWrapper_v4(select) {
    return (
      select.closest(".field") ||
      select.closest(".form-field") ||
      select.closest(".form-group") ||
      select.parentElement
    );
  }

  function buildHeaderSelect_v4(headerOptions, selectedValue) {
    const select = document.createElement("select");
    select.dataset.processFieldHeaderSelectV4 = "1";

    select.appendChild(createOption_v4("", "Sem cabeçalho", selectedValue));

    headerOptions.forEach((header) => {
      select.appendChild(createOption_v4(header.key, header.label, selectedValue));
    });

    return select;
  }

  function removeOldManagers_v4(form) {
    form.querySelectorAll(
      ".process-fields-picker-row-v3, .process-fields-picker-row-v4, " +
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, .process-field-header-picker-v4"
    ).forEach((element) => {
      const nameSelect = element.querySelector("select:not([data-process-field-header-select-v4])");
      const parent = element.parentElement;

      if (nameSelect && parent) {
        parent.insertBefore(nameSelect.closest(".field") || nameSelect, element);
      }

      element.remove();
    });
  }

  function ensureSideBySideLayout_v4(form, nameSelect, headerOptions) {
    if (form.querySelector('[data-main-header-select-v4="1"]')) {
      return form.querySelector('[data-main-header-select-v4="1"]');
    }

    const nameWrapper = getFieldWrapper_v4(nameSelect);
    const row = document.createElement("div");
    row.className = "process-fields-picker-row-v4";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-field-header-picker-v4";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const headerSelect = buildHeaderSelect_v4(headerOptions, "");
    headerSelect.dataset.mainHeaderSelectV4 = "1";

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(headerSelect);

    if (nameWrapper && nameWrapper.parentElement) {
      nameWrapper.parentElement.insertBefore(row, nameWrapper);
      row.appendChild(nameWrapper);
      row.appendChild(headerWrapper);
    }

    return headerSelect;
  }

  function renameLabels_v4(root) {
    Array.from(root.querySelectorAll("label, th, strong, span, div")).forEach((element) => {
      const text = normalizeText_v4(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  //###################################################################################
  // (6) PAYLOAD PARA GRAVAR NO BANCO
  //###################################################################################

  function getConfiguredFieldRows_v4(form, nameSelect) {
    const controls = Array.from(form.querySelectorAll('[name="visible_fields"]')).filter((control) => {
      return control !== nameSelect && !control.dataset.generatedProcessFieldV4;
    });

    return controls
      .map((control, index) => {
        const row = (
          control.closest("tr") ||
          control.closest(".configured-field-row") ||
          control.closest(".settings-row") ||
          control.closest(".field-row") ||
          control.parentElement
        );

        const headerSelect = row?.querySelector('[data-row-header-select-v4="1"]');
        const oldHeader = row?.querySelector('[name="visible_headers"]');
        const oldHeaders = Array.from(form.querySelectorAll('[name="visible_headers"]'));

        return {
          fieldKey: String(control.value || "").trim().toLowerCase(),
          headerKey: String(
            headerSelect?.value ||
            oldHeader?.value ||
            oldHeaders[index]?.value ||
            ""
          ).trim().toLowerCase()
        };
      })
      .filter((row) => row.fieldKey);
  }

  function getSelectedFieldRow_v4(nameSelect, headerSelect) {
    const fieldKey = String(nameSelect.value || "").trim().toLowerCase();

    if (!fieldKey) {
      return null;
    }

    if (isHeaderOption_v4(nameSelect.selectedOptions[0])) {
      return null;
    }

    return {
      fieldKey,
      headerKey: String(headerSelect?.value || "").trim().toLowerCase()
    };
  }

  function buildPayloadRows_v4(form, nameSelect, headerSelect) {
    const rows = getConfiguredFieldRows_v4(form, nameSelect);
    const selectedRow = getSelectedFieldRow_v4(nameSelect, headerSelect);

    if (selectedRow && !rows.some((row) => row.fieldKey === selectedRow.fieldKey)) {
      rows.push(selectedRow);
    }

    return rows;
  }

  function syncFormData_v4(form, nameSelect, headerSelect, formData) {
    const rows = buildPayloadRows_v4(form, nameSelect, headerSelect);

    formData.delete("visible_fields");
    formData.delete("visible_headers");
    formData.delete("process_field_header_picker");

    rows.forEach((row) => {
      formData.append("visible_fields", row.fieldKey);
      formData.append("visible_headers", row.headerKey);
    });
  }

  function addSubmitFallbackInputs_v4(form, nameSelect, headerSelect) {
    form.querySelectorAll('[data-generated-process-field-v4="1"]').forEach((input) => {
      input.remove();
    });

    const rows = buildPayloadRows_v4(form, nameSelect, headerSelect);

    rows.forEach((row) => {
      const fieldInput = document.createElement("input");
      fieldInput.type = "hidden";
      fieldInput.name = "visible_fields";
      fieldInput.value = row.fieldKey;
      fieldInput.dataset.generatedProcessFieldV4 = "1";

      const headerInput = document.createElement("input");
      headerInput.type = "hidden";
      headerInput.name = "visible_headers";
      headerInput.value = row.headerKey;
      headerInput.dataset.generatedProcessFieldV4 = "1";

      form.appendChild(fieldInput);
      form.appendChild(headerInput);
    });
  }

  //###################################################################################
  // (7) CAMPOS CONFIGURADOS - CABEÇALHO POR LINHA
  //###################################################################################

  function ensureConfiguredRows_v4(form, nameSelect, headerOptions) {
    const controls = Array.from(form.querySelectorAll('[name="visible_fields"]')).filter((control) => {
      return control !== nameSelect && !control.dataset.generatedProcessFieldV4;
    });

    controls.forEach((control, index) => {
      const row = (
        control.closest("tr") ||
        control.closest(".configured-field-row") ||
        control.closest(".settings-row") ||
        control.closest(".field-row") ||
        control.parentElement
      );

      if (!row || row.querySelector('[data-row-header-select-v4="1"]')) {
        return;
      }

      const oldHeader = row.querySelector('[name="visible_headers"]');
      const oldHeaders = Array.from(form.querySelectorAll('[name="visible_headers"]'));
      const selectedHeader = String(oldHeader?.value || oldHeaders[index]?.value || "").trim().toLowerCase();

      const headerSelect = buildHeaderSelect_v4(headerOptions, selectedHeader);
      headerSelect.name = "visible_headers";
      headerSelect.dataset.rowHeaderSelectV4 = "1";

      const table = row.closest("table");

      if (table && row.tagName.toLowerCase() === "tr") {
        const headerRow = table.querySelector("thead tr");

        if (headerRow && headerRow.dataset.headerColumnV4 !== "1") {
          const th = document.createElement("th");
          th.textContent = "CABEÇALHO DO CAMPO";
          headerRow.insertBefore(th, headerRow.lastElementChild);
          headerRow.dataset.headerColumnV4 = "1";
        }

        const td = document.createElement("td");
        td.appendChild(headerSelect);
        row.insertBefore(td, row.lastElementChild);
        return;
      }

      const wrapper = document.createElement("div");
      wrapper.className = "configured-field-header-picker-v4";

      const label = document.createElement("label");
      label.textContent = "Cabeçalho do campo";

      wrapper.appendChild(label);
      wrapper.appendChild(headerSelect);
      row.appendChild(wrapper);
    });
  }

  //###################################################################################
  // (8) ESTILO
  //###################################################################################

  function injectStyle_v4() {
    if (document.getElementById("process-fields-header-manager-v4-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v4-style";
    style.textContent = `
      .process-fields-picker-row-v4 {
        display: grid;
        grid-template-columns: minmax(360px, 1fr) minmax(240px, 320px);
        gap: 12px;
        align-items: end;
        width: 100%;
        max-width: 1320px;
      }

      .process-fields-picker-row-v4 > * {
        min-width: 0;
      }

      .process-fields-picker-row-v4 .field,
      .process-field-header-picker-v4 {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .process-field-header-picker-v4 label,
      .configured-field-header-picker-v4 label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-fields-picker-row-v4 select,
      .process-field-header-picker-v4 select,
      .configured-field-header-picker-v4 select,
      select[data-row-header-select-v4="1"] {
        width: 100%;
        min-height: 38px;
      }

      @media (max-width: 900px) {
        .process-fields-picker-row-v4 {
          grid-template-columns: 1fr;
          max-width: 100%;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (9) INICIALIZAR
  //###################################################################################

  function initForm_v4(form) {
    if (form.dataset.processFieldsHeaderManagerV4 === "1") {
      return;
    }

    const root = form.closest(".card") || form.closest("section") || form;

    renameLabels_v4(root);

    const nameSelect = findNameFieldSelect_v4(form);

    if (!nameSelect) {
      return;
    }

    form.dataset.processFieldsHeaderManagerV4 = "1";

    const headerOptions = getHeaderOptions_v4(form, nameSelect);

    filterNameFieldOptions_v4(nameSelect);
    removeOldManagers_v4(form);

    const headerSelect = ensureSideBySideLayout_v4(form, nameSelect, headerOptions);

    ensureConfiguredRows_v4(form, nameSelect, headerOptions);

    form.addEventListener("submit", () => {
      addSubmitFallbackInputs_v4(form, nameSelect, headerSelect);
    }, true);

    form.addEventListener("formdata", (event) => {
      syncFormData_v4(form, nameSelect, headerSelect, event.formData);
    });
  }

  function initProcessFieldsHeaderManager_v4() {
    injectStyle_v4();

    findProcessFieldsForms_v4().forEach((form) => {
      initForm_v4(form);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v4);
  } else {
    initProcessFieldsHeaderManager_v4();
  }

  window.setTimeout(initProcessFieldsHeaderManager_v4, 300);
  window.setTimeout(initProcessFieldsHeaderManager_v4, 900);
})();
