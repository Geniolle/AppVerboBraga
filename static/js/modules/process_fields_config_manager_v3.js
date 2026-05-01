//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V3
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v3(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function escapeHtml_v3(value) {
    return toSafeString_v3(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeText_v3(value) {
    return toSafeString_v3(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizeKey_v3(value) {
    return normalizeText_v3(value);
  }

  function cleanHeaderLabel_v3(label) {
    return toSafeString_v3(label)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function isHeaderOption_v3(option) {
    if (!option || !toSafeString_v3(option.value).trim()) {
      return false;
    }

    const dataKind = normalizeText_v3(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const optionText = normalizeText_v3(option.textContent);
    const optionValue = normalizeText_v3(option.value);

    return (
      dataKind === "header" ||
      optionText.includes("cabecalho") ||
      optionValue.includes("cabecalho")
    );
  }

  function createOption_v3(value, label, selectedValue) {
    const option = document.createElement("option");
    option.value = value || "";
    option.textContent = label || "";

    if (toSafeString_v3(value) === toSafeString_v3(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  function createActionButton_v3(action, label, itemId, disabled) {
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
  // (2) ELEMENTOS DO FORMULARIO
  //###################################################################################

  function getElements_v3(form) {
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

  function validateElements_v3(elements) {
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
  // (3) OPCOES DISPONIVEIS
  //###################################################################################

  function getOriginalOptions_v3(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = toSafeString_v3(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key: key,
          label: cleanHeaderLabel_v3(
            toSafeString_v3(option.dataset.processConfigLabel || option.textContent).trim()
          ),
          kind: isHeaderOption_v3(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function getFieldOptions_v3(originalOptions) {
    return originalOptions.filter(function (item) {
      return item.kind !== "header";
    });
  }

  function getHeaderOptions_v3(originalOptions) {
    return originalOptions.filter(function (item) {
      return item.kind === "header";
    });
  }

  function findOptionByKey_v3(options, key) {
    const cleanKey = normalizeKey_v3(key);

    return options.find(function (item) {
      return normalizeKey_v3(item.key) === cleanKey;
    }) || null;
  }

  function getFieldLabel_v3(fieldOptions, fieldKey) {
    const option = findOptionByKey_v3(fieldOptions, fieldKey);
    return option ? option.label : fieldKey;
  }

  function getHeaderLabel_v3(headerOptions, headerKey) {
    const option = findOptionByKey_v3(headerOptions, headerKey);
    return option ? option.label : "";
  }

  //###################################################################################
  // (4) LER ITENS JA CONFIGURADOS
  //###################################################################################

  function readValueFromRow_v3(row, selector) {
    const input = row.querySelector(selector);
    return input ? toSafeString_v3(input.value).trim().toLowerCase() : "";
  }

  function readConfiguredItemsFromLegacyRows_v3(elements, fieldOptions, headerOptions) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = readValueFromRow_v3(row, "[data-process-config-key]");
      const label = readValueFromRow_v3(row, "[data-process-config-label]") || key;
      const kind = readValueFromRow_v3(row, "[data-process-config-kind]");

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
        label: getFieldLabel_v3(fieldOptions, key) || label,
        headerKey: currentHeaderKey,
        headerLabel: getHeaderLabel_v3(headerOptions, currentHeaderKey)
      });
    });

    return items;
  }

  function readConfiguredItemsFromHiddenInputs_v3(elements, fieldOptions, headerOptions) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_fields"]')
    );
    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll('input[name="visible_headers"]')
    );

    if (!fieldInputs.length) {
      return [];
    }

    return fieldInputs
      .map(function (input, index) {
        const key = toSafeString_v3(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = toSafeString_v3(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          managerId: "hidden_" + index + "_" + key,
          key: key,
          label: getFieldLabel_v3(fieldOptions, key),
          headerKey: headerKey,
          headerLabel: getHeaderLabel_v3(headerOptions, headerKey)
        };
      })
      .filter(Boolean);
  }

  function mergeConfiguredItems_v3(primaryItems, fallbackItems) {
    const merged = [];
    const seen = new Set();

    primaryItems.concat(fallbackItems).forEach(function (item) {
      const key = normalizeKey_v3(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  function readInitialItems_v3(elements, fieldOptions, headerOptions) {
    const fromHidden = readConfiguredItemsFromHiddenInputs_v3(
      elements,
      fieldOptions,
      headerOptions
    );
    const fromLegacy = readConfiguredItemsFromLegacyRows_v3(
      elements,
      fieldOptions,
      headerOptions
    );

    return mergeConfiguredItems_v3(fromHidden, fromLegacy);
  }

  //###################################################################################
  // (5) EDITOR
  //###################################################################################

  function rebuildEditorOptions_v3(elements, fieldOptions, state) {
    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizeKey_v3(item.key);
      })
    );

    const currentValue = normalizeKey_v3(elements.editorKey.value);

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(createOption_v3("", "Selecione", ""));

    fieldOptions.forEach(function (item) {
      if (configuredKeys.has(normalizeKey_v3(item.key)) && normalizeKey_v3(item.key) !== currentValue) {
        return;
      }

      const option = createOption_v3(item.key, item.label, currentValue);
      option.dataset.processConfigKind = "field";
      option.dataset.processConfigLabel = item.label;
      elements.editorKey.appendChild(option);
    });
  }

  function buildHeaderSelect_v3(headerOptions) {
    const select = document.createElement("select");
    select.dataset.processFieldsConfigHeaderEditorV3 = "1";
    select.appendChild(createOption_v3("", "Sem cabeçalho", ""));

    headerOptions.forEach(function (item) {
      const option = createOption_v3(item.key, item.label, "");
      option.dataset.processConfigKind = "header";
      option.dataset.processConfigLabel = item.label;
      select.appendChild(option);
    });

    return select;
  }

  function ensureHeaderEditor_v3(form, elements, headerOptions) {
    const existing = form.querySelector("[data-process-fields-config-header-editor-v3='1']");

    if (existing) {
      return existing;
    }

    const editorWrapper =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    const row = document.createElement("div");
    row.className = "process-fields-config-editor-row-v3";

    const headerWrapper = document.createElement("div");
    headerWrapper.className = "process-fields-config-header-editor-v3";

    const label = document.createElement("label");
    label.textContent = "CABEÇALHO DO CAMPO";

    const select = buildHeaderSelect_v3(headerOptions);

    headerWrapper.appendChild(label);
    headerWrapper.appendChild(select);

    if (editorWrapper && editorWrapper.parentElement) {
      editorWrapper.parentElement.insertBefore(row, editorWrapper);
      row.appendChild(editorWrapper);
      row.appendChild(headerWrapper);
    }

    return select;
  }

  function renameEditorLabel_v3(form) {
    Array.from(form.querySelectorAll("label, th")).forEach(function (element) {
      const text = normalizeText_v3(element.textContent);

      if (text === "campo do processo") {
        element.textContent = "NOME DO CAMPO";
      }
    });
  }

  function clearEditor_v3(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";

    if (state.headerSelect) {
      state.headerSelect.value = "";
    }

    rebuildEditorOptions_v3(elements, state.fieldOptions, state);
  }

  function readDraftItem_v3(state, elements) {
    const option = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!option || !option.value) {
      return null;
    }

    const key = toSafeString_v3(option.value).trim().toLowerCase();
    const headerKey = toSafeString_v3(state.headerSelect ? state.headerSelect.value : "")
      .trim()
      .toLowerCase();

    return {
      managerId: state.editingId || "new_" + Date.now() + "_" + key,
      key: key,
      label: toSafeString_v3(option.dataset.processConfigLabel || option.textContent).trim(),
      headerKey: headerKey,
      headerLabel: getHeaderLabel_v3(state.headerOptions, headerKey)
    };
  }

  function hasDraft_v3(state, elements) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  function validateDraft_v3(state, item) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId &&
        normalizeKey_v3(existing.key) === normalizeKey_v3(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function addOrUpdateDraft_v3(state, elements) {
    const item = readDraftItem_v3(state, elements);

    if (!validateDraft_v3(state, item)) {
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

    clearEditor_v3(state, elements);
    return true;
  }

  function loadEditor_v3(state, elements, item) {
    state.editingId = item.managerId;
    rebuildEditorOptions_v3(elements, state.fieldOptions, state);
    elements.editorKey.value = item.key || "";

    if (state.headerSelect) {
      state.headerSelect.value = item.headerKey || "";
    }

    elements.editorKey.focus();
  }

  //###################################################################################
  // (6) HIDDEN INPUTS PARA O BACKEND
  //###################################################################################

  function syncHiddenInputs_v3(state, elements) {
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

  function submitNative_v3(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (7) TABELA
  //###################################################################################

  function rewriteTableHead_v3(elements) {
    const headRow = elements.table.querySelector("thead tr");

    if (!headRow || headRow.dataset.processFieldsConfigHeaderV3 === "1") {
      return;
    }

    headRow.innerHTML = [
      "<th>NOME DO CAMPO</th>",
      "<th>CABEÇALHO DO CAMPO</th>",
      "<th>AÇÕES</th>"
    ].join("");

    headRow.dataset.processFieldsConfigHeaderV3 = "1";
  }

  function renderTable_v3(state, elements) {
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
        "<td>" + escapeHtml_v3(item.label || item.key) + "</td>",
        "<td>" + escapeHtml_v3(item.headerLabel || "Sem cabeçalho") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createActionButton_v3("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createActionButton_v3("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createActionButton_v3("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(createActionButton_v3("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderPagination_v3(state, elements, totalPages);
    syncHiddenInputs_v3(state, elements);
    rebuildEditorOptions_v3(elements, state.fieldOptions, state);
  }

  function renderPagination_v3(state, elements, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderTable_v3(state, elements);
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
        renderTable_v3(state, elements);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  //###################################################################################
  // (8) ACOES
  //###################################################################################

  function findItemIndex_v3(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moveItem_v3(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function bindEvents_v3(form, state, elements) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v3(state, elements)) {
        const ok = addOrUpdateDraft_v3(state, elements);

        if (!ok) {
          return;
        }
      }

      renderTable_v3(state, elements);
      syncHiddenInputs_v3(state, elements);
      submitNative_v3(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      clearEditor_v3(state, elements);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderTable_v3(state, elements);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = findItemIndex_v3(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        loadEditor_v3(state, elements, state.items[index]);
        return;
      }

      if (action === "up") {
        moveItem_v3(state, index, index - 1);
      }

      if (action === "down") {
        moveItem_v3(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderTable_v3(state, elements);
    });

    form.addEventListener("submit", function () {
      syncHiddenInputs_v3(state, elements);
    });
  }

  //###################################################################################
  // (9) ESTILO
  //###################################################################################

  function injectStyle_v3() {
    if (document.getElementById("process-fields-config-manager-v3-style")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "process-fields-config-manager-v3-style";
    style.textContent = `
      .process-fields-config-editor-row-v3 {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: 12px;
        align-items: end;
        width: 100%;
      }

      .process-fields-config-editor-row-v3 > * {
        min-width: 0;
        width: 100%;
      }

      .process-fields-config-editor-row-v3 .field,
      .process-fields-config-header-editor-v3 {
        display: flex;
        flex-direction: column;
        gap: 6px;
        width: 100%;
        min-width: 0;
        margin: 0;
      }

      .process-fields-config-editor-row-v3 label,
      .process-fields-config-header-editor-v3 label {
        min-height: 14px;
        line-height: 14px;
        margin: 0;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .process-fields-config-editor-row-v3 select,
      .process-fields-config-header-editor-v3 select {
        width: 100%;
        min-width: 0;
        max-width: 100%;
        height: 38px;
        min-height: 38px;
        box-sizing: border-box;
      }

      @media (max-width: 900px) {
        .process-fields-config-editor-row-v3 {
          grid-template-columns: 1fr;
        }
      }
    `;

    document.head.appendChild(style);
  }

  //###################################################################################
  // (10) INICIALIZACAO
  //###################################################################################

  function setupProcessFieldsConfigManager_v3(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV3 === "1") {
      return;
    }

    const elements = getElements_v3(form);

    if (!validateElements_v3(elements)) {
      return;
    }

    form.dataset.processFieldsConfigManagerBoundV3 = "1";

    injectStyle_v3();
    renameEditorLabel_v3(form);

    const originalOptions = getOriginalOptions_v3(elements);
    const fieldOptions = getFieldOptions_v3(originalOptions);
    const headerOptions = getHeaderOptions_v3(originalOptions);
    const headerSelect = ensureHeaderEditor_v3(form, elements, headerOptions);

    const state = {
      items: [],
      fieldOptions: fieldOptions,
      headerOptions: headerOptions,
      headerSelect: headerSelect,
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    state.items = readInitialItems_v3(elements, fieldOptions, headerOptions);

    rewriteTableHead_v3(elements);
    bindEvents_v3(form, state, elements);
    renderTable_v3(state, elements);
  }

  function setupAllProcessFieldsConfigManagers_v3() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(setupProcessFieldsConfigManager_v3);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessFieldsConfigManagers_v3);
  } else {
    setupAllProcessFieldsConfigManagers_v3();
  }

  window.setTimeout(setupAllProcessFieldsConfigManagers_v3, 150);
  window.setTimeout(setupAllProcessFieldsConfigManagers_v3, 600);
})();
