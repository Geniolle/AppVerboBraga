//###################################################################################
// APPVERBOBRAGA - PROCESS QUANTITY FIELDS MANAGER V1
//###################################################################################

(function () {
  "use strict";

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
    button.dataset.processQuantityAction = action;
    button.dataset.processQuantityItemId = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.innerHTML = icons[action] || label;

    if (disabled) {
      button.disabled = true;
    }

    return button;
  }

  function getElements_v1(form) {
    return {
      legacyContainer: form.querySelector("[data-process-quantity-fields-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-quantity-fields-hidden-container]"),
      editorKey: form.querySelector("[data-process-quantity-editor-key]"),
      editorLabel: form.querySelector("[data-process-quantity-editor-label]"),
      editorQuantityField: form.querySelector("[data-process-quantity-editor-field]"),
      editorRepeatedFields: form.querySelector("[data-process-quantity-editor-repeated-fields]"),
      editorHeaderKey: form.querySelector("[data-process-quantity-editor-header-key]"),
      editorMaxItems: form.querySelector("[data-process-quantity-editor-max-items]"),
      editorItemLabel: form.querySelector("[data-process-quantity-editor-item-label]"),
      submitButton: form.querySelector("[data-process-quantity-editor-submit]"),
      cancelButton: form.querySelector("[data-process-quantity-editor-cancel]"),
      table: form.querySelector("[data-process-quantity-table]"),
      tableBody: form.querySelector("[data-process-quantity-table-body]"),
      emptyState: form.querySelector("[data-process-quantity-empty]"),
      totalLabel: form.querySelector("[data-process-quantity-total-label]"),
      pageSize: form.querySelector("[data-process-quantity-page-size]"),
      pagination: form.querySelector("[data-process-quantity-pagination]")
    };
  }

  function readInput_v1(row, name) {
    const input = row.querySelector("[name='" + name + "']");
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function parseRepeatedFieldKeys_v1(rawValue) {
    const cleanValue = toSafeString_v1(rawValue).trim();
    if (!cleanValue) {
      return [];
    }
    try {
      const parsed = JSON.parse(cleanValue);
      if (Array.isArray(parsed)) {
        return parsed
          .map(function (item) {
            return toSafeString_v1(item).trim();
          })
          .filter(Boolean);
      }
    } catch (error) {
      // Ignore invalid persisted JSON and fallback to CSV-like parsing.
    }
    return cleanValue
      .split(/[,\n;\r]+/)
      .map(function (item) {
        return toSafeString_v1(item).trim();
      })
      .filter(Boolean);
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(elements.legacyContainer.querySelectorAll("[data-process-quantity-field-row]"));

    return rows
      .map(function (row, index) {
        const label = readInput_v1(row, "quantity_rule_label");
        const key = readInput_v1(row, "quantity_rule_key") || ("qty_" + normalizeKey_v1(label || ("regra_" + (index + 1))));
        return {
          managerId: "quantity_" + index + "_" + key,
          key: key,
          label: label,
          quantityFieldKey: readInput_v1(row, "quantity_field_key"),
          repeatedFieldKeys: parseRepeatedFieldKeys_v1(readInput_v1(row, "quantity_repeated_field_keys_json")),
          headerKey: readInput_v1(row, "quantity_header_key"),
          maxItems: readInput_v1(row, "quantity_max_items") || "10",
          itemLabel: readInput_v1(row, "quantity_item_label") || "Item"
        };
      })
      .filter(function (item) {
        return item.label || item.quantityFieldKey || item.repeatedFieldKeys.length;
      });
  }

  function getOptionLabel_v1(select, value) {
    const cleanValue = toSafeString_v1(value).trim();
    if (!select || !cleanValue) {
      return "";
    }
    const option = Array.from(select.options).find(function (item) {
      return toSafeString_v1(item.value).trim() === cleanValue;
    });
    return option ? toSafeString_v1(option.textContent).trim() : cleanValue;
  }

  function getSelectedValues_v1(select) {
    if (!select) {
      return [];
    }
    return Array.from(select.selectedOptions || [])
      .map(function (option) {
        return toSafeString_v1(option.value).trim();
      })
      .filter(Boolean);
  }

  function selectMultipleValues_v1(select, values) {
    if (!select) {
      return;
    }
    const selectedValues = new Set(
      Array.isArray(values)
        ? values.map(function (item) { return toSafeString_v1(item).trim(); }).filter(Boolean)
        : []
    );
    Array.from(select.options || []).forEach(function (option) {
      option.selected = selectedValues.has(toSafeString_v1(option.value).trim());
    });
  }

  function syncHiddenInputs_v1(state, elements) {
    elements.hiddenContainer.innerHTML = "";

    state.items.forEach(function (item) {
      const fields = [
        ["quantity_rule_key", item.key],
        ["quantity_rule_label", item.label],
        ["quantity_field_key", item.quantityFieldKey],
        ["quantity_repeated_field_keys_json", JSON.stringify(item.repeatedFieldKeys || [])],
        ["quantity_header_key", item.headerKey],
        ["quantity_max_items", item.maxItems],
        ["quantity_item_label", item.itemLabel]
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

  function clearEditor_v1(state, elements) {
    state.editingId = "";
    elements.editorKey.value = "";
    elements.editorLabel.value = "";
    elements.editorQuantityField.value = "";
    selectMultipleValues_v1(elements.editorRepeatedFields, []);
    elements.editorHeaderKey.value = "";
    elements.editorMaxItems.value = "10";
    elements.editorItemLabel.value = "Item";
  }

  function loadEditor_v1(item, state, elements) {
    state.editingId = item.managerId;
    elements.editorKey.value = item.key || "";
    elements.editorLabel.value = item.label || "";
    elements.editorQuantityField.value = item.quantityFieldKey || "";
    selectMultipleValues_v1(elements.editorRepeatedFields, item.repeatedFieldKeys || []);
    elements.editorHeaderKey.value = item.headerKey || "";
    elements.editorMaxItems.value = item.maxItems || "10";
    elements.editorItemLabel.value = item.itemLabel || "Item";
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(state, elements) {
    const label = toSafeString_v1(elements.editorLabel.value).trim();
    const quantityFieldKey = toSafeString_v1(elements.editorQuantityField.value).trim();
    const repeatedFieldKeys = getSelectedValues_v1(elements.editorRepeatedFields);
    const headerKey = toSafeString_v1(elements.editorHeaderKey.value).trim();
    const maxItems = toSafeString_v1(elements.editorMaxItems.value).trim() || "10";
    const itemLabel = toSafeString_v1(elements.editorItemLabel.value).trim() || "Item";
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();
    const key = currentKey || ("qty_" + normalizeKey_v1(label || itemLabel));

    return {
      managerId: state.editingId || "tmp_" + Date.now(),
      key: key,
      label: label,
      quantityFieldKey: quantityFieldKey,
      repeatedFieldKeys: repeatedFieldKeys,
      headerKey: headerKey,
      maxItems: maxItems,
      itemLabel: itemLabel
    };
  }

  function validateItem_v1(item, state) {
    if (!item.label) {
      window.alert("Informe o nome da regra.");
      return false;
    }
    if (!item.quantityFieldKey) {
      window.alert("Selecione o campo origem da quantidade.");
      return false;
    }
    if (!Array.isArray(item.repeatedFieldKeys) || !item.repeatedFieldKeys.length) {
      window.alert("Selecione ao menos um campo repetido.");
      return false;
    }
    const parsedMaxItems = Number.parseInt(item.maxItems, 10);
    if (!Number.isFinite(parsedMaxItems) || parsedMaxItems <= 0) {
      window.alert("Informe uma quantidade máxima válida.");
      return false;
    }
    const duplicate = state.items.some(function (existing) {
      return existing.managerId !== item.managerId
        && normalizeKey_v1(existing.label) === normalizeKey_v1(item.label);
    });
    if (duplicate) {
      window.alert("Já existe uma regra com esse nome.");
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
      item.managerId = "tmp_" + Date.now() + "_" + normalizeKey_v1(item.label || item.itemLabel);
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
      toSafeString_v1(elements.editorQuantityField.value).trim() ||
      getSelectedValues_v1(elements.editorRepeatedFields).length
    );
  }

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
      row.dataset.processQuantityItemId = item.managerId;

      const repeatedLabel = (item.repeatedFieldKeys || [])
        .map(function (fieldKey) {
          return getOptionLabel_v1(elements.editorRepeatedFields, fieldKey) || fieldKey;
        })
        .join(", ");

      row.innerHTML = [
        "<td>" + escapeHtml_v1(item.label) + "</td>",
        "<td>" + escapeHtml_v1(getOptionLabel_v1(elements.editorQuantityField, item.quantityFieldKey) || "-") + "</td>",
        "<td>" + escapeHtml_v1(repeatedLabel || "-") + "</td>",
        "<td>" + escapeHtml_v1(getOptionLabel_v1(elements.editorHeaderKey, item.headerKey) || "Sem cabeçalho") + "</td>",
        "<td>" + escapeHtml_v1(item.maxItems || "10") + "</td>",
        "<td>" + escapeHtml_v1(item.itemLabel || "Item") + "</td>"
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
    elements.totalLabel.textContent = totalItems + " " + (totalItems === 1 ? "regra" : "regras");

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
      const button = event.target.closest("[data-process-quantity-action]");
      if (!button) {
        return;
      }

      const action = button.dataset.processQuantityAction;
      const itemId = button.dataset.processQuantityItemId;
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

  function setupProcessQuantityFieldsManager_v1(form) {
    if (!form || form.dataset.processQuantityFieldsManagerBoundV1 === "1") {
      return;
    }

    const elements = getElements_v1(form);
    if (
      !elements.legacyContainer ||
      !elements.hiddenContainer ||
      !elements.editorKey ||
      !elements.editorLabel ||
      !elements.editorQuantityField ||
      !elements.editorRepeatedFields ||
      !elements.editorHeaderKey ||
      !elements.editorMaxItems ||
      !elements.editorItemLabel ||
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

    form.dataset.processQuantityFieldsManagerBoundV1 = "1";

    bindEvents_v1(form, state, elements);
    syncHiddenInputs_v1(state, elements);
    renderTable_v1(state, elements);
  }

  function setupAllProcessQuantityFieldsManagers_v1() {
    document
      .querySelectorAll("form[data-process-quantity-fields-manager-v1='1']")
      .forEach(setupProcessQuantityFieldsManager_v1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessQuantityFieldsManagers_v1);
  } else {
    setupAllProcessQuantityFieldsManagers_v1();
  }

  window.setTimeout(setupAllProcessQuantityFieldsManagers_v1, 150);
  window.setTimeout(setupAllProcessQuantityFieldsManagers_v1, 600);
})();
