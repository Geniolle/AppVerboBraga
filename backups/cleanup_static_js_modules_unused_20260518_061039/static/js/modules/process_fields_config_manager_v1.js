//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function escapeHtml_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeKey_v1(value) {
    return toSafeString_v1(value).trim().toLowerCase();
  }

  function getKindLabel_v1(kind) {
    return kind === "header" ? "Cabeçalho" : "Campo";
  }

  function createButton_v1(action, label, itemId, disabled) {
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
  // (2) LEITURA DO DOM
  //###################################################################################

  function getElements_v1(form) {
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

  function readHiddenValue_v1(row, selector) {
    const input = row.querySelector(selector);
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(elements.legacyContainer.querySelectorAll("[data-process-config-field-row]"));

    return rows
      .map(function (row, index) {
        const key = readHiddenValue_v1(row, "[data-process-config-key]");
        const label = readHiddenValue_v1(row, "[data-process-config-label]") || key;
        const kind = readHiddenValue_v1(row, "[data-process-config-kind]") === "header" ? "header" : "field";

        return {
          managerId: "config_" + index + "_" + key,
          key: key,
          label: label,
          kind: kind
        };
      })
      .filter(function (item) {
        return item.key;
      });
  }

  function readOptionItem_v1(elements) {
    const option = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!option || !option.value) {
      return null;
    }

    return {
      managerId: "tmp_" + Date.now() + "_" + option.value,
      key: toSafeString_v1(option.value).trim(),
      label: toSafeString_v1(option.dataset.processConfigLabel || option.textContent).replace(" - Cabeçalho", "").trim(),
      kind: option.dataset.processConfigKind === "header" ? "header" : "field"
    };
  }

  //###################################################################################
  // (3) SINCRONIZACAO COM BACKEND
  //###################################################################################

  function syncHiddenInputs_v1(state, elements) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = item.kind === "header" ? "visible_headers" : "visible_fields";
      input.value = item.key || "";
      elements.hiddenContainer.appendChild(input);
    });
  }

  //###################################################################################
  // (4) EDITOR SUPERIOR
  //###################################################################################

  function clearEditor_v1(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";
  }

  function loadEditor_v1(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";
    elements.editorKey.focus();
  }

  function validateItem_v1(item, state) {
    if (!item || !item.key) {
      window.alert("Selecione um campo.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && normalizeKey_v1(existing.key) === normalizeKey_v1(item.key);
    });

    if (duplicate) {
      window.alert("Este campo já está configurado.");
      return false;
    }

    return true;
  }

  function addOrUpdateFromEditor_v1(state, elements) {
    const item = readOptionItem_v1(elements);

    if (!item) {
      return false;
    }

    if (state.editingId) {
      item.managerId = state.editingId;
    }

    if (!validateItem_v1(item, state)) {
      return false;
    }

    const index = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (index >= 0) {
      state.items[index] = item;
    } else {
      item.managerId = "tmp_" + Date.now() + "_" + item.key;
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v1(state, elements);
    return true;
  }

  function hasDraft_v1(elements, state) {
    return Boolean(state.editingId || elements.editorKey.value);
  }

  //###################################################################################
  // (5) TABELA E PAGINACAO
  //###################################################################################

  function renderTable_v1(state, elements) {
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
        "<td>" + escapeHtml_v1(item.label || item.key) + "</td>",
        "<td>" + escapeHtml_v1(getKindLabel_v1(item.kind)) + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createButton_v1("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createButton_v1("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createButton_v1("down", "Descer", item.managerId, absoluteIndex === totalItems - 1));
      actionsWrap.appendChild(createButton_v1("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "campo" : "campos");

    renderPagination_v1(state, elements, totalPages);
  }

  function renderPagination_v1(state, elements, totalPages) {
    elements.pagination.innerHTML = "";

    const previousButton = document.createElement("button");
    previousButton.type = "button";
    previousButton.className = "table-limiter-nav-btn";
    previousButton.innerHTML = "&#8249;";
    previousButton.disabled = state.page <= 1;
    previousButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        renderTable_v1(state, elements);
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
        renderTable_v1(state, elements);
      }
    });

    elements.pagination.appendChild(previousButton);
    elements.pagination.appendChild(pageLabel);
    elements.pagination.appendChild(nextButton);
  }

  //###################################################################################
  // (6) ACOES
  //###################################################################################

  function findItemIndex_v1(state, itemId) {
    return state.items.findIndex(function (item) {
      return item.managerId === itemId;
    });
  }

  function moveItem_v1(state, fromIndex, toIndex) {
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= state.items.length || toIndex >= state.items.length) {
      return;
    }

    const item = state.items.splice(fromIndex, 1)[0];
    state.items.splice(toIndex, 0, item);
  }

  function bindEvents_v1(form, state, elements) {
    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v1(elements, state)) {
        const ok = addOrUpdateFromEditor_v1(state, elements);

        if (!ok) {
          return;
        }
      }

      syncHiddenInputs_v1(state, elements);

      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
        return;
      }

      form.submit();
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      clearEditor_v1(state, elements);
    });

    elements.pageSize.addEventListener("change", function () {
      state.pageSize = Number.parseInt(elements.pageSize.value, 10) || 5;
      state.page = 1;
      renderTable_v1(state, elements);
    });

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-fields-config-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processFieldsConfigAction;
      const itemId = button.dataset.processFieldsConfigItemId;
      const index = findItemIndex_v1(state, itemId);

      if (index < 0) {
        return;
      }

      if (action === "edit") {
        loadEditor_v1(state.items[index], state, elements);
        return;
      }

      if (action === "up") {
        moveItem_v1(state, index, index - 1);
      }

      if (action === "down") {
        moveItem_v1(state, index, index + 1);
      }

      if (action === "remove") {
        state.items.splice(index, 1);
      }

      renderTable_v1(state, elements);
      syncHiddenInputs_v1(state, elements);
    });

    form.addEventListener("submit", function () {
      syncHiddenInputs_v1(state, elements);
    });
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function setupProcessFieldsConfigManager_v1(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV1 === "1") {
      return;
    }

    const elements = getElements_v1(form);

    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
      !elements.submitButton ||
      !elements.cancelButton ||
      !elements.table ||
      !elements.tableBody ||
      !elements.emptyState ||
      !elements.totalLabel ||
      !elements.pageSize ||
      !elements.pagination
    ) {
      return;
    }

    const state = {
      items: readInitialItems_v1(elements),
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    form.dataset.processFieldsConfigManagerBoundV1 = "1";

    bindEvents_v1(form, state, elements);
    syncHiddenInputs_v1(state, elements);
    renderTable_v1(state, elements);
  }

  function setupAllProcessFieldsConfigManagers_v1() {
    document
      .querySelectorAll("form[data-process-fields-config-manager-v1='1']")
      .forEach(setupProcessFieldsConfigManager_v1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessFieldsConfigManagers_v1);
  } else {
    setupAllProcessFieldsConfigManagers_v1();
  }

  window.setTimeout(setupAllProcessFieldsConfigManagers_v1, 150);
  window.setTimeout(setupAllProcessFieldsConfigManagers_v1, 600);
})();
