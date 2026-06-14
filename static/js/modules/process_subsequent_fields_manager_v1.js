//###################################################################################
// APPVERBOBRAGA - PROCESS SUBSEQUENT FIELDS MANAGER V1
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

  function normalizeSearchText_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function escapeHtml_v1(value) {
    return toSafeString_v1(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function canUseSessionStorage_v1() {
    try {
      return Boolean(window && window.sessionStorage);
    } catch (error) {
      return false;
    }
  }

  function readStoredPaginationState_v1(storageKey, fallbackPageSize) {
    if (!storageKey || !canUseSessionStorage_v1()) {
      return null;
    }

    try {
      const rawValue = window.sessionStorage.getItem(storageKey);
      if (!rawValue) {
        return null;
      }

      const parsed = JSON.parse(rawValue);
      const page = Number.parseInt(parsed && parsed.page, 10);
      const pageSize = Number.parseInt(parsed && parsed.pageSize, 10);

      return {
        page: Number.isFinite(page) && page > 0 ? page : 1,
        pageSize: Number.isFinite(pageSize) && pageSize > 0 ? pageSize : fallbackPageSize
      };
    } catch (error) {
      return null;
    }
  }

  function saveStoredPaginationState_v1(storageKey, state) {
    if (!storageKey || !state || !canUseSessionStorage_v1()) {
      return;
    }

    try {
      window.sessionStorage.setItem(
        storageKey,
        JSON.stringify({
          page: Number.isFinite(state.page) && state.page > 0 ? state.page : 1,
          pageSize: Number.isFinite(state.pageSize) && state.pageSize > 0 ? state.pageSize : 5
        })
      );
    } catch (error) {
      // Ignore storage quota/private mode failures.
    }
  }

  function buildPaginationStorageKey_v1(form) {
    const menuKeyInput = form ? form.querySelector("input[name='menu_key']") : null;
    const menuKey = normalizeKey_v1(menuKeyInput ? menuKeyInput.value : "");
    return "appverbo:process-editor:campos-subsequentes:" + (menuKey || "default");
  }

  function getOptionLabel_v1(select, value) {
    const cleanValue = toSafeString_v1(value).trim();

    if (!select || !cleanValue) {
      return "";
    }

    const option = Array.from(select.options).find(function (item) {
      return toSafeString_v1(item.value).trim() === cleanValue;
    });

    return option ? option.textContent.trim() : cleanValue;
  }

  function getOperatorLabel_v1(value) {
    const labels = {
      equals: "Igual a",
      not_equals: "Diferente de",
      is_empty: "Vazio",
      is_not_empty: "Diferente de vazio"
    };

    return labels[value] || value || "-";
  }

  function resolveSearchText_v1(item, elements) {
    return [
      getOptionLabel_v1(elements.triggerField, item.triggerField) || "-",
      getOptionLabel_v1(elements.subsequentField, item.fieldKey) || "-",
      getOperatorLabel_v1(item.operator),
      item.triggerValue || "-"
    ].join(" ");
  }

  function resolveFilteredItems_v1(state, elements) {
    const searchQuery = normalizeSearchText_v1(state.searchQuery);

    if (!searchQuery) {
      return state.items.slice();
    }

    return state.items.filter(function (item) {
      return normalizeSearchText_v1(resolveSearchText_v1(item, elements)).includes(searchQuery);
    });
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
    button.dataset.processSubsequentAction = action;
    button.dataset.processSubsequentItemId = itemId;
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
      legacyContainer: form.querySelector("[data-process-subsequent-fields-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-subsequent-fields-hidden-container]"),
      editorKey: form.querySelector("[data-process-subsequent-field-editor-key]"),
      triggerField: form.querySelector("[data-process-subsequent-trigger-field]"),
      subsequentField: form.querySelector("[data-process-subsequent-field]"),
      operator: form.querySelector("[data-process-subsequent-operator]"),
      triggerValue: form.querySelector("[data-process-subsequent-trigger-value]"),
      submitButton: form.querySelector("[data-process-subsequent-field-submit]"),
      cancelButton: form.querySelector("[data-process-subsequent-field-cancel]"),
      table: form.querySelector("[data-process-subsequent-fields-table]"),
      tableBody: form.querySelector("[data-process-subsequent-fields-table-body]"),
      emptyState: form.querySelector("[data-process-subsequent-fields-empty]"),
      totalLabel: form.querySelector("[data-process-subsequent-fields-total-label]"),
      searchInput: form.querySelector("[data-process-subsequent-fields-search]"),
      pageSize: form.querySelector("[data-process-subsequent-fields-page-size]"),
      pagination: form.querySelector("[data-process-subsequent-fields-pagination]")
    };
  }

  function readInput_v1(row, name) {
    const input = row.querySelector("[name='" + name + "']");
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(elements.legacyContainer.querySelectorAll("[data-process-subsequent-field-row]"));

    return rows
      .map(function (row, index) {
        const triggerField = readInput_v1(row, "subsequent_trigger_field");
        const fieldKey = readInput_v1(row, "subsequent_field");
        const operator = readInput_v1(row, "subsequent_operator") || "equals";
        const triggerValue = readInput_v1(row, "subsequent_trigger_value");
        const key = readInput_v1(row, "subsequent_field_key")
          || "sub_" + normalizeKey_v1(triggerField + "_" + fieldKey + "_" + operator) + "_" + (index + 1);

        return {
          managerId: "subsequent_" + index + "_" + key,
          key: key,
          triggerField: triggerField,
          fieldKey: fieldKey,
          operator: operator,
          triggerValue: triggerValue
        };
      })
      .filter(function (item) {
        return item.triggerField || item.fieldKey;
      });
  }

  //###################################################################################
  // (3) SINCRONIZACAO COM BACKEND
  //###################################################################################

  function syncHiddenInputs_v1(state, elements) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fields = [
        ["subsequent_field_key", item.key],
        ["subsequent_trigger_field", item.triggerField],
        ["subsequent_field", item.fieldKey],
        ["subsequent_operator", item.operator],
        ["subsequent_trigger_value", item.triggerValue]
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

  function submitRemoveSilently_v1(form, state, elements, removedItem, removedIndex) {
    const actionUrl = (form.getAttribute("action") || form.action || "").trim();
    const formData = new FormData(form);

    if (typeof window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1 === "function") {
      window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1("saving", "A atualizar...");
    }

    fetch(actionUrl, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      headers: {
        "X-AppVerbo-Silent-Refresh": "1",
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then(function (response) { return response.json(); })
      .then(function (payload) {
        if (payload && payload.success === true) {
          if (typeof window.APPVERBO_MARK_TOPBAR_FEEDBACK_SYNCED_V1 === "function") {
            window.APPVERBO_MARK_TOPBAR_FEEDBACK_SYNCED_V1(payload.message || "Campo subsequente eliminado.");
          }
        } else {
          state.items.splice(removedIndex, 0, removedItem);
          renderTable_v1(state, elements);
          syncHiddenInputs_v1(state, elements);
          const errorMsg = (payload && payload.message) || "Não foi possível eliminar o campo.";
          if (typeof window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1 === "function") {
            window.APPVERBO_SET_TOPBAR_FEEDBACK_STATE_V1("error", errorMsg);
          }
        }
      })
      .catch(function () {
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit();
        } else {
          form.submit();
        }
      });
  }

  //###################################################################################
  // (4) EDITOR SUPERIOR
  //###################################################################################

  function clearEditor_v1(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";
    elements.triggerField.value = "";
    elements.subsequentField.value = "";
    elements.operator.value = "equals";
    elements.triggerValue.value = "";
  }

  function loadEditor_v1(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";
    elements.triggerField.value = item.triggerField || "";
    elements.subsequentField.value = item.fieldKey || "";
    elements.operator.value = item.operator || "equals";
    elements.triggerValue.value = item.triggerValue || "";
    elements.triggerField.focus();
  }

  function readEditorItem_v1(state, elements) {
    const triggerField = toSafeString_v1(elements.triggerField.value).trim();
    const fieldKey = toSafeString_v1(elements.subsequentField.value).trim();
    const operator = toSafeString_v1(elements.operator.value).trim() || "equals";
    const triggerValue = toSafeString_v1(elements.triggerValue.value).trim();
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();
    const key = currentKey || "sub_" + normalizeKey_v1(triggerField + "_" + fieldKey + "_" + operator + "_" + Date.now());

    return {
      managerId: state.editingId || "tmp_" + Date.now(),
      key: key,
      triggerField: triggerField,
      fieldKey: fieldKey,
      operator: operator,
      triggerValue: triggerValue
    };
  }

  function validateItem_v1(item, state) {
    if (!item.triggerField) {
      window.alert("Selecione o campo acionador.");
      return false;
    }

    if (!item.fieldKey) {
      window.alert("Selecione o campo subsequente.");
      return false;
    }

    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && existing.triggerField === item.triggerField
        && existing.fieldKey === item.fieldKey
        && existing.operator === item.operator
        && existing.triggerValue === item.triggerValue;
    });

    if (duplicate) {
      window.alert("Ja existe uma regra igual criada.");
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
      item.managerId = "tmp_" + Date.now() + "_" + normalizeKey_v1(item.triggerField + "_" + item.fieldKey);
      state.items.push(item);
      state.page = Math.max(1, Math.ceil(state.items.length / state.pageSize));
    }

    clearEditor_v1(state, elements);
    return true;
  }

  function hasDraft_v1(elements, state) {
    return Boolean(
      state.editingId ||
      toSafeString_v1(elements.triggerField.value).trim() ||
      toSafeString_v1(elements.subsequentField.value).trim() ||
      toSafeString_v1(elements.triggerValue.value).trim() ||
      toSafeString_v1(elements.operator.value).trim() !== "equals"
    );
  }

  //###################################################################################
  // (5) TABELA E PAGINACAO
  //###################################################################################

  function renderTable_v1(state, elements) {
    const totalAllItems = state.items.length;
    const filteredItems = resolveFilteredItems_v1(state, elements);
    const totalItems = filteredItems.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / state.pageSize));

    if (state.page > totalPages) {
      state.page = totalPages;
    }

    const visibleCount = Math.min(totalItems, Math.max(1, state.page) * state.pageSize);
    const visibleItems = filteredItems.slice(0, visibleCount);

    elements.tableBody.innerHTML = "";

    visibleItems.forEach(function (item, visibleIndex) {
      const absoluteIndex = findItemIndex_v1(state, item.managerId);
      const row = document.createElement("tr");

      row.dataset.processSubsequentItemId = item.managerId;
      row.innerHTML = [
        "<td>" + escapeHtml_v1(getOptionLabel_v1(elements.triggerField, item.triggerField) || "-") + "</td>",
        "<td>" + escapeHtml_v1(getOptionLabel_v1(elements.subsequentField, item.fieldKey) || "-") + "</td>",
        "<td>" + escapeHtml_v1(getOperatorLabel_v1(item.operator)) + "</td>",
        "<td>" + escapeHtml_v1(item.triggerValue || "-") + "</td>"
      ].join("");

      const actionsTd = document.createElement("td");
      const actionsWrap = document.createElement("div");

      actionsTd.className = "configurable-items-actions-cell-v1";
      actionsWrap.className = "configurable-items-actions-v1";

      actionsWrap.appendChild(createButton_v1("edit", "Editar", item.managerId, false));
      actionsWrap.appendChild(createButton_v1("up", "Subir", item.managerId, absoluteIndex === 0));
      actionsWrap.appendChild(createButton_v1("down", "Descer", item.managerId, absoluteIndex === totalAllItems - 1));
      actionsWrap.appendChild(createButton_v1("remove", "Remover", item.managerId, false));

      actionsTd.appendChild(actionsWrap);
      row.appendChild(actionsTd);
      elements.tableBody.appendChild(row);
    });

    elements.table.style.display = totalItems ? "" : "none";
    elements.emptyState.style.display = totalItems ? "none" : "";
    elements.emptyState.textContent = state.searchQuery && totalAllItems
      ? "Sem resultados para a procura."
      : "Sem campos subsequentes criados.";
    elements.totalLabel.textContent = totalAllItems + " " + (totalAllItems === 1 ? "regra" : "regras");

    renderPagination_v1(state, elements, totalPages, totalItems, visibleCount);
    saveStoredPaginationState_v1(state.storageKey, state);
  }

  function renderPagination_v1(state, elements, totalPages, totalItems, visibleCount) {
    elements.pagination.innerHTML = "";

    if (totalItems <= state.pageSize) {
      elements.pagination.style.display = "none";
      return;
    }

    elements.pagination.style.display = "";

    const configurableCore = window.AppVerboConfigurableItems || {};

    if (typeof configurableCore.renderFooterLoadMorePagination_v1 === "function") {
      configurableCore.renderFooterLoadMorePagination_v1({
        container: elements.pagination,
        currentPage: state.page,
        totalPages,
        totalItems,
        visibleCount,
        loadMoreLabel: "Mais",
        onPageChange: function (nextPage) {
          state.page = Math.max(1, Math.min(totalPages, nextPage));
          renderTable_v1(state, elements);
        }
      });
      return;
    }

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

    if (elements.searchInput) {
      elements.searchInput.addEventListener("input", function () {
        state.searchQuery = toSafeString_v1(elements.searchInput.value);
        state.page = 1;
        renderTable_v1(state, elements);
      });
    }

    elements.tableBody.addEventListener("click", function (event) {
      const button = event.target.closest("[data-process-subsequent-action]");

      if (!button) {
        return;
      }

      const action = button.dataset.processSubsequentAction;
      const itemId = button.dataset.processSubsequentItemId;
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
        const removedItem = state.items.splice(index, 1)[0];
        renderTable_v1(state, elements);
        syncHiddenInputs_v1(state, elements);
        submitRemoveSilently_v1(form, state, elements, removedItem, index);
        return;
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

  function setupProcessSubsequentFieldsManager_v1(form) {
    if (!form || form.dataset.processSubsequentFieldsManagerBoundV1 === "1") {
      return;
    }

    const elements = getElements_v1(form);

    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
      !elements.triggerField ||
      !elements.subsequentField ||
      !elements.operator ||
      !elements.triggerValue ||
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
      storageKey: buildPaginationStorageKey_v1(form),
      searchQuery: "",
      editingId: ""
    };

    const storedState = readStoredPaginationState_v1(state.storageKey, state.pageSize);
    if (storedState) {
      state.page = storedState.page;
      state.pageSize = storedState.pageSize;
    }

    if (elements.pageSize) {
      const hasOption = Array.from(elements.pageSize.options || []).some(function (optionEl) {
        return Number.parseInt(optionEl.value, 10) === state.pageSize;
      });
      if (hasOption) {
        elements.pageSize.value = String(state.pageSize);
      }
    }

    form.dataset.processSubsequentFieldsManagerBoundV1 = "1";

    bindEvents_v1(form, state, elements);
    syncHiddenInputs_v1(state, elements);
    renderTable_v1(state, elements);
  }

  function setupAllProcessSubsequentFieldsManagers_v1() {
    document
      .querySelectorAll("form[data-process-subsequent-fields-manager-v1='1']")
      .forEach(setupProcessSubsequentFieldsManager_v1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessSubsequentFieldsManagers_v1);
  } else {
    setupAllProcessSubsequentFieldsManagers_v1();
  }

  window.setTimeout(setupAllProcessSubsequentFieldsManagers_v1, 150);
  window.setTimeout(setupAllProcessSubsequentFieldsManagers_v1, 600);
})();
