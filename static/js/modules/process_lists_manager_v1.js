//###################################################################################
// APPGENESIS - PROCESS LISTS MANAGER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const FORM_SELECTOR = "form[data-process-lists-manager-v1='1']";

  //###################################################################################
  // (1) HELPERS
  //###################################################################################

  function getCore_v1() {
    return window.AppGenesisConfigurableItems || {};
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
    const root = form.querySelector("[data-process-list-reusable-manager]");

    if (!root) {
      return null;
    }

    return {
      root,
      legacyContainer: root.querySelector("[data-process-lists-legacy-container]"),
      hiddenContainer: root.querySelector("[data-process-lists-hidden-container]"),
      editorKey: root.querySelector("[data-process-list-editor-key]"),
      editorLabel: root.querySelector("[data-process-list-editor-label]"),
      editorItems: root.querySelector("[data-process-list-editor-items]"),
      editorItemsWrapper: root.querySelector("[data-process-list-editor-items-wrapper]"),
      editorFieldType: root.querySelector("[data-process-list-editor-field-type]"),
      editorSourceMenu: root.querySelector("[data-process-list-editor-source-menu]"),
      editorSourceMenuWrapper: root.querySelector("[data-process-list-editor-menu-wrapper]"),
      submitButton: root.querySelector("[data-process-list-editor-submit]"),
      cancelButton: root.querySelector("[data-process-list-editor-cancel]"),
      table: root.querySelector("[data-process-lists-table]"),
      tableBody: root.querySelector("[data-process-lists-table-body]"),
      emptyState: root.querySelector("[data-process-lists-empty]"),
      totalLabel: root.querySelector("[data-process-lists-total-label]"),
      pageSize: root.querySelector("[data-process-lists-page-size]"),
      pagination: root.querySelector("[data-process-lists-pagination]"),
      searchInput: root.querySelector("[data-configurable-search]")
    };
  }

  function hasRequiredElements_v1(elements) {
    return Boolean(
      elements &&
      elements.root &&
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.editorLabel &&
      elements.editorFieldType &&
      elements.editorItems &&
      elements.editorItemsWrapper &&
      elements.editorSourceMenu &&
      elements.editorSourceMenuWrapper &&
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
        const fieldType = (readInput_v1(row, "process_list_field_type") || "").trim().toLowerCase();
        const itemsCsv = readInput_v1(row, "process_list_items_csv");
        const sourceMenuKey = readInput_v1(row, "process_list_source_menu_key");

        return {
          managerId: `list_${index}_${key}`,
          key,
          label,
          field_type: fieldType || "manual",
          itemsCsv,
          sourceMenuKey
        };
      })
      .filter((item) => item.label || item.itemsCsv);
  }

  //###################################################################################
  // (3) COLUNAS DA LISTAGEM DO PROCESSO
  //###################################################################################

  function getColumnElements_v2(form) {
    const root = form.querySelector("[data-process-list-columns-manager]");

    if (!root) {
      return null;
    }

    return {
      root,
      legacyContainer: root.querySelector("[data-process-list-columns-legacy-container]"),
      hiddenContainer: root.querySelector("[data-process-list-columns-hidden-container]"),
      editorKey: root.querySelector("[data-process-list-column-editor-key]"),
      editorField: root.querySelector("[data-process-list-column-editor-field]"),
      editorLabel: root.querySelector("[data-process-list-column-editor-label]"),
      editorSourceKind: root.querySelector("[data-process-list-column-editor-source-kind]"),
      editorAlwaysVisible: root.querySelector("[data-process-list-column-editor-always-visible]"),
      editorPriority: root.querySelector("[data-process-list-column-editor-priority]"),
      submitButton: root.querySelector("[data-process-list-column-editor-submit]"),
      cancelButton: root.querySelector("[data-process-list-column-editor-cancel]"),
      pageSize: root.querySelector("[data-process-list-columns-page-size]")
    };
  }

  function readInitialColumns_v2(elements) {
    return Array.from(elements.legacyContainer.querySelectorAll("[data-process-list-column-row]"))
      .map((row, index) => {
        const fieldKey = readInput_v1(row, "process_list_column_field_key");
        const key = readInput_v1(row, "process_list_column_key") || fieldKey;

        return {
          managerId: `column_${index}_${key}`,
          key,
          label: readInput_v1(row, "process_list_column_label"),
          fieldKey,
          sourceKind: readInput_v1(row, "process_list_column_source_kind") || "field",
          alwaysVisible: readInput_v1(row, "process_list_column_always_visible") === "1",
          responsivePriority: Number.parseInt(readInput_v1(row, "process_list_column_responsive_priority"), 10) || 0
        };
      })
      .filter((item) => item.fieldKey);
  }

  function clearColumnEditor_v2(context) {
    const elements = context && context.elements ? context.elements : context;

    if (!elements) {
      return;
    }

    elements.editorKey.value = "";
    elements.editorField.value = "";
    elements.editorLabel.value = "";
    elements.editorAlwaysVisible.checked = false;
    elements.editorPriority.value = "0";
  }

  function loadColumnEditorItem_v2(item, context) {
    const elements = context && context.elements ? context.elements : null;

    if (!item || !elements) {
      return;
    }

    elements.editorKey.value = item.key || "";
    elements.editorField.value = item.fieldKey || "";
    elements.editorLabel.value = item.label || "";
    elements.editorAlwaysVisible.checked = Boolean(item.alwaysVisible);
    elements.editorPriority.value = String(item.responsivePriority || 0);
    elements.editorField.focus();
  }

  function readColumnEditorItem_v2(context) {
    const elements = context.elements;
    const fieldKey = toSafeString_v1(elements.editorField.value).trim();
    const selectedOption = elements.editorField.options[elements.editorField.selectedIndex];
    const label = toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(selectedOption ? selectedOption.textContent : "").trim();
    const currentKey = toSafeString_v1(elements.editorKey.value).trim();

    return {
      managerId: toSafeString_v1(context.state.editingId).trim() || `tmp_column_${Date.now()}`,
      key: currentKey || fieldKey,
      label,
      fieldKey,
      sourceKind: "field",
      alwaysVisible: Boolean(elements.editorAlwaysVisible.checked),
      responsivePriority: Number.parseInt(elements.editorPriority.value, 10) || 0
    };
  }

  function validateColumnItem_v2(item, context) {
    if (!item.fieldKey) {
      return { valid: false, message: "Selecione o campo da coluna." };
    }

    const editingId = toSafeString_v1(context.state.editingId).trim();
    const duplicate = context.items.some((existing) => {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId !== editingId && existing.fieldKey === item.fieldKey;
    });

    return duplicate
      ? { valid: false, message: "Este campo já está configurado como coluna." }
      : { valid: true };
  }

  function syncColumnHiddenInputs_v2(context) {
    const elements = context.elements;
    elements.hiddenContainer.innerHTML = "";

    context.items.forEach((item) => {
      [
        ["process_list_column_key", item.key],
        ["process_list_column_label", item.label],
        ["process_list_column_field_key", item.fieldKey],
        ["process_list_column_source_kind", item.sourceKind || "field"],
        ["process_list_column_always_visible", item.alwaysVisible ? "1" : "0"],
        ["process_list_column_responsive_priority", String(item.responsivePriority || 0)]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4) EDITOR E COMPATIBILIDADE DE SUBMIT
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
    elements.editorSourceMenu.value = "";
    delete elements.editorItems.dataset.previousItems;
    if (elements.editorFieldType) {
      elements.editorFieldType.value = "manual";
    }
    // ensure items input enabled when cleared
    if (elements.editorFieldType) {
      applyEditorFieldTypeState_v2(elements, { resetTemporaryState: true });
    }
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
    elements.editorSourceMenu.value = item.sourceMenuKey || "";
    delete elements.editorItems.dataset.previousItems;
    if (elements.editorFieldType) {
      elements.editorFieldType.value = item.field_type || "manual";
    }
    // apply enable/disable state according to field type
    if (elements.editorFieldType) {
      applyEditorFieldTypeState_v2(elements);
    }
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(context) {
    const state = context && context.state ? context.state : {};
    const elements = context && context.elements ? context.elements : {};
    const label = toSafeString_v1(elements.editorLabel ? elements.editorLabel.value : "").trim();
    const itemsCsv = toSafeString_v1(elements.editorItems ? elements.editorItems.value : "").trim();
    const fieldType = toSafeString_v1(elements.editorFieldType ? elements.editorFieldType.value : "").trim().toLowerCase();
    const sourceMenuKey = toSafeString_v1(elements.editorSourceMenu ? elements.editorSourceMenu.value : "").trim().toLowerCase();
    const currentKey = toSafeString_v1(elements.editorKey ? elements.editorKey.value : "").trim();
    const editingId = toSafeString_v1(state.editingId).trim();
    const key = currentKey || normalizeKey_v1(label);

    return {
      managerId: editingId || `tmp_${Date.now()}`,
      key,
      label,
      field_type: (fieldType === "automatic" ? "automatic" : "manual"),
      itemsCsv: fieldType === "automatic" ? "" : itemsCsv,
      sourceMenuKey: fieldType === "automatic" ? sourceMenuKey : ""
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

    if (item.field_type === "manual" && !item.itemsCsv) {
      return { valid: false, message: "Informe o conteúdo da lista." };
    }

    if (item.field_type === "automatic" && !item.sourceMenuKey) {
      return {
        valid: false,
        message: "Selecione o menu de origem da lista automática."
      };
    }

    return { valid: true };
  }

  function hasDraft_v1(elements, manager) {
    return Boolean(
      (manager && manager.state && manager.state.editingId) ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorItems.value).trim()
      || toSafeString_v1(elements.editorSourceMenu.value).trim()
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
        ["process_list_field_type", item.field_type || "manual"],
        ["process_list_items_csv", item.field_type === "automatic" ? "" : item.itemsCsv],
        ["process_list_source_menu_key", item.field_type === "automatic" ? item.sourceMenuKey : ""]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

  //###################################################################################
  // (4.5) FIELD TYPE UI BEHAVIOR
  //###################################################################################

  function applyEditorFieldTypeState_v2(elements, options) {
    if (!elements || !elements.editorFieldType || !elements.editorItems ||
        !elements.editorItemsWrapper || !elements.editorSourceMenu ||
        !elements.editorSourceMenuWrapper) {
      return;
    }

    const val = String(elements.editorFieldType.value || "").trim().toLowerCase();
    const resetTemporaryState = Boolean(options && options.resetTemporaryState);

    if (val === "automatic") {
      if (elements.editorItems.dataset.previousItems === undefined) {
        elements.editorItems.dataset.previousItems = elements.editorItems.value || "";
      }
      elements.editorItems.value = "";
      elements.editorItems.disabled = true;
      elements.editorItemsWrapper.hidden = true;
      elements.editorSourceMenuWrapper.hidden = false;
      elements.editorSourceMenu.disabled = false;
    } else {
      elements.editorSourceMenu.value = "";
      elements.editorSourceMenu.disabled = true;
      elements.editorSourceMenuWrapper.hidden = true;
      elements.editorItemsWrapper.hidden = false;
      elements.editorItems.disabled = false;
      if (!resetTemporaryState && elements.editorItems.dataset.previousItems !== undefined) {
        if (!elements.editorItems.value) {
          elements.editorItems.value = elements.editorItems.dataset.previousItems || "";
        }
      }
      delete elements.editorItems.dataset.previousItems;
    }
  }

  function bindCancel_v1(form, elements, manager) {
    if (!form || !elements.cancelButton || form.dataset.processListsCancelBoundV1 === "1") {
      return;
    }

    form.dataset.processListsCancelBoundV1 = "1";
    elements.cancelButton.dataset.appgenesisCancel = "1";
    elements.cancelButton.dataset.appgenesisCancelLocal = "1";

    form.addEventListener("appgenesis:cancelled", (event) => {
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
      if (form.processListColumnsManagerV2) {
        form.processListColumnsManagerV2.syncHiddenInputs();
      }
      submitNative_v1(form);
    });

    if (form.dataset.processListsSubmitNativeBoundV1 === "1") {
      return;
    }

    form.dataset.processListsSubmitNativeBoundV1 = "1";
    form.addEventListener("submit", () => {
      manager.syncHiddenInputs();
      if (form.processListColumnsManagerV2) {
        form.processListColumnsManagerV2.syncHiddenInputs();
      }
    });
  }

  function setupProcessListColumnsManager_v2(form) {
    const core = getCore_v1();
    const elements = getColumnElements_v2(form);

    if (!elements || !elements.legacyContainer || !elements.hiddenContainer ||
        !elements.editorField || !elements.editorLabel || !elements.submitButton ||
        !elements.cancelButton || !elements.pageSize) {
      return null;
    }

    const manager = core.createConfigurableItemsManager_v1({
      root: elements.root,
      itemName: "coluna",
      itemNamePlural: "colunas",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 20],
      initialItems: readInitialColumns_v2(elements),
      selectors: {
        editorForm: "[data-process-list-column-editor-block]",
        table: "[data-process-list-columns-table]",
        tableBody: "[data-process-list-columns-table-body]",
        emptyState: "[data-process-list-columns-empty]",
        pagination: "[data-process-list-columns-pagination]",
        pageSize: "[data-process-list-columns-page-size]",
        hiddenContainer: "[data-process-list-columns-hidden-container]",
        totalLabel: "[data-process-list-columns-total-label]"
      },
      columns: [
        { key: "fieldKey", label: "Campo da coluna", render: (item) => {
          const option = Array.from(elements.editorField.options).find((entry) => entry.value === item.fieldKey);
          return option ? option.textContent : item.fieldKey;
        } },
        { key: "label", label: "Nome da coluna" },
        { key: "alwaysVisible", label: "Sempre visível", render: (item) => item.alwaysVisible ? "Sim" : "Não" },
        { key: "responsivePriority", label: "Prioridade" }
      ],
      getItemId: (item, index) => item.managerId || item.__managerId || item.key || `column_${index + 1}`,
      readEditorItem: readColumnEditorItem_v2,
      loadEditorItem: loadColumnEditorItem_v2,
      clearEditor: clearColumnEditor_v2,
      validateItem: validateColumnItem_v2,
      syncHiddenInputs: syncColumnHiddenInputs_v2
    });

    if (!manager) {
      return null;
    }

    Object.assign(manager.elements, elements);
    elements.cancelButton.dataset.appgenesisCancel = "1";
    elements.cancelButton.dataset.appgenesisCancelLocal = "1";
    form.addEventListener("appgenesis:cancelled", (event) => {
      if (event.detail && event.detail.trigger === elements.cancelButton) {
        manager.clearEditing();
      }
    });
    elements.submitButton.addEventListener("click", (event) => {
      event.preventDefault();
      const hasDraft = Boolean(manager.state.editingId || elements.editorField.value || elements.editorLabel.value.trim());

      if (hasDraft) {
        const item = readColumnEditorItem_v2({ elements, state: manager.state });
        const validation = validateColumnItem_v2(item, { items: manager.getItems(), state: manager.state });

        if (!validation.valid) {
          showValidationMessage_v1(validation.message);
          return;
        }
        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      if (form.processListsManagerV1) {
        form.processListsManagerV1.syncHiddenInputs();
      }
      submitNative_v1(form);
    });
    manager.syncHiddenInputs();
    form.processListColumnsManagerV2 = manager;
    return manager;
  }

  //###################################################################################
  // (5) INICIALIZACAO
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
      root: elements.root,
      itemName: "lista",
      itemNamePlural: "listas",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 20],
      initialItems: readInitialItems_v1(elements),
      selectors: {
        editorForm: "[data-process-list-reusable-editor-block]",
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
          key: "field_type",
          label: "Tipo de campo",
          render: (item) => {
            const ft = String(item.field_type || "").trim().toLowerCase();
            return ft === "automatic" ? "Automático" : "Manual";
          }
        },
        {
          key: "itemsCsv",
          label: "Conteúdo da lista",
          render: (item) => item.itemsCsv || "-"
        },
        {
          key: "sourceMenuKey",
          label: "Menu",
          render: (item) => {
            if (String(item.field_type || "manual").toLowerCase() !== "automatic") {
              return "-";
            }
            const option = Array.from(elements.editorSourceMenu.options).find(
              (entry) => entry.value === item.sourceMenuKey
            );
            return option ? option.textContent : "Menu indisponível";
          }
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

    Object.assign(manager.elements, elements);

    elements.editorFieldType.addEventListener("change", () => {
      applyEditorFieldTypeState_v2(elements);
    });
    applyEditorFieldTypeState_v2(elements, { resetTemporaryState: true });

    bindCancel_v1(form, elements, manager);
    form.processListsManagerV1 = manager;
    setupProcessListColumnsManager_v2(form);
    bindSubmit_v1(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function setupAllProcessListsManagers_v1() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(setupProcessListsManager_v1);
  }

  //###################################################################################
  // (6) BOOT
  //###################################################################################

  window.setupProcessListsManagerV1 = setupAllProcessListsManagers_v1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessListsManagers_v1);
  } else {
    setupAllProcessListsManagers_v1();
  }
})(window, document);
