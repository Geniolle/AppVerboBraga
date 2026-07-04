//###################################################################################
// APPVERBOBRAGA - PROCESS LISTS MANAGER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const FORM_SELECTOR = "form[data-process-lists-manager-v1='1']";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function getCore_v1() {
    return window.AppVerboConfigurableItems || {};
  }

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

  function showValidationMessage_v1(message) {
    const core = getCore_v1();

    if (typeof core.showAlertDialog_v1 === "function") {
      core.showAlertDialog_v1({
        title: "Validacao",
        message
      });
      return;
    }

    if (
      window.AppGenesisDialogV1 &&
      typeof window.AppGenesisDialogV1.alert === "function"
    ) {
      window.AppGenesisDialogV1.alert({
        title: "Validacao",
        message
      });
      return;
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[ProcessListsManagerV1]", message);
    }
  }

  function submitNative_v1(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (2) ELEMENTOS E LEITURA INICIAL
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
      pagination: form.querySelector("[data-process-lists-pagination]"),
      searchInput: form.querySelector("[data-configurable-search]")
    };
  }

  function hasRequiredElements_v1(elements) {
    return Boolean(
      elements &&
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.editorLabel &&
      elements.editorItems &&
      elements.submitButton &&
      elements.cancelButton &&
      elements.table &&
      elements.tableBody &&
      elements.emptyState &&
      elements.pageSize &&
      elements.pagination
    );
  }

  function readInput_v1(row, name) {
    const input = row.querySelector(`[name='${name}']`);
    return input ? toSafeString_v1(input.value).trim() : "";
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-list-row]")
    );

    return rows
      .map((row, index) => {
        const label = readInput_v1(row, "process_list_label");
        const key = readInput_v1(row, "process_list_key") || normalizeKey_v1(label) || `lista_${index + 1}`;
        const itemsCsv = readInput_v1(row, "process_list_items_csv");

        return {
          managerId: `list_${index}_${key}`,
          key,
          label,
          itemsCsv
        };
      })
      .filter((item) => item.label || item.itemsCsv);
  }

  //###################################################################################
  // (3) EDITOR E COMPATIBILIDADE DE SUBMIT
  //###################################################################################

  function clearEditor_v1(context) {
    const elements = context && context.elements ? context.elements : context;
    const manager = context && context.manager ? context.manager : null;

    if (manager && manager.root) {
      manager.root.classList.remove("configurable-items-editing-v1");
    }

    if (!elements) {
      return;
    }

    elements.editorKey.value = "";
    elements.editorLabel.value = "";
    elements.editorItems.value = "";
  }

  function loadEditorItem_v1(item, context) {
    const elements = context && context.elements ? context.elements : null;
    const manager = context && context.manager ? context.manager : null;

    if (!item || !elements) {
      return;
    }

    if (manager && manager.root) {
      manager.root.classList.add("configurable-items-editing-v1");
    }

    elements.editorKey.value = item.key || "";
    elements.editorLabel.value = item.label || "";
    elements.editorItems.value = item.itemsCsv || "";
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(context) {
    const state = context && context.state ? context.state : {};
    const elements = context && context.elements ? context.elements : {};
    const label = toSafeString_v1(elements.editorLabel ? elements.editorLabel.value : "").trim();
    const itemsCsv = toSafeString_v1(elements.editorItems ? elements.editorItems.value : "").trim();
    const currentKey = toSafeString_v1(elements.editorKey ? elements.editorKey.value : "").trim();
    const editingId = toSafeString_v1(state.editingId).trim();
    const key = currentKey || normalizeKey_v1(label);

    return {
      managerId: editingId || `tmp_${Date.now()}`,
      key,
      label,
      itemsCsv
    };
  }

  function validateItem_v1(item, context) {
    const items = context && Array.isArray(context.items) ? context.items : [];
    const editingId = context && context.state ? toSafeString_v1(context.state.editingId).trim() : "";

    if (!item.label) {
      return {
        valid: false,
        message: "Informe o nome da lista."
      };
    }

    const normalizedLabel = normalizeKey_v1(item.label);
    const duplicate = items.some((existing) => {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId !== editingId && normalizeKey_v1(existing.label) === normalizedLabel;
    });

    if (duplicate) {
      return {
        valid: false,
        message: "Ja existe uma lista com esse nome."
      };
    }

    return { valid: true };
  }

  function hasDraft_v1(elements, manager) {
    return Boolean(
      (manager && manager.state && manager.state.editingId) ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorItems.value).trim()
    );
  }

  function syncHiddenInputs_v1(context) {
    const elements = context && context.elements ? context.elements : null;
    const items = context && Array.isArray(context.items) ? context.items : [];

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    elements.hiddenContainer.innerHTML = "";

    items.forEach((item) => {
      [
        ["process_list_key", item.key],
        ["process_list_label", item.label],
        ["process_list_items_csv", item.itemsCsv]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  function bindCancel_v1(form, elements, manager) {
    if (!form || !elements.cancelButton || form.dataset.processListsCancelBoundV1 === "1") {
      return;
    }

    form.dataset.processListsCancelBoundV1 = "1";
    elements.cancelButton.dataset.appverboCancel = "1";
    elements.cancelButton.dataset.appverboCancelLocal = "1";

    form.addEventListener("appverbo:cancelled", (event) => {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== elements.cancelButton) {
        return;
      }

      manager.clearEditing();
    });
  }

  function bindSubmit_v1(form, elements, manager) {
    if (!form || !elements.submitButton || form.dataset.processListsSubmitBoundV1 === "1") {
      return;
    }

    form.dataset.processListsSubmitBoundV1 = "1";

    elements.submitButton.addEventListener("click", (event) => {
      event.preventDefault();

      if (hasDraft_v1(elements, manager)) {
        const item = readEditorItem_v1({
          manager,
          elements: manager.elements,
          state: manager.state
        });
        const validationResult = validateItem_v1(item, {
          manager,
          elements: manager.elements,
          state: manager.state,
          items: manager.getItems()
        });

        if (validationResult && validationResult.valid === false) {
          if (validationResult.message) {
            showValidationMessage_v1(validationResult.message);
          }
          return;
        }

        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      submitNative_v1(form);
    });

    if (form.dataset.processListsSubmitNativeBoundV1 === "1") {
      return;
    }

    form.dataset.processListsSubmitNativeBoundV1 = "1";
    form.addEventListener("submit", () => {
      manager.syncHiddenInputs();
    });
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function setupProcessListsManager_v1(form) {
    if (!form || form.dataset.processListsManagerBoundV1 === "1") {
      return null;
    }

    const core = getCore_v1();

    if (!core || typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const elements = getElements_v1(form);

    if (!hasRequiredElements_v1(elements)) {
      return null;
    }

    form.dataset.processListsManagerBoundV1 = "1";

    const manager = core.createConfigurableItemsManager_v1({
      root: form,
      itemName: "lista",
      itemNamePlural: "listas",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 20],
      initialItems: readInitialItems_v1(elements),
      selectors: {
        editorForm: "[data-process-list-editor-block]",
        table: "[data-process-lists-table]",
        tableBody: "[data-process-lists-table-body]",
        emptyState: "[data-process-lists-empty]",
        pagination: "[data-process-lists-pagination]",
        pageSize: "[data-process-lists-page-size]",
        hiddenContainer: "[data-process-lists-hidden-container]",
        totalLabel: "[data-process-lists-total-label]",
        searchInput: "[data-configurable-search]"
      },
      columns: [
        {
          key: "label",
          label: "Nome da lista"
        },
        {
          key: "itemsCsv",
          label: "Conteúdo da lista",
          render: (item) => item.itemsCsv || "-"
        }
      ],
      getItemId: (item, index) => item.managerId || item.__managerId || item.key || `list_${index + 1}`,
      readEditorItem: readEditorItem_v1,
      loadEditorItem: loadEditorItem_v1,
      clearEditor: clearEditor_v1,
      validateItem: validateItem_v1,
      syncHiddenInputs: syncHiddenInputs_v1
    });

    if (!manager) {
      form.dataset.processListsManagerBoundV1 = "";
      return null;
    }

    bindCancel_v1(form, elements, manager);
    bindSubmit_v1(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function setupAllProcessListsManagers_v1() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(setupProcessListsManager_v1);
  }

  //###################################################################################
  // (5) BOOT
  //###################################################################################

  window.setupProcessListsManagerV1 = setupAllProcessListsManagers_v1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessListsManagers_v1);
  } else {
    setupAllProcessListsManagers_v1();
  }
})(window, document);
