//###################################################################################
// (1) PROCESS FIELDS BUILDER V1
//###################################################################################
(function registerProcessFieldsBuilderV1() {
  "use strict";

  function setupProcessFieldsBuilder() {
    const processFieldsBuilderEl = document.getElementById("process-fields-builder");
    if (!processFieldsBuilderEl) {
      return;
    }
    const optionsRaw = processFieldsBuilderEl.getAttribute("data-field-options") || "[]";
    const headerOptionsRaw = processFieldsBuilderEl.getAttribute("data-header-options") || "[]";
    let fieldOptions = [];
    let headerOptions = [];
    try {
      fieldOptions = JSON.parse(optionsRaw);
    } catch (_error) {
      fieldOptions = [];
    }
    try {
      headerOptions = JSON.parse(headerOptionsRaw);
    } catch (_error) {
      headerOptions = [];
    }
    if (!Array.isArray(fieldOptions) || !fieldOptions.length) {
      return;
    }
    if (!Array.isArray(headerOptions)) {
      headerOptions = [];
    }

    const containerEl = document.getElementById("process-visible-fields-container");
    const addButtonEl = document.getElementById("process-field-add-btn");
    const formEl = processFieldsBuilderEl.closest("form");
    if (!containerEl || !addButtonEl || !formEl) {
      return;
    }

    function renderFieldOptions(selectedKey) {
      return fieldOptions
        .map((option) => {
          const optionKey = String(option.key || "");
          const optionLabel = String(option.label || optionKey);
          const isSelected = optionKey === String(selectedKey || "");
          return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
        })
        .join("");
    }

    function renderHeaderOptions(selectedKey) {
      const cleanSelectedKey = String(selectedKey || "").trim();
      const optionsHtml = headerOptions
        .map((option) => {
          const optionKey = String(option.key || "");
          const optionLabel = String(option.label || optionKey);
          const isSelected = optionKey === cleanSelectedKey;
          return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
        })
        .join("");
      return `<option value="">Sem cabeçalho</option>${optionsHtml}`;
    }

    function updateRemoveButtonsState() {
      const removeButtons = containerEl.querySelectorAll(".process-field-remove-btn");
      const isSingleRow = removeButtons.length <= 1;
      removeButtons.forEach((button) => {
        button.disabled = isSingleRow;
        button.classList.toggle("table-icon-btn-disabled", isSingleRow);
        button.setAttribute(
          "title",
          isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
        );
        button.setAttribute(
          "aria-label",
          isSingleRow ? "É necessário manter pelo menos um campo" : "Remover campo"
        );
      });
    }

    function bindRemoveButton(buttonEl) {
      buttonEl.addEventListener("click", () => {
        const rows = containerEl.querySelectorAll(".process-field-row");
        if (rows.length <= 1) {
          updateRemoveButtonsState();
          return;
        }
        const rowEl = buttonEl.closest(".process-field-row");
        if (rowEl) {
          rowEl.remove();
        }
        updateRemoveButtonsState();
      });
    }

    function createFieldRow(selectedKey, selectedHeaderKey) {
      const rowEl = document.createElement("div");
      rowEl.className = "process-field-row";
      rowEl.innerHTML = `
      <div class="field">
        <label>Campo</label>
        <select name="visible_fields" class="process-field-select">
          ${renderFieldOptions(selectedKey || fieldOptions[0].key)}
        </select>
      </div>
      <div class="field">
        <label>Cabeçalho</label>
        <select name="visible_headers" class="process-field-header-select">
          ${renderHeaderOptions(selectedHeaderKey || "")}
        </select>
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-field-remove-btn"
        title="Remover campo"
        aria-label="Remover campo"
      >
        &#10005;
      </button>
    `;
      const removeButtonEl = rowEl.querySelector(".process-field-remove-btn");
      if (removeButtonEl) {
        bindRemoveButton(removeButtonEl);
      }
      return rowEl;
    }

    containerEl.querySelectorAll(".process-field-remove-btn").forEach((buttonEl) => {
      bindRemoveButton(buttonEl);
    });

    addButtonEl.addEventListener("click", () => {
      containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
      updateRemoveButtonsState();
    });

    formEl.addEventListener("submit", () => {
      const seenFieldKeys = new Set();
      const selects = containerEl.querySelectorAll("select[name='visible_fields']");
      selects.forEach((selectEl) => {
        const cleanValue = String(selectEl.value || "").trim();
        if (!cleanValue || seenFieldKeys.has(cleanValue)) {
          selectEl.removeAttribute("name");
          const rowEl = selectEl.closest(".process-field-row");
          if (rowEl) {
            const headerSelectEl = rowEl.querySelector("select[name='visible_headers']");
            if (headerSelectEl) {
              headerSelectEl.removeAttribute("name");
            }
          }
          return;
        }
        seenFieldKeys.add(cleanValue);
      });
    });

    if (!containerEl.querySelector(".process-field-row")) {
      containerEl.appendChild(createFieldRow(fieldOptions[0].key, ""));
    }
    if (fieldOptions.length <= 1) {
      addButtonEl.disabled = true;
      addButtonEl.classList.add("table-icon-btn-disabled");
      addButtonEl.setAttribute("title", "Não há mais campos para adicionar");
      addButtonEl.setAttribute("aria-label", "Não há mais campos para adicionar");
    }
    updateRemoveButtonsState();
  }

  window.APPVERBO_SETUP_PROCESS_FIELDS_BUILDER_V1 = setupProcessFieldsBuilder;
})();
