(function () {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES E NORMALIZACAO
  //###################################################################################

  const NONE_HEADER_VALUE = "";

  function normalizeText_v2(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v2(value) {
    return normalizeText_v2(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function isEmptyOption_v2(option) {
    return !String(option?.value || "").trim();
  }

  function isHeaderOption_v2(option) {
    if (!option || isEmptyOption_v2(option)) {
      return false;
    }

    const fieldType = normalizeText_v2(
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v2(option.textContent);
    const optionValue = normalizeText_v2(option.value);

    return (
      fieldType === "header" ||
      optionText.includes("cabecalho") ||
      optionText.includes("cabeçalho") ||
      optionValue.includes("cabecalho") ||
      optionValue.includes("cabeçalho")
    );
  }

  function createOption_v2(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULARIO DA CONFIGURACAO DOS CAMPOS
  //###################################################################################

  function isProcessFieldsForm_v2(form) {
    const action = String(form.getAttribute("action") || "");
    const text = normalizeText_v2(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos") ||
      Boolean(form.querySelector('[name="visible_fields"]'))
    );
  }

  function findProcessFieldsForms_v2() {
    return Array.from(document.querySelectorAll("form")).filter(isProcessFieldsForm_v2);
  }

  function findCardRoot_v2(form) {
    return (
      form.closest(".card") ||
      form.closest("section") ||
      form.closest("[id]") ||
      form
    );
  }

  //###################################################################################
  // (3) LOCALIZAR SELECT NOME DO CAMPO
  //###################################################################################

  function findSelectByLabelText_v2(form, expectedTextList) {
    const labels = Array.from(form.querySelectorAll("label"));

    for (const label of labels) {
      const labelText = normalizeText_v2(label.textContent);

      if (!expectedTextList.some((expectedText) => labelText.includes(expectedText))) {
        continue;
      }

      const labelFor = String(label.getAttribute("for") || "").trim();

      if (labelFor) {
        const byId = form.querySelector(`#${CSS.escape(labelFor)}`);

        if (byId && byId.tagName && byId.tagName.toLowerCase() === "select") {
          return byId;
        }
      }

      const nearbySelect =
        label.parentElement?.querySelector("select") ||
        label.nextElementSibling;

      if (nearbySelect && nearbySelect.tagName && nearbySelect.tagName.toLowerCase() === "select") {
        return nearbySelect;
      }
    }

    return null;
  }

  function findNameFieldSelect_v2(form) {
    const byLabel = findSelectByLabelText_v2(form, [
      "nome do campo",
      "campo do processo"
    ]);

    if (byLabel) {
      return byLabel;
    }

    const candidates = Array.from(form.querySelectorAll("select")).filter((select) => {
      const name = normalizeText_v2(select.name);
      const id = normalizeText_v2(select.id);

      if (select.dataset.headerPickerV2 === "1") {
        return false;
      }

      if (name.includes("header") || id.includes("header")) {
        return false;
      }

      if (name === "visible_headers") {
        return false;
      }

      return select.options.length > 0;
    });

    const preferred = candidates.find((select) => {
      const name = normalizeText_v2(select.name);
      const id = normalizeText_v2(select.id);

      return (
        name.includes("field") ||
        name.includes("visible") ||
        id.includes("field")
      );
    });

    return preferred || candidates[0] || null;
  }

  //###################################################################################
  // (4) EXTRAIR CABECALHOS E FILTRAR NOME DO CAMPO
  //###################################################################################

  function extractHeaderOptionsFromNameSelect_v2(nameSelect) {
    const headerOptions = [];
    const seen = new Set();

    Array.from(nameSelect.options).forEach((option) => {
      if (!isHeaderOption_v2(option)) {
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
      headerOptions.push({
        key,
        label
      });
    });

    return headerOptions;
  }

  function removeHeaderOptionsFromNameSelect_v2(nameSelect) {
    const options = Array.from(nameSelect.options);
    const selectedWasHeader = isHeaderOption_v2(nameSelect.selectedOptions[0]);

    options.forEach((option) => {
      if (!isHeaderOption_v2(option)) {
        return;
      }

      option.remove();
    });

    if (selectedWasHeader) {
      const firstValidOption = Array.from(nameSelect.options).find((option) => {
        return !isEmptyOption_v2(option);
      });

      if (firstValidOption) {
        nameSelect.value = firstValidOption.value;
      } else {
        nameSelect.value = "";
      }
    }
  }

  function renameLabels_v2(root) {
    Array.from(root.querySelectorAll("label, th, strong, span, div")).forEach((element) => {
      const text = normalizeText_v2(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
        return;
      }

      if (text.includes("campo do processo")) {
        element.childNodes.forEach((node) => {
          if (node.nodeType !== Node.TEXT_NODE) {
            return;
          }

          node.textContent = node.textContent
            .replace(/CAMPO DO PROCESSO/g, "NOME DO CAMPO")
            .replace(/Campo do processo/g, "Nome do campo")
            .replace(/campo do processo/g, "nome do campo");
        });
      }
    });
  }

  //###################################################################################
  // (5) CRIAR SELECT CABECALHO DO CAMPO SOMENTE COM CABECALHOS
  //###################################################################################

  function buildHeaderPicker_v2(headerOptions, selectedValue) {
    const select = document.createElement("select");
    select.name = "process_field_header_picker";
    select.dataset.headerPickerV2 = "1";

    select.appendChild(createOption_v2(NONE_HEADER_VALUE, "Sem cabeçalho", selectedValue));

    headerOptions.forEach((headerOption) => {
      select.appendChild(
        createOption_v2(
          headerOption.key,
          headerOption.label,
          selectedValue
        )
      );
    });

    return select;
  }

  function removeOldHeaderPickerWrappers_v2(form) {
    form.querySelectorAll(
      ".process-field-header-picker-v1, .configured-field-header-picker-v1"
    ).forEach((element) => element.remove());

    form.querySelectorAll(
      '[data-process-field-header-picker="1"], [data-configured-field-header-picker="1"]'
    ).forEach((element) => {
      const wrapper = element.closest(".process-field-header-picker-v1") ||
        element.closest(".configured-field-header-picker-v1");

      if (wrapper) {
        wrapper.remove();
      }
    });
  }

  function ensureMainHeaderPicker_v2(form, nameSelect, headerOptions) {
    let picker = form.querySelector('[data-main-header-picker-v2="1"]');

    if (picker) {
      return picker;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "process-field-header-picker-v2";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    picker = buildHeaderPicker_v2(headerOptions, "");
    picker.dataset.mainHeaderPickerV2 = "1";

    wrapper.appendChild(label);
    wrapper.appendChild(picker);

    const fieldWrapper =
      nameSelect.closest(".field") ||
      nameSelect.closest(".form-field") ||
      nameSelect.closest(".form-group") ||
      nameSelect.parentElement;

    if (fieldWrapper && fieldWrapper.parentElement) {
      fieldWrapper.parentElement.insertBefore(wrapper, fieldWrapper.nextSibling);
    } else {
      nameSelect.insertAdjacentElement("afterend", wrapper);
    }

    return picker;
  }

  //###################################################################################
  // (6) CAMPOS CONFIGURADOS - ADICIONAR COLUNA CABECALHO DO CAMPO
  //###################################################################################

  function findConfiguredFieldControls_v2(form, nameSelect) {
    return Array.from(form.querySelectorAll('[name="visible_fields"]')).filter((control) => {
      return control !== nameSelect;
    });
  }

  function getConfiguredRow_v2(control) {
    return (
      control.closest("tr") ||
      control.closest(".configured-field-row") ||
      control.closest(".settings-row") ||
      control.closest(".field-row") ||
      control.parentElement?.parentElement ||
      control.parentElement
    );
  }

  function getExistingHeaderValue_v2(form, row, rowIndex) {
    const picker = row?.querySelector('[data-row-header-picker-v2="1"]');

    if (picker) {
      return String(picker.value || "").trim().toLowerCase();
    }

    const existingInRow = row?.querySelector('[name="visible_headers"]');

    if (existingInRow) {
      return String(existingInRow.value || "").trim().toLowerCase();
    }

    const allHeaders = Array.from(form.querySelectorAll('[name="visible_headers"]'));

    return String(allHeaders[rowIndex]?.value || "").trim().toLowerCase();
  }

  function ensureHeaderColumn_v2(table) {
    const headerRow = table.querySelector("thead tr");

    if (!headerRow || headerRow.dataset.headerColumnV2 === "1") {
      return;
    }

    const th = document.createElement("th");
    th.textContent = "CABEÇALHO DO CAMPO";

    const actionHeader = Array.from(headerRow.children).find((cell) => {
      return normalizeText_v2(cell.textContent).includes("acoes") ||
        normalizeText_v2(cell.textContent).includes("ações");
    });

    if (actionHeader) {
      headerRow.insertBefore(th, actionHeader);
    } else {
      headerRow.appendChild(th);
    }

    headerRow.dataset.headerColumnV2 = "1";
  }

  function ensureConfiguredRowHeaderPicker_v2(form, row, rowIndex, headerOptions) {
    if (!row || row.querySelector('[data-row-header-picker-v2="1"]')) {
      return;
    }

    const selectedValue = getExistingHeaderValue_v2(form, row, rowIndex);
    const picker = buildHeaderPicker_v2(headerOptions, selectedValue);

    picker.name = "visible_headers";
    picker.dataset.rowHeaderPickerV2 = "1";

    const table = row.closest("table");

    if (table && row.tagName.toLowerCase() === "tr") {
      ensureHeaderColumn_v2(table);

      const td = document.createElement("td");
      td.appendChild(picker);

      const actionCell = Array.from(row.children).find((cell) => {
        const text = normalizeText_v2(cell.textContent);

        return (
          text.includes("acoes") ||
          text.includes("ações") ||
          text.includes("↑") ||
          text.includes("↓") ||
          text.includes("x")
        );
      });

      if (actionCell) {
        row.insertBefore(td, actionCell);
      } else {
        row.appendChild(td);
      }

      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "configured-field-header-picker-v2";

    const label = document.createElement("label");
    label.textContent = "Cabeçalho do campo";

    wrapper.appendChild(label);
    wrapper.appendChild(picker);

    row.appendChild(wrapper);
  }

  function ensureConfiguredRowsHeaderPickers_v2(form, nameSelect, headerOptions) {
    findConfiguredFieldControls_v2(form, nameSelect).forEach((control, rowIndex) => {
      const row = getConfiguredRow_v2(control);

      ensureConfiguredRowHeaderPicker_v2(form, row, rowIndex, headerOptions);
    });
  }

  //###################################################################################
  // (7) SINCRONIZAR ENVIO DO FORMULARIO
  //###################################################################################

  function removeOldHiddenHeaders_v2(form) {
    form.querySelectorAll('input[type="hidden"][name="visible_headers"][data-generated-header-v2="1"]').forEach((input) => {
      input.remove();
    });
  }

  function ensureSelectedFieldSubmission_v2(form, nameSelect, mainHeaderPicker) {
    const selectedValue = String(nameSelect.value || "").trim().toLowerCase();

    if (!selectedValue) {
      return;
    }

    const selectedOption = nameSelect.selectedOptions[0];

    if (isHeaderOption_v2(selectedOption)) {
      return;
    }

    const existingFieldValues = findConfiguredFieldControls_v2(form, nameSelect).map((control) => {
      return String(control.value || "").trim().toLowerCase();
    });

    if (existingFieldValues.includes(selectedValue)) {
      return;
    }

    if (String(nameSelect.name || "") !== "visible_fields") {
      const fieldInput = document.createElement("input");
      fieldInput.type = "hidden";
      fieldInput.name = "visible_fields";
      fieldInput.value = selectedValue;
      fieldInput.dataset.generatedHeaderV2 = "1";

      form.appendChild(fieldInput);
    }

    const headerInput = document.createElement("input");
    headerInput.type = "hidden";
    headerInput.name = "visible_headers";
    headerInput.value = String(mainHeaderPicker?.value || "").trim().toLowerCase();
    headerInput.dataset.generatedHeaderV2 = "1";

    form.appendChild(headerInput);
  }

  function syncConfiguredHeaders_v2(form, nameSelect) {
    const configuredControls = findConfiguredFieldControls_v2(form, nameSelect);

    configuredControls.forEach((control) => {
      const row = getConfiguredRow_v2(control);
      const picker = row?.querySelector('[data-row-header-picker-v2="1"]');

      if (!picker) {
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "visible_headers";
        hiddenInput.value = "";
        hiddenInput.dataset.generatedHeaderV2 = "1";
        control.insertAdjacentElement("afterend", hiddenInput);
      }
    });
  }

  function prepareFormSubmit_v2(form, nameSelect, mainHeaderPicker) {
    removeOldHiddenHeaders_v2(form);
    syncConfiguredHeaders_v2(form, nameSelect);
    ensureSelectedFieldSubmission_v2(form, nameSelect, mainHeaderPicker);
  }

  //###################################################################################
  // (8) ESTILO
  //###################################################################################

  function injectStyle_v2() {
    if (document.getElementById("process-fields-header-manager-v2-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v2-style";
    style.textContent = `
      .process-field-header-picker-v2,
      .configured-field-header-picker-v2 {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 220px;
        margin-top: 8px;
      }

      .process-field-header-picker-v2 label,
      .configured-field-header-picker-v2 label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-field-header-picker-v2 select,
      .configured-field-header-picker-v2 select,
      select[data-row-header-picker-v2="1"] {
        width: 100%;
        min-height: 38px;
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (9) INICIALIZAR FORMULARIO
  //###################################################################################

  function initForm_v2(form) {
    const root = findCardRoot_v2(form);

    renameLabels_v2(root);
    removeOldHeaderPickerWrappers_v2(form);

    const nameSelect = findNameFieldSelect_v2(form);

    if (!nameSelect) {
      return;
    }

    const headerOptions = extractHeaderOptionsFromNameSelect_v2(nameSelect);

    removeHeaderOptionsFromNameSelect_v2(nameSelect);

    const mainHeaderPicker = ensureMainHeaderPicker_v2(form, nameSelect, headerOptions);

    ensureConfiguredRowsHeaderPickers_v2(form, nameSelect, headerOptions);

    form.addEventListener("submit", () => {
      prepareFormSubmit_v2(form, nameSelect, mainHeaderPicker);
    });
  }

  function initProcessFieldsHeaderManager_v2() {
    injectStyle_v2();

    findProcessFieldsForms_v2().forEach((form) => {
      initForm_v2(form);
    });
  }

  //###################################################################################
  // (10) BOOT E MUTATION OBSERVER
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v2);
  } else {
    initProcessFieldsHeaderManager_v2();
  }

  window.setTimeout(initProcessFieldsHeaderManager_v2, 300);
  window.setTimeout(initProcessFieldsHeaderManager_v2, 900);
})();
