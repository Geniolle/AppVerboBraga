(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO E HELPERS
  //###################################################################################

  const HEADER_NONE_VALUE = "";

  function normalizeText_v1(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v1(value) {
    return normalizeText_v1(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function replaceTextInNode_v1(node, oldValue, newValue) {
    if (!node || !node.textContent) {
      return;
    }

    if (node.children && node.children.length > 0) {
      Array.from(node.childNodes).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          child.textContent = child.textContent.replace(oldValue, newValue);
        }
      });
      return;
    }

    node.textContent = node.textContent.replace(oldValue, newValue);
  }

  function createOption_v1(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  function getFormMenuKey_v1(form) {
    const input = form.querySelector('input[name="menu_key"]');
    return String(input?.value || "").trim().toLowerCase();
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULARIOS DA CONFIGURACAO DOS CAMPOS
  //###################################################################################

  function findProcessFieldsForms_v1() {
    const forms = Array.from(document.querySelectorAll("form"));

    return forms.filter((form) => {
      const action = String(form.getAttribute("action") || "");
      const hasVisibleFields = Boolean(
        form.querySelector('[name="visible_fields"]') ||
        form.querySelector('select[name*="field"]')
      );

      return action.includes("/settings/menu/process-fields") || hasVisibleFields;
    });
  }

  function findProcessFieldsCard_v1(form) {
    return (
      form.closest(".card") ||
      form.closest("section") ||
      form.closest("[id]") ||
      document.body
    );
  }

  //###################################################################################
  // (3) RENOMEAR LABEL VISUAL PARA NOME DO CAMPO
  //###################################################################################

  function renameProcessFieldLabels_v1(root) {
    const candidates = Array.from(root.querySelectorAll("label, th, strong, span, div"));

    candidates.forEach((element) => {
      const text = normalizeText_v1(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }

      if (text.includes("campo do processo")) {
        replaceTextInNode_v1(element, "Campo do processo", "Nome do campo");
        replaceTextInNode_v1(element, "CAMPO DO PROCESSO", "NOME DO CAMPO");
      }
    });
  }

  //###################################################################################
  // (4) LER CABECALHOS CRIADOS EM CAMPOS ADICIONAIS
  //###################################################################################

  function findAdditionalFieldRows_v1() {
    const typeControls = Array.from(
      document.querySelectorAll(
        'select[name="additional_field_type"], select[name*="additional_field_type"]'
      )
    );

    return typeControls
      .map((typeControl) => {
        return (
          typeControl.closest("tr") ||
          typeControl.closest(".settings-row") ||
          typeControl.closest(".additional-field-row") ||
          typeControl.closest(".field-row") ||
          typeControl.parentElement?.parentElement ||
          typeControl.parentElement
        );
      })
      .filter(Boolean);
  }

  function getHeaderOptionsFromAdditionalFields_v1() {
    const options = [];
    const seen = new Set();

    findAdditionalFieldRows_v1().forEach((row) => {
      const typeControl =
        row.querySelector('select[name="additional_field_type"]') ||
        row.querySelector('select[name*="additional_field_type"]');

      if (!typeControl || normalizeText_v1(typeControl.value) !== "header") {
        return;
      }

      const keyInput =
        row.querySelector('input[name="additional_field_key"]') ||
        row.querySelector('input[name*="additional_field_key"]') ||
        row.querySelector('input[name*="field_key"]');

      const labelInput =
        row.querySelector('input[name="additional_field_label"]') ||
        row.querySelector('input[name*="additional_field_label"]') ||
        row.querySelector('input[name*="label"]') ||
        row.querySelector('input[type="text"]');

      const label = String(labelInput?.value || "").trim();
      const key = String(keyInput?.value || normalizeKey_v1(label)).trim().toLowerCase();

      if (!key || !label || seen.has(key)) {
        return;
      }

      seen.add(key);
      options.push({
        key: key,
        label: label,
      });
    });

    return options;
  }

  function getHeaderOptionsFromCurrentForm_v1(form) {
    const options = [];
    const seen = new Set();

    Array.from(form.querySelectorAll("option")).forEach((option) => {
      const fieldType = normalizeText_v1(
        option.dataset.fieldType ||
        option.dataset.type ||
        option.getAttribute("data-field-type") ||
        option.getAttribute("data-type") ||
        ""
      );

      if (fieldType !== "header") {
        return;
      }

      const key = String(option.value || "").trim().toLowerCase();
      const label = String(option.textContent || "").trim();

      if (!key || !label || seen.has(key)) {
        return;
      }

      seen.add(key);
      options.push({
        key: key,
        label: label,
      });
    });

    return options;
  }

  function getHeaderOptions_v1(form) {
    const merged = [];
    const seen = new Set();

    getHeaderOptionsFromCurrentForm_v1(form)
      .concat(getHeaderOptionsFromAdditionalFields_v1())
      .forEach((item) => {
        const key = String(item.key || "").trim().toLowerCase();
        const label = String(item.label || "").trim();

        if (!key || !label || seen.has(key)) {
          return;
        }

        seen.add(key);
        merged.push({
          key: key,
          label: label,
        });
      });

    return merged;
  }

  //###################################################################################
  // (5) IDENTIFICAR SELECT DO NOME DO CAMPO
  //###################################################################################

  function findMainFieldSelect_v1(form) {
    const selects = Array.from(form.querySelectorAll("select"));

    const exact = selects.find((select) => {
      const name = String(select.name || "").toLowerCase();
      const id = String(select.id || "").toLowerCase();
      return (
        name === "process_field" ||
        name === "field_key" ||
        id.includes("process-field") ||
        id.includes("field-select")
      );
    });

    if (exact) {
      return exact;
    }

    return selects.find((select) => {
      const name = String(select.name || "").toLowerCase();
      return (
        name !== "visible_headers" &&
        !name.includes("header") &&
        select.options.length > 0
      );
    }) || null;
  }

  //###################################################################################
  // (6) ADICIONAR SELECT CABECALHO DO CAMPO NO FORMULARIO
  //###################################################################################

  function buildHeaderSelect_v1(headerOptions, selectedValue) {
    const select = document.createElement("select");
    select.name = "process_field_header_picker";
    select.dataset.processFieldHeaderPicker = "1";

    select.appendChild(createOption_v1(HEADER_NONE_VALUE, "Sem cabeçalho", selectedValue));

    headerOptions.forEach((item) => {
      select.appendChild(createOption_v1(item.key, item.label, selectedValue));
    });

    return select;
  }

  function ensureMainHeaderPicker_v1(form) {
    const mainFieldSelect = findMainFieldSelect_v1(form);

    if (!mainFieldSelect) {
      return null;
    }

    if (form.querySelector("[data-process-field-header-picker='1']")) {
      return form.querySelector("[data-process-field-header-picker='1']");
    }

    const headerOptions = getHeaderOptions_v1(form);

    const wrapper = document.createElement("div");
    wrapper.className = "process-field-header-picker-v1";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const select = buildHeaderSelect_v1(headerOptions, "");

    wrapper.appendChild(label);
    wrapper.appendChild(select);

    const parentField =
      mainFieldSelect.closest(".field") ||
      mainFieldSelect.closest(".form-field") ||
      mainFieldSelect.closest("label") ||
      mainFieldSelect.parentElement;

    if (parentField && parentField.parentElement) {
      parentField.parentElement.insertBefore(wrapper, parentField.nextSibling);
    } else {
      form.insertBefore(wrapper, mainFieldSelect.nextSibling);
    }

    return select;
  }

  //###################################################################################
  // (7) CONFIGURAR LINHAS JA ADICIONADAS COM CABECALHO DO CAMPO
  //###################################################################################

  function getFieldRows_v1(form) {
    const visibleFieldInputs = Array.from(form.querySelectorAll('[name="visible_fields"]'));

    return visibleFieldInputs
      .map((input) => {
        return (
          input.closest("tr") ||
          input.closest(".configured-field-row") ||
          input.closest(".settings-row") ||
          input.closest(".field-row") ||
          input.parentElement?.parentElement ||
          input.parentElement
        );
      })
      .filter(Boolean);
  }

  function getVisibleFieldInputFromRow_v1(row) {
    return row.querySelector('[name="visible_fields"]');
  }

  function getCurrentHeaderValueForField_v1(form, fieldInput, rowIndex) {
    const row = fieldInput.closest("tr") || fieldInput.parentElement;
    const rowHeaderInput = row?.querySelector('[name="visible_headers"]');

    if (rowHeaderInput) {
      return String(rowHeaderInput.value || "").trim().toLowerCase();
    }

    const allHeaderInputs = Array.from(form.querySelectorAll('[name="visible_headers"]'));
    const indexedHeader = allHeaderInputs[rowIndex];

    return String(indexedHeader?.value || "").trim().toLowerCase();
  }

  function ensureHeaderColumnInTable_v1(table) {
    const headerRow = table.querySelector("thead tr");

    if (!headerRow || headerRow.dataset.headerColumnV1 === "1") {
      return;
    }

    const actionHeader = Array.from(headerRow.children).find((cell) => {
      return normalizeText_v1(cell.textContent).includes("acoes");
    });

    const th = document.createElement("th");
    th.textContent = "CABEÇALHO DO CAMPO";

    if (actionHeader) {
      headerRow.insertBefore(th, actionHeader);
    } else {
      headerRow.appendChild(th);
    }

    headerRow.dataset.headerColumnV1 = "1";
  }

  function ensureConfiguredRowHeaderPicker_v1(form, row, rowIndex) {
    if (row.querySelector("[data-configured-field-header-picker='1']")) {
      return;
    }

    const fieldInput = getVisibleFieldInputFromRow_v1(row);

    if (!fieldInput) {
      return;
    }

    const headerOptions = getHeaderOptions_v1(form);
    const selectedValue = getCurrentHeaderValueForField_v1(form, fieldInput, rowIndex);
    const select = buildHeaderSelect_v1(headerOptions, selectedValue);

    select.name = "visible_headers";
    select.dataset.configuredFieldHeaderPicker = "1";

    const table = row.closest("table");

    if (table && row.tagName.toLowerCase() === "tr") {
      ensureHeaderColumnInTable_v1(table);

      const actionCell = Array.from(row.children).find((cell) => {
        return normalizeText_v1(cell.textContent).includes("↑") || normalizeText_v1(cell.textContent).includes("x");
      });

      const td = document.createElement("td");
      td.appendChild(select);

      if (actionCell) {
        row.insertBefore(td, actionCell);
      } else {
        row.appendChild(td);
      }

      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "configured-field-header-picker-v1";

    const label = document.createElement("label");
    label.textContent = "Cabeçalho do campo";

    wrapper.appendChild(label);
    wrapper.appendChild(select);
    row.appendChild(wrapper);
  }

  function ensureConfiguredRowsHeaderPickers_v1(form) {
    getFieldRows_v1(form).forEach((row, rowIndex) => {
      ensureConfiguredRowHeaderPicker_v1(form, row, rowIndex);
    });
  }

  //###################################################################################
  // (8) SINCRONIZAR visible_headers ANTES DE GRAVAR
  //###################################################################################

  function syncVisibleHeadersBeforeSubmit_v1(form) {
    const visibleFieldInputs = Array.from(form.querySelectorAll('[name="visible_fields"]'));
    const configuredPickers = Array.from(
      form.querySelectorAll("[data-configured-field-header-picker='1']")
    );

    form.querySelectorAll('input[type="hidden"][name="visible_headers"]').forEach((input) => {
      input.remove();
    });

    visibleFieldInputs.forEach((fieldInput, index) => {
      const row =
        fieldInput.closest("tr") ||
        fieldInput.closest(".configured-field-row") ||
        fieldInput.closest(".settings-row") ||
        fieldInput.closest(".field-row") ||
        fieldInput.parentElement;

      const rowPicker =
        row?.querySelector("[data-configured-field-header-picker='1']") ||
        configuredPickers[index];

      const hiddenInput = document.createElement("input");
      hiddenInput.type = "hidden";
      hiddenInput.name = "visible_headers";
      hiddenInput.value = String(rowPicker?.value || "").trim().toLowerCase();

      fieldInput.insertAdjacentElement("afterend", hiddenInput);
    });
  }

  function appendSelectedFieldIfNeeded_v1(form) {
    const mainFieldSelect = findMainFieldSelect_v1(form);
    const mainHeaderPicker = form.querySelector("[data-process-field-header-picker='1']");

    if (!mainFieldSelect) {
      return;
    }

    const selectedField = String(mainFieldSelect.value || "").trim().toLowerCase();

    if (!selectedField) {
      return;
    }

    const existingFields = Array.from(form.querySelectorAll('[name="visible_fields"]')).map((input) => {
      return String(input.value || "").trim().toLowerCase();
    });

    if (existingFields.includes(selectedField)) {
      return;
    }

    const hiddenField = document.createElement("input");
    hiddenField.type = "hidden";
    hiddenField.name = "visible_fields";
    hiddenField.value = selectedField;

    const hiddenHeader = document.createElement("input");
    hiddenHeader.type = "hidden";
    hiddenHeader.name = "visible_headers";
    hiddenHeader.value = String(mainHeaderPicker?.value || "").trim().toLowerCase();

    form.appendChild(hiddenField);
    form.appendChild(hiddenHeader);
  }

  //###################################################################################
  // (9) ESTILO VISUAL
  //###################################################################################

  function injectStyles_v1() {
    if (document.getElementById("process-fields-header-manager-v1-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v1-style";
    style.textContent = `
      .process-field-header-picker-v1,
      .configured-field-header-picker-v1 {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 220px;
      }

      .process-field-header-picker-v1 label,
      .configured-field-header-picker-v1 label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-field-header-picker-v1 select,
      .configured-field-header-picker-v1 select,
      select[data-configured-field-header-picker="1"] {
        width: 100%;
        min-height: 38px;
      }

      @media (min-width: 720px) {
        .process-field-header-picker-v1 {
          margin-top: 0;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (10) INICIALIZAR
  //###################################################################################

  function initProcessFieldsHeaderManager_v1() {
    injectStyles_v1();

    findProcessFieldsForms_v1().forEach((form) => {
      const card = findProcessFieldsCard_v1(form);

      renameProcessFieldLabels_v1(card);
      ensureMainHeaderPicker_v1(form);
      ensureConfiguredRowsHeaderPickers_v1(form);

      form.addEventListener("submit", () => {
        appendSelectedFieldIfNeeded_v1(form);
        ensureConfiguredRowsHeaderPickers_v1(form);
        syncVisibleHeadersBeforeSubmit_v1(form);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v1);
  } else {
    initProcessFieldsHeaderManager_v1();
  }
})();
