//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V4
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function safeText_v4(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeText_v4(value) {
    return safeText_v4(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v4(value) {
    return normalizeText_v4(value);
  }

  function escapeHtml_v4(value) {
    return safeText_v4(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isHeaderOption_v4(option) {
    if (!option || !safeText_v4(option.value).trim()) {
      return false;
    }

    const kind = normalizeText_v4(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v4(option.textContent);
    const optionValue = normalizeText_v4(option.value);

    return (
      kind === "header" ||
      optionText.includes("cabecalho") ||
      optionValue.includes("cabecalho")
    );
  }

  function cleanHeaderLabel_v4(value) {
    return safeText_v4(value)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function createOption_v4(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value || "";
    option.textContent = label || "";

    if (safeText_v4(value) === safeText_v4(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  function createActionButton_v4(action, label, itemId, disabled) {
    const button = document.createElement("button");
    const icons = {
      edit: "&#9998;",
      up: "&#8593;",
      down: "&#8595;",
      remove: "&#128465;"
    };

    button.type = "button";
    button.className = "configurable-items-action-btn-v1";
    button.dataset.processFieldsConfigAction = action;
    button.dataset.processFieldsConfigItemId = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.innerHTML = icons[action] || label;

    if (disabled) {
      button.disabled = true;
    }

    return button;
  }

  //###################################################################################
  // (2) LOCALIZAR ELEMENTOS
  //###################################################################################

  function getElements_v4(form) {
    return {
      legacyContainer: form.querySelector("[data-process-fields-config-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-fields-config-hidden-container]"),
      editorKey: form.querySelector("[data-process-fields-config-editor-key]"),
      submitButton: form.querySelector("[data-process-fields-config-submit]"),
      cancelButton: form.querySelector("[data-process-fields-config-cancel]"),
      table: form.querySelector("[data-process-fields-config-table]"),
      tableBody: form.querySelector("[data-process-fields-config-table-body]"),
      emptyState: form.querySelector("[data-process-fields-config-empty]"),
      totalLabel: form.querySelector("[data-process-fields-config-total-label]"),
      pageSize: form.querySelector("[data-process-fields-config-page-size]"),
      pagination: form.querySelector("[data-process-fields-config-pagination]")
    };
  }

  function hasRequiredElements_v4(elements) {
    return Boolean(
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.submitButton &&
      elements.cancelButton &&
      elements.table &&
      elements.tableBody &&
      elements.emptyState &&
      elements.totalLabel &&
      elements.pageSize &&
      elements.pagination
    );
  }

  //###################################################################################
  // (3) LIMPAR DUPLICADOS DE TENTATIVAS ANTERIORES
  //###################################################################################

  function cleanupOldManagers_v4(form, elements) {
    form.querySelectorAll(
      ".process-fields-picker-row-v1, .process-fields-picker-row-v2, .process-fields-picker-row-v3, .process-fields-picker-row-v4, .process-fields-picker-row-v5, .process-fields-picker-row-v6, " +
      ".process-fields-config-editor-row-v2, .process-fields-config-editor-row-v3, .process-fields-config-editor-row-v4, " +
      ".process-field-header-picker-v1, .process-field-header-picker-v2, .process-field-header-picker-v3, .process-field-header-picker-v4, .process-field-header-picker-v5, .process-field-header-picker-v6, " +
      ".process-fields-config-header-editor-v2, .process-fields-config-header-editor-v3, .process-fields-config-header-editor-v4"
    ).forEach(function (element) {
      if (element.contains(elements.editorKey)) {
        const editorField =
          elements.editorKey.closest(".field") ||
          elements.editorKey.closest(".form-field") ||
          elements.editorKey.parentElement;

        if (editorField && element.parentElement) {
          element.parentElement.insertBefore(editorField, element);
        }
      }

      element.remove();
    });

    form.querySelectorAll(
      "[data-process-field-header-picker], " +
      "[data-configured-field-header-picker], " +
      "[data-main-header-picker-v2], " +
      "[data-main-header-picker-v3], " +
      "[data-main-header-select-v4], " +
      "[data-main-header-select-v5], " +
      "[data-main-header-select-v6], " +
      "[data-process-fields-config-header-editor-v2], " +
      "[data-process-fields-config-header-editor-v3]"
    ).forEach(function (element) {
      if (element !== elements.editorKey) {
        const wrapper =
          element.closest(".process-field-header-picker-v1") ||
          element.closest(".process-field-header-picker-v2") ||
          element.closest(".process-field-header-picker-v3") ||
          element.closest(".process-field-header-picker-v4") ||
          element.closest(".process-field-header-picker-v5") ||
          element.closest(".process-field-header-picker-v6") ||
          element.closest(".process-fields-config-header-editor-v2") ||
          element.closest(".process-fields-config-header-editor-v3") ||
          element;

        wrapper.remove();
      }
    });
  }

  //###################################################################################
  // (4) OPCOES DO SELECT
  //###################################################################################

  function readOriginalOptions_v4(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = safeText_v4(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key: key,
          label: cleanHeaderLabel_v4(
            safeText_v4(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: isHeaderOption_v4(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function getFieldOptions_v4(options) {
    return options.filter(function (item) {
      return item.kind !== "header";
    });
  }

  function getHeaderOptions_v4(options) {
    return options.filter(function (item) {
      return item.kind === "header";
    });
  }

  function findByKey_v4(options, key) {
    const cleanKey = normalizeKey_v4(key);

    return options.find(function (item) {
      return normalizeKey_v4(item.key) === cleanKey;
    }) || null;
  }

  function getFieldLabel_v4(state, fieldKey) {
    const option = findByKey_v4(state.fieldOptions, fieldKey);
    return option ? option.label : fieldKey;
  }

  function getHeaderLabel_v4(state, headerKey) {
    const option = findByKey_v4(state.headerOptions, headerKey);
    return option ? option.label : "";
  }

  //###################################################################################
  // (5) LER CAMPOS CONFIGURADOS DO HTML
  //###################################################################################

  function readInputValue_v4(row, selector) {
    const input = row.querySelector(selector);
    return input ? safeText_v4(input.value).trim().toLowerCase() : "";
  }

  function readInitialItemsFromLegacy_v4(elements, state) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = readInputValue_v4(row, "[data-process-config-key]");
      const kind = readInputValue_v4(row, "[data-process-config-kind]");

      if (!key) {
        return;
      }

      if (kind === "header") {
        currentHeaderKey = key;
        return;
      }

      items.push({
        managerId: "legacy_" + index + "_" + key,
        key: key,
        label: getFieldLabel_v4(state, key),
        headerKey: currentHeaderKey,
        headerLabel: getHeaderLabel_v4(state, currentHeaderKey)
      });
    });

    return items;
  }

  function readInitialItemsFromHidden_v4(elements, state) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_fields"]')
    );
    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_headers"]')
    );

    return fieldInputs
      .map(function (input, index) {
        const key = safeText_v4(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = safeText_v4(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          managerId: "hidden_" + index + "_" + key,
          key: key,
          label: getFieldLabel_v4(state, key),
          headerKey: headerKey,
          headerLabel: getHeaderLabel_v4(state, headerKey)
        };
      })
      .filter(Boolean);
  }

  function mergeInitialItems_v4(first, second) {
    const merged = [];
    const seen = new Set();

    first.concat(second).forEach(function (item) {
      const key = normalizeKey_v4(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  //###################################################################################
  // (6) EDITOR
  //###################################################################################

  function renameLabels_v4(form) {
    Array.from(form.querySelectorAll("label, th")).forEach(function (element) {
      const text = normalizeText_v4(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  function rebuildFieldSelect_v4(elements, state) {
    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizeKey_v4(item.key);
      })
    );

    const currentValue = normalizeKey_v4(elements.editorKey.value);

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(createOption_v4("", "Selecione", ""));

    state.fieldOptions.forEach(function (item) {
      const itemKey = normalizeKey_v4(item.key);

      if (configuredKeys.has(itemKey) && itemKey !== currentValue) {
        return;
      }

      const option = createOption_v4(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "field";
      option.dataset.processConfigLabel = item.label;
      elements.editorKey.appendChild(option);
    });
  }

  function buildHeaderSelect_v4(state) {
    const select = document.createElement("select");
    select.dataset.processFieldsConfigHeaderEditorV4 = "1";

    select.appendChild(createOption_v4("", "Sem cabeçalho", ""));

    state.headerOptions.forEach(function (item) {
      const option = createOption_v4(item.key, item.label, "");
      option.dataset.processConfigKind = "header";
      option.dataset.processConfigLabel = item.label;
      select.appendChild(option);
    });

    return select;
  }

  function ensureHeaderEditor_v4(form, elements, state) {
    const existing = form.querySelector("[data-process-fields-config-header-editor-v4='1']");

    if (existing) {
      return existing;
    }

    const editorWrapper =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v4";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-fields-config-header-editor-v4";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const select = buildHeaderSelect_v4(state);

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(select);

    if (editorWrapper && editorWrapper.parentElement) {
      editorWrapper.parentElement.insertBefore(row, editorWrapper);
      row.appendChild(editorWrapper);
      row.appendChild(headerWrapper);
    }

    return select;
  }

  function clearEditor_v4(elements, state) {
    state.editingId = "";
    elements.editorKey.value = "";

    if (state.headerSelect) {
      state.headerSelect.value = "";
    }

    rebuildFieldSelect_v4(elements, state);
  }

  function readDraft_v4(elements, state) {
    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!selectedOption || !selectedOption.value) {
      return null;
    }

    const key = safeText_v4(selectedOption.value).trim().toLowerCase();
    const headerKey = safeText_v4(state.headerSelect ? state.headerSelect.value : "")
      .trim()
      .toLowerCase();

    return {
      managerId: state.editingId || "item_" + Date.now() + "_" + key,
      key: key,
      label: safeText_v4(selectedOption.dataset.processConfigLabel || selectedOption.textContent),
      headerKey: headerKey,
      headerLabel: getHeaderLabel_v4(state, headerKey)
    };
  }

  function validateDraft_v4(state, item) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId &&
        normalizeKey_v4(existing.key) === normalizeKey_v4(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function addOrUpdateDraft_v4(elements, state) {
    const item = readDraft_v4(elements, state);

    if (!validateDraft_v4(state, item)) {
      return false;
    }

    const index = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (index >= 0) {
      state.items[index] = item;
    } else {
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v4(elements, state);
    return true;
  }

  function hasDraft_v4(elements, state) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  function loadEditor_v4(elements, state, item) {
    state.editingId = item.managerId;
    rebuildFieldSelect_v4(elements, state);

    elements.editorKey.value = item.key || "";

    if (state.headerSelect) {
      state.headerSelect.value = item.headerKey || "";
    }

    elements.editorKey.focus();
  }

  //###################################################################################
  // (7) HIDDEN INPUTS PARA GRAVAR NO BD
  //###################################################################################

  function syncHiddenInputs_v4(elements, state) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fieldInput = document.createElement("input");
      fieldInput.type = "hidden";
      fieldInput.name = "visible_fields";
      fieldInput.value = item.key || "";
      elements.hiddenContainer.appendChild(fieldInput);

      const headerInput = document.createElement("input");
      headerInput.type = "hidden";
      headerInput.name = "visible_headers";
      headerInput.value = item.headerKey || "";
      elements.hiddenContainer.appendChild(headerInput);
    });
  }

  function nativeSubmit_v4(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (8) TABELA
  //###################################################################################

  function rewriteTableHeader_v4(elements) {
    const headRow = elements.table.querySelector("thead tr");

    if (!headRow || headRow.dataset.processFieldsConfigHeaderV4 === "1") {
      return;
    }

    headRow.innerHTML = [
      "<th>NOME DO CAMPO</th>",
      "<th>CABEÇALHO DO CAMPO</th>",
      "<th>AÇÕES</th>"
    ].join("");

    headRow.dataset.processFieldsConfigHeaderV4 = "1";
  }

  function renderPagination_v4(elements, state, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderTable_v4(elements, state);
      }
    });

    const pageLabel = document.createElement("span");
    pageLabel.className = "table-limiter-page";
    pageLabel.textContent = String(state.page);

    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.className = "table-limiter-nav-btn";
    nextButton.innerHTML = "&#8250;";
    nextButton.disabled = state.page >= totalPages;
    nextButton.addEventListener("click", function () {
      if (state.page < totalPages) {
        state.page += 1;
        renderTable_v4(elements, state);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  function renderTable_v4(elements, state) {
    const totalItems = state.items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / state.pageSize));

    if (state.page > totalPages) {
      state.page = totalPages;
    }

    const start = (state.page - 1) * state.pageSize;
    const visibleItems = state.items.slice(start, start + state.pageSize);

    elements.tableBody.innerHTML = "";

    visibleItems.forEach(function (item, visibleIndex) {
      const absoluteIndex = start + visibleIndex;
      const row = document.createElement("tr");

      row.dataset.processFieldsConfigItemId = item.managerId;
      row.innerHTML = [
        "<td>" + escapeHtml_v4(item.label || item.key) + "</td>",
        "<td>" + escapeHtml_v4(item.headerLabel || "Sem cabeçalho") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createActionButton_v4("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createActionButton_v4("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createActionButton_v4("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(createActionButton_v4("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderPagination_v4(elements, state, totalPages);
    syncHiddenInputs_v4(elements, state);
    rebuildFieldSelect_v4(elements, state);
  }

  //###################################################################################
  // (9) EVENTOS
  //###################################################################################

  function findItemIndex_v4(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moveItem_v4(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function bindEvents_v4(form, elements, state) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v4(elements, state)) {
        const ok = addOrUpdateDraft_v4(elements, state);

        if (!ok) {
          return;
        }
      }

      renderTable_v4(elements, state);
      syncHiddenInputs_v4(elements, state);
      nativeSubmit_v4(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      clearEditor_v4(elements, state);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderTable_v4(elements, state);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = findItemIndex_v4(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        loadEditor_v4(elements, state, state.items[index]);
        return;
      }

      if (action === "up") {
        moveItem_v4(state, index, index - 1);
      }

      if (action === "down") {
        moveItem_v4(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderTable_v4(elements, state);
    });

    form.addEventListener("submit", function () {
      syncHiddenInputs_v4(elements, state);
    });
  }

  //###################################################################################
  // (10) ESTILO
  //###################################################################################

  function injectStyle_v4() {
    if (document.getElementById("process-fields-config-manager-v4-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-config-manager-v4-style";
    style.textContent = `
      .process-fields-config-editor-row-v4 {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
        gap: 12px !important;
        align-items: end !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v4 > * {
        min-width: 0 !important;
        width: 100% !important;
      }

      .process-fields-config-editor-row-v4 .field,
      .process-fields-config-header-editor-v4 {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }

      .process-fields-config-editor-row-v4 label,
      .process-fields-config-header-editor-v4 label {
        min-height: 14px !important;
        line-height: 14px !important;
        margin: 0 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
      }

      .process-fields-config-editor-row-v4 select,
      .process-fields-config-header-editor-v4 select {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 38px !important;
        min-height: 38px !important;
        box-sizing: border-box !important;
      }

      @media (max-width: 900px) {
        .process-fields-config-editor-row-v4 {
          grid-template-columns: 1fr !important;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (11) INICIALIZAR
  //###################################################################################

  function setupProcessFieldsConfigManager_v4(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV4 === "1") {
      return;
    }

    const elements = getElements_v4(form);

    if (!hasRequiredElements_v4(elements)) {
      return;
    }

    form.dataset.processFieldsConfigManagerBoundV4 = "1";

    injectStyle_v4();
    cleanupOldManagers_v4(form, elements);
    renameLabels_v4(form);

    const originalOptions = readOriginalOptions_v4(elements);

    const state = {
      fieldOptions: getFieldOptions_v4(originalOptions),
      headerOptions: getHeaderOptions_v4(originalOptions),
      headerSelect: null,
      items: [],
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    state.headerSelect = ensureHeaderEditor_v4(form, elements, state);
    state.items = mergeInitialItems_v4(
      readInitialItemsFromHidden_v4(elements, state),
      readInitialItemsFromLegacy_v4(elements, state)
    );

    rewriteTableHeader_v4(elements);
    bindEvents_v4(form, elements, state);
    renderTable_v4(elements, state);
  }

  function setupAllProcessFieldsConfigManagers_v4() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(setupProcessFieldsConfigManager_v4);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessFieldsConfigManagers_v4);
  } else {
    setupAllProcessFieldsConfigManagers_v4();
  }

  window.setTimeout(setupAllProcessFieldsConfigManagers_v4, 150);
  window.setTimeout(setupAllProcessFieldsConfigManagers_v4, 600);
})();
