(function () {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES E NORMALIZAÇÃO
  //###################################################################################

  const HEADER_NONE_VALUE = "";

  function normalizeText_v3(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v3(value) {
    return normalizeText_v3(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function isEmptyOption_v3(option) {
    return !String(option?.value || "").trim();
  }

  function isHeaderOption_v3(option) {
    if (!option || isEmptyOption_v3(option)) {
      return false;
    }

    const dataType = normalizeText_v3(
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v3(option.textContent);
    const optionValue = normalizeText_v3(option.value);

    return (
      dataType === "header" ||
      optionText.includes("cabecalho") ||
      optionText.includes("cabeçalho") ||
      optionValue.includes("cabecalho") ||
      optionValue.includes("cabeçalho")
    );
  }

  function createOption_v3(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (String(value || "") === String(selectedValue || "")) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DA CONFIGURAÇÃO DOS CAMPOS
  //###################################################################################

  function isProcessFieldsForm_v3(form) {
    const action = String(form.getAttribute("action") || "");
    const text = normalizeText_v3(form.textContent);

    return (
      action.includes("/settings/menu/process-fields") ||
      text.includes("configuracao dos campos") ||
      text.includes("configuração dos campos") ||
      Boolean(form.querySelector('[name="visible_fields"]'))
    );
  }

  function findProcessFieldsForms_v3() {
    return Array.from(document.querySelectorAll("form")).filter(isProcessFieldsForm_v3);
  }

  function findCardRoot_v3(form) {
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

  function findSelectByLabelText_v3(form, expectedTextList) {
    const labels = Array.from(form.querySelectorAll("label"));

    for (const label of labels) {
      const labelText = normalizeText_v3(label.textContent);

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

  function findNameFieldSelect_v3(form) {
    const byLabel = findSelectByLabelText_v3(form, [
      "nome do campo",
      "campo do processo"
    ]);

    if (byLabel) {
      return byLabel;
    }

    const candidates = Array.from(form.querySelectorAll("select")).filter((select) => {
      const name = normalizeText_v3(select.name);
      const id = normalizeText_v3(select.id);

      if (select.dataset.mainHeaderPickerV3 === "1" || select.dataset.rowHeaderPickerV3 === "1") {
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
      const name = normalizeText_v3(select.name);
      const id = normalizeText_v3(select.id);

      return (
        name.includes("field") ||
        name.includes("visible") ||
        id.includes("field")
      );
    });

    return preferred || candidates[0] || null;
  }

  //###################################################################################
  // (4) FILTRAR OPÇÕES
  //###################################################################################

  function extractHeaderOptionsFromNameSelect_v3(nameSelect) {
    const headerOptions = [];
    const seen = new Set();

    Array.from(nameSelect.options).forEach((option) => {
      if (!isHeaderOption_v3(option)) {
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

  function removeHeaderOptionsFromNameSelect_v3(nameSelect) {
    const selectedWasHeader = isHeaderOption_v3(nameSelect.selectedOptions[0]);

    Array.from(nameSelect.options).forEach((option) => {
      if (isHeaderOption_v3(option)) {
        option.remove();
      }
    });

    if (selectedWasHeader) {
      const firstValidOption = Array.from(nameSelect.options).find((option) => {
        return !isEmptyOption_v3(option);
      });

      nameSelect.value = firstValidOption ? firstValidOption.value : "";
    }
  }

  function renameLabels_v3(root) {
    Array.from(root.querySelectorAll("label, th, strong, span, div")).forEach((element) => {
      const text = normalizeText_v3(element.textContent);

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
  // (5) CRIAR CABEÇALHO DO CAMPO LADO A LADO
  //###################################################################################

  function buildHeaderPicker_v3(headerOptions, selectedValue) {
    const select = document.createElement("select");
    select.name = "process_field_header_picker";
    select.dataset.headerPickerV3 = "1";

    select.appendChild(createOption_v3(HEADER_NONE_VALUE, "Sem cabeçalho", selectedValue));

    headerOptions.forEach((headerOption) => {
      select.appendChild(
        createOption_v3(
          headerOption.key,
          headerOption.label,
          selectedValue
        )
      );
    });

    return select;
  }

  function removeOldHeaderManagers_v3(form) {
    form.querySelectorAll(
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, " +
      ".configured-field-header-picker-v1, .configured-field-header-picker-v2, .configured-field-header-picker-v3"
    ).forEach((element) => element.remove());

    form.querySelectorAll(
      '[data-process-field-header-picker="1"], [data-configured-field-header-picker="1"], ' +
      '[data-main-header-picker-v2="1"], [data-row-header-picker-v2="1"], ' +
      '[data-main-header-picker-v3="1"], [data-row-header-picker-v3="1"]'
    ).forEach((element) => {
      const wrapper =
        element.closest(".process-field-header-picker-v1") ||
        element.closest(".process-field-header-picker-v2") ||
        element.closest(".process-field-header-picker-v3") ||
        element.closest(".configured-field-header-picker-v1") ||
        element.closest(".configured-field-header-picker-v2") ||
        element.closest(".configured-field-header-picker-v3");

      if (wrapper) {
        wrapper.remove();
      }
    });
  }

  function getNameFieldWrapper_v3(nameSelect) {
    return (
      nameSelect.closest(".field") ||
      nameSelect.closest(".form-field") ||
      nameSelect.closest(".form-group") ||
      nameSelect.parentElement
    );
  }

  function ensureSideBySidePickers_v3(form, nameSelect, headerOptions) {
    let picker = form.querySelector('[data-main-header-picker-v3="1"]');

    if (picker) {
      return picker;
    }

    const nameWrapper = getNameFieldWrapper_v3(nameSelect);

    const row = document.createElement("div");
    row.className = "process-fields-picker-row-v3";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-field-header-picker-v3";

    const headerLabel = document.createElement("label");
    headerLabel.textContent = "CABEÇALHO DO CAMPO";

    picker = buildHeaderPicker_v3(headerOptions, "");
    picker.dataset.mainHeaderPickerV3 = "1";

    headerWrapper.appendChild(headerLabel);
    headerWrapper.appendChild(picker);

    if (nameWrapper && nameWrapper.parentElement) {
      nameWrapper.parentElement.insertBefore(row, nameWrapper);
      row.appendChild(nameWrapper);
      row.appendChild(headerWrapper);
    } else {
      form.insertBefore(row, nameSelect);
      row.appendChild(nameSelect);
      row.appendChild(headerWrapper);
    }

    return picker;
  }

  //###################################################################################
  // (6) CAMPOS CONFIGURADOS
  //###################################################################################

  function findConfiguredFieldControls_v3(form, nameSelect) {
    return Array.from(form.querySelectorAll('[name="visible_fields"]')).filter((control) => {
      return control !== nameSelect && !control.dataset.generatedHeaderV3;
    });
  }

  function getConfiguredRow_v3(control) {
    return (
      control.closest("tr") ||
      control.closest(".configured-field-row") ||
      control.closest(".settings-row") ||
      control.closest(".field-row") ||
      control.parentElement?.parentElement ||
      control.parentElement
    );
  }

  function getExistingHeaderValue_v3(form, row, rowIndex) {
    const picker = row?.querySelector('[data-row-header-picker-v3="1"]');

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

  function ensureHeaderColumn_v3(table) {
    const headerRow = table.querySelector("thead tr");

    if (!headerRow || headerRow.dataset.headerColumnV3 === "1") {
      return;
    }

    const th = document.createElement("th");
    th.textContent = "CABEÇALHO DO CAMPO";

    const actionHeader = Array.from(headerRow.children).find((cell) => {
      const text = normalizeText_v3(cell.textContent);
      return text.includes("acoes") || text.includes("ações");
    });

    if (actionHeader) {
      headerRow.insertBefore(th, actionHeader);
    } else {
      headerRow.appendChild(th);
    }

    headerRow.dataset.headerColumnV3 = "1";
  }

  function ensureConfiguredRowHeaderPicker_v3(form, row, rowIndex, headerOptions) {
    if (!row || row.querySelector('[data-row-header-picker-v3="1"]')) {
      return;
    }

    const selectedValue = getExistingHeaderValue_v3(form, row, rowIndex);
    const picker = buildHeaderPicker_v3(headerOptions, selectedValue);

    picker.name = "visible_headers";
    picker.dataset.rowHeaderPickerV3 = "1";

    const table = row.closest("table");

    if (table && row.tagName.toLowerCase() === "tr") {
      ensureHeaderColumn_v3(table);

      const td = document.createElement("td");
      td.appendChild(picker);

      const actionCell = Array.from(row.children).find((cell) => {
        const text = normalizeText_v3(cell.textContent);

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
    wrapper.className = "configured-field-header-picker-v3";

    const label = document.createElement("label");
    label.textContent = "Cabeçalho do campo";

    wrapper.appendChild(label);
    wrapper.appendChild(picker);

    row.appendChild(wrapper);
  }

  function ensureConfiguredRowsHeaderPickers_v3(form, nameSelect, headerOptions) {
    findConfiguredFieldControls_v3(form, nameSelect).forEach((control, rowIndex) => {
      const row = getConfiguredRow_v3(control);
      ensureConfiguredRowHeaderPicker_v3(form, row, rowIndex, headerOptions);
    });
  }

  //###################################################################################
  // (7) PREPARAR PAYLOAD PARA GRAVAR NO BD
  //###################################################################################

  function getConfiguredPayloadRows_v3(form, nameSelect) {
    const rows = [];

    findConfiguredFieldControls_v3(form, nameSelect).forEach((control, rowIndex) => {
      const fieldKey = String(control.value || "").trim().toLowerCase();

      if (!fieldKey) {
        return;
      }

      const row = getConfiguredRow_v3(control);
      const picker = row?.querySelector('[data-row-header-picker-v3="1"]');
      const headerKey = String(
        picker?.value ||
        getExistingHeaderValue_v3(form, row, rowIndex) ||
        ""
      ).trim().toLowerCase();

      rows.push({
        fieldKey,
        headerKey
      });
    });

    return rows;
  }

  function getSelectedPayloadRow_v3(nameSelect, mainHeaderPicker) {
    const selectedOption = nameSelect.selectedOptions[0];
    const fieldKey = String(nameSelect.value || "").trim().toLowerCase();

    if (!fieldKey || isHeaderOption_v3(selectedOption)) {
      return null;
    }

    return {
      fieldKey,
      headerKey: String(mainHeaderPicker?.value || "").trim().toLowerCase()
    };
  }

  function removeGeneratedInputs_v3(form) {
    form.querySelectorAll('[data-generated-header-v3="1"]').forEach((input) => {
      input.remove();
    });
  }

  function disableOriginalProcessInputs_v3(form, nameSelect) {
    Array.from(form.querySelectorAll('[name="visible_fields"], [name="visible_headers"]')).forEach((control) => {
      if (control.dataset.generatedHeaderV3 === "1") {
        return;
      }

      control.dataset.originalNameV3 = control.name;
      control.removeAttribute("name");
    });

    if (nameSelect && nameSelect.name) {
      nameSelect.dataset.originalNameV3 = nameSelect.name;
      nameSelect.removeAttribute("name");
    }
  }

  function appendPayloadInput_v3(form, name, value) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    input.dataset.generatedHeaderV3 = "1";
    form.appendChild(input);
  }

  function prepareFormSubmit_v3(form, nameSelect, mainHeaderPicker) {
    removeGeneratedInputs_v3(form);

    const payloadRows = getConfiguredPayloadRows_v3(form, nameSelect);
    const selectedRow = getSelectedPayloadRow_v3(nameSelect, mainHeaderPicker);

    if (selectedRow && !payloadRows.some((row) => row.fieldKey === selectedRow.fieldKey)) {
      payloadRows.push(selectedRow);
    }

    disableOriginalProcessInputs_v3(form, nameSelect);

    payloadRows.forEach((row) => {
      appendPayloadInput_v3(form, "visible_fields", row.fieldKey);
      appendPayloadInput_v3(form, "visible_headers", row.headerKey);
    });
  }

  //###################################################################################
  // (8) ESTILO LADO A LADO
  //###################################################################################

  function injectStyle_v3() {
    if (document.getElementById("process-fields-header-manager-v3-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-header-manager-v3-style";
    style.textContent = `
      .process-fields-picker-row-v3 {
        display: grid;
        grid-template-columns: minmax(260px, 1fr) minmax(260px, 360px);
        gap: 12px;
        align-items: end;
        width: 100%;
      }

      .process-fields-picker-row-v3 > * {
        min-width: 0;
      }

      .process-field-header-picker-v3,
      .configured-field-header-picker-v3 {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 0;
      }

      .process-field-header-picker-v3 label,
      .configured-field-header-picker-v3 label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-field-header-picker-v3 select,
      .configured-field-header-picker-v3 select,
      select[data-row-header-picker-v3="1"] {
        width: 100%;
        min-height: 38px;
      }

      @media (max-width: 780px) {
        .process-fields-picker-row-v3 {
          grid-template-columns: 1fr;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (9) INICIALIZAR
  //###################################################################################

  function initForm_v3(form) {
    if (form.dataset.processFieldsHeaderManagerV3 === "1") {
      return;
    }

    form.dataset.processFieldsHeaderManagerV3 = "1";

    const root = findCardRoot_v3(form);

    renameLabels_v3(root);
    removeOldHeaderManagers_v3(form);

    const nameSelect = findNameFieldSelect_v3(form);

    if (!nameSelect) {
      return;
    }

    const headerOptions = extractHeaderOptionsFromNameSelect_v3(nameSelect);

    removeHeaderOptionsFromNameSelect_v3(nameSelect);

    const mainHeaderPicker = ensureSideBySidePickers_v3(form, nameSelect, headerOptions);

    ensureConfiguredRowsHeaderPickers_v3(form, nameSelect, headerOptions);

    form.addEventListener(
      "submit",
      () => {
        prepareFormSubmit_v3(form, nameSelect, mainHeaderPicker);
      },
      true
    );
  }

  function initProcessFieldsHeaderManager_v3() {
    injectStyle_v3();

    findProcessFieldsForms_v3().forEach((form) => {
      initForm_v3(form);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProcessFieldsHeaderManager_v3);
  } else {
    initProcessFieldsHeaderManager_v3();
  }

  window.setTimeout(initProcessFieldsHeaderManager_v3, 300);
  window.setTimeout(initProcessFieldsHeaderManager_v3, 900);
})();
