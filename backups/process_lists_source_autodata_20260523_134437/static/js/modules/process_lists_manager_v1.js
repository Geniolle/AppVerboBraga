//###################################################################################
// APPVERBOBRAGA - PROCESS LISTS MANAGER V1
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNCOES BASE
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKey_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function escapeHtml_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
    button.dataset.processListAction = action;
    button.dataset.processListItemId = itemId;
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
      legacyContainer: form.querySelector("[data-process-lists-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-lists-hidden-container]"),
      editorKey: form.querySelector("[data-process-list-editor-key]"),
      editorLabel: form.querySelector("[data-process-list-editor-label]"),
      editorItems: form.querySelector("[data-process-list-editor-items]"),
      submitButton: form.querySelector("[data-process-list-editor-submit]"),
      cancelButton: form.querySelector("[data-process-list-editor-cancel]"),
      table: form.querySelector("[data-process-lists-table]"),
      tableBody: form.querySelector("[data-process-lists-table-body]"),
      emptyState: form.querySelector("[data-process-lists-empty]"),
      totalLabel: form.querySelector("[data-process-lists-total-label]"),
      pageSize: form.querySelector("[data-process-lists-page-size]"),
      pagination: form.querySelector("[data-process-lists-pagination]")
    };
  }

  function readInput_v1(row, name) {
    const input = row.querySelector("[name='" + name + "']");
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(elements.legacyContainer.querySelectorAll("[data-process-list-row]"));

    return rows
      .map(function (row, index) {
        const label = readInput_v1(row, "process_list_label");
        const key = readInput_v1(row, "process_list_key") || normalizeKey_v1(label) || "lista_" + (index + 1);
        const itemsCsv = readInput_v1(row, "process_list_items_csv");

        return {
          managerId: "list_" + index + "_" + key,
          key: key,
          label: label,
          itemsCsv: itemsCsv
        };
      })
      .filter(function (item) {
        return item.label || item.itemsCsv;
      });
  }

  //###################################################################################
  // (3) SINCRONIZACAO COM BACKEND
  //###################################################################################

  function syncHiddenInputs_v1(state, elements) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fields = [
        ["process_list_key", item.key],
        ["process_list_label", item.label],
        ["process_list_items_csv", item.itemsCsv]
      ];

      fields.forEach(function (field) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4) EDITOR SUPERIOR
  //###################################################################################

  function clearEditor_v1(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";
    elements.editorLabel.value = "";
    elements.editorItems.value = "";
  }

  function loadEditor_v1(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";
    elements.editorLabel.value = item.label || "";
    elements.editorItems.value = item.itemsCsv || "";
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(state, elements) {
    const label = toSafeString_v1(elements.editorLabel.value).trim();
    const itemsCsv = toSafeString_v1(elements.editorItems.value).trim();
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();
    const key = currentKey || normalizeKey_v1(label);

    return {
      managerId: state.editingId || "tmp_" + Date.now(),
      key: key,
      label: label,
      itemsCsv: itemsCsv
    };
  }

  function validateItem_v1(item, state) {
    if (!item.label) {
      window.alert("Informe o nome da lista.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && normalizeKey_v1(existing.label) === normalizeKey_v1(item.label);
    });

    if (duplicate) {
      window.alert("Ja existe uma lista com esse nome.");
      return false;
    }

    return true;
  }

  function addOrUpdateFromEditor_v1(state, elements) {
    const item = readEditorItem_v1(state, elements);

    if (!validateItem_v1(item, state)) {
      return false;
    }

    const currentIndex = state.items.findIndex(function (existing) {
      return existing.managerId === item.managerId;
    });

    if (currentIndex >= 0) {
      state.items[currentIndex] = item;
    } else {
      item.managerId = "tmp_" + Date.now() + "_" + normalizeKey_v1(item.label);
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v1(state, elements);
    return true;
  }

  function hasDraft_v1(elements, state) {
    return Boolean(
      state.editingId ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorItems.value).trim()
    );
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

      row.dataset.processListItemId = item.managerId;
      row.innerHTML = [
        "<td>" + escapeHtml_v1(item.label) + "</td>",
        "<td>" + escapeHtml_v1(item.itemsCsv || "-") + "</td>"
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
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "lista" : "listas");

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
      const button = event.target.closest("[data-process-list-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processListAction;
      const itemId = button.dataset.processListItemId;
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

  function setupProcessListsManager_v1(form) {
    if (!form || form.dataset.processListsManagerBoundV1 === "1") {
      return;
    }

    const elements = getElements_v1(form);

    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
      !elements.editorLabel ||
      !elements.editorItems ||
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

    form.dataset.processListsManagerBoundV1 = "1";

    bindEvents_v1(form, state, elements);
    syncHiddenInputs_v1(state, elements);
    renderTable_v1(state, elements);
  }

  function setupAllProcessListsManagers_v1() {
    document
      .querySelectorAll("form[data-process-lists-manager-v1='1']")
      .forEach(setupProcessListsManager_v1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessListsManagers_v1);
  } else {
    setupAllProcessListsManagers_v1();
  }

  window.setTimeout(setupAllProcessListsManagers_v1, 150);
  window.setTimeout(setupAllProcessListsManagers_v1, 600);
})();
