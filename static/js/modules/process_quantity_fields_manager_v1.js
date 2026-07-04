//###################################################################################
// APPVERBOBRAGA - PROCESS QUANTITY FIELDS MANAGER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const FORM_SELECTOR = "form[data-process-quantity-fields-manager-v1='1']";
  const FIELD_OPTIONS_RESOLVER_NAMESPACE = "AppVerboProcessFieldOptionsResolverV1";

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

  function getFieldOptionsResolver_v1() {
    return window[FIELD_OPTIONS_RESOLVER_NAMESPACE] || null;
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
      window.console.warn("[ProcessQuantityFieldsManagerV1]", message);
    }
  }

  function submitNative_v1(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  //###################################################################################
  // (2) DOM E LEITURA INICIAL
  //###################################################################################

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
      pagination: form.querySelector("[data-process-quantity-pagination]"),
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
      elements.editorQuantityField &&
      elements.editorRepeatedFields &&
      elements.editorHeaderKey &&
      elements.editorMaxItems &&
      elements.editorItemLabel &&
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

  function parseRepeatedFieldKeys_v1(rawValue) {
    const cleanValue = toSafeString_v1(rawValue).trim();

    if (!cleanValue) {
      return [];
    }

    try {
      const parsed = JSON.parse(cleanValue);

      if (Array.isArray(parsed)) {
        return parsed
          .map((item) => toSafeString_v1(item).trim())
          .filter(Boolean);
      }
    } catch (error) {
      // Ignore invalid persisted JSON and fallback to CSV-like parsing.
    }

    return cleanValue
      .split(/[,\n;\r]+/)
      .map((item) => toSafeString_v1(item).trim())
      .filter(Boolean);
  }

  function readInitialItems_v1(elements) {
    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-quantity-field-row]")
    );

    return rows
      .map((row, index) => {
        const label = readInput_v1(row, "quantity_rule_label");
        const key = readInput_v1(row, "quantity_rule_key") || `qty_${normalizeKey_v1(label || `regra_${index + 1}`)}`;

        return {
          managerId: `quantity_${index}_${key}`,
          key,
          label,
          quantityFieldKey: readInput_v1(row, "quantity_field_key"),
          repeatedFieldKeys: parseRepeatedFieldKeys_v1(readInput_v1(row, "quantity_repeated_field_keys_json")),
          headerKey: readInput_v1(row, "quantity_header_key"),
          maxItems: readInput_v1(row, "quantity_max_items") || "10",
          itemLabel: readInput_v1(row, "quantity_item_label") || "Item"
        };
      })
      .filter((item) => item.label || item.quantityFieldKey || item.repeatedFieldKeys.length);
  }

  //###################################################################################
  // (3) OPCOES DOS SELECTS
  //###################################################################################

  function getOptionLabel_v1(select, value) {
    const cleanValue = toSafeString_v1(value).trim();

    if (!select || !cleanValue) {
      return "";
    }

    const option = Array.from(select.options).find((item) => {
      return toSafeString_v1(item.value).trim() === cleanValue;
    });

    return option ? toSafeString_v1(option.textContent).trim() : cleanValue;
  }

  function getSelectedValues_v1(select) {
    if (!select) {
      return [];
    }

    return Array.from(select.selectedOptions || [])
      .map((option) => toSafeString_v1(option.value).trim())
      .filter(Boolean);
  }

  function selectMultipleValues_v1(select, values) {
    if (!select) {
      return;
    }

    const selectedValues = new Set(
      Array.isArray(values)
        ? values.map((item) => toSafeString_v1(item).trim()).filter(Boolean)
        : []
    );

    Array.from(select.options || []).forEach((option) => {
      option.selected = selectedValues.has(toSafeString_v1(option.value).trim());
    });
  }

  function snapshotSelectOptions_v1(select) {
    const resolver = getFieldOptionsResolver_v1();

    if (resolver && typeof resolver.createOptionSnapshot_v1 === "function") {
      return resolver.createOptionSnapshot_v1(select);
    }

    return [];
  }

  function rebuildSelectOptions_v1(select, options, config) {
    if (!select) {
      return;
    }

    const safeConfig = config && typeof config === "object" ? config : {};
    const previousValue = safeConfig.multiple
      ? getSelectedValues_v1(select)
      : toSafeString_v1(select.value).trim();

    select.innerHTML = "";

    if (!safeConfig.multiple) {
      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = safeConfig.placeholder || "Selecione";
      select.appendChild(emptyOption);
    }

    (Array.isArray(options) ? options : []).forEach((item) => {
      const option = document.createElement("option");
      option.value = item.key || "";
      option.textContent = item.label || item.key || "";
      select.appendChild(option);
    });

    if (safeConfig.multiple) {
      selectMultipleValues_v1(select, previousValue);
      return;
    }

    select.value = previousValue || "";
  }

  function updateFieldOptions_v1(form, elements, manager, optionCache) {
    const resolver = getFieldOptionsResolver_v1();

    if (!resolver || typeof resolver.resolveScopeOptions_v1 !== "function") {
      return;
    }

    const resolved = resolver.resolveScopeOptions_v1(
      form.closest("#settings-menu-edit-card") || form,
      Array.isArray(optionCache && optionCache.staticOptions) ? optionCache.staticOptions : []
    );
    const selectableOptions = Array.isArray(resolved.selectableOptions)
      ? resolved.selectableOptions
      : [];
    const quantityOptions = selectableOptions.filter((option) => option.fieldType === "number");

    rebuildSelectOptions_v1(elements.editorQuantityField, quantityOptions, {
      placeholder: "Selecione"
    });
    rebuildSelectOptions_v1(elements.editorRepeatedFields, selectableOptions, {
      multiple: true
    });
    rebuildSelectOptions_v1(elements.editorHeaderKey, resolved.headerOptions, {
      placeholder: "Sem cabecalho"
    });

    if (manager) {
      manager.render();
    }
  }

  function bindFieldOptionsRefresh_v1(form, elements, manager, optionCache) {
    if (!form || form.dataset.processQuantityOptionsBoundV1 === "1") {
      return;
    }

    form.dataset.processQuantityOptionsBoundV1 = "1";

    document.addEventListener("appverbo:configurable-items-change", (event) => {
      const additionalRoot = event && event.target && typeof event.target.closest === "function"
        ? event.target.closest("[data-process-additional-fields-manager-v3='1']")
        : null;

      if (!additionalRoot) {
        return;
      }

      const formScope = form.closest("#settings-menu-edit-card") || form;

      if (!formScope.contains(additionalRoot)) {
        return;
      }

      updateFieldOptions_v1(form, elements, manager, optionCache);
    });
  }

  //###################################################################################
  // (4) EDITOR E SUBMIT
  //###################################################################################

  function syncHiddenInputs_v1(context) {
    const elements = context && context.elements ? context.elements : null;
    const items = context && Array.isArray(context.items) ? context.items : [];

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    elements.hiddenContainer.innerHTML = "";

    items.forEach((item) => {
      [
        ["quantity_rule_key", item.key],
        ["quantity_rule_label", item.label],
        ["quantity_field_key", item.quantityFieldKey],
        ["quantity_repeated_field_keys_json", JSON.stringify(item.repeatedFieldKeys || [])],
        ["quantity_header_key", item.headerKey],
        ["quantity_max_items", item.maxItems],
        ["quantity_item_label", item.itemLabel]
      ].forEach((field) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = field[0];
        input.value = field[1] || "";
        elements.hiddenContainer.appendChild(input);
      });
    });
  }

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
    elements.editorQuantityField.value = "";
    selectMultipleValues_v1(elements.editorRepeatedFields, []);
    elements.editorHeaderKey.value = "";
    elements.editorMaxItems.value = "10";
    elements.editorItemLabel.value = "Item";
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
    elements.editorQuantityField.value = item.quantityFieldKey || "";
    selectMultipleValues_v1(elements.editorRepeatedFields, item.repeatedFieldKeys || []);
    elements.editorHeaderKey.value = item.headerKey || "";
    elements.editorMaxItems.value = item.maxItems || "10";
    elements.editorItemLabel.value = item.itemLabel || "Item";
    elements.editorLabel.focus();
  }

  function readEditorItem_v1(context) {
    const state = context && context.state ? context.state : {};
    const elements = context && context.elements ? context.elements : {};
    const label = toSafeString_v1(elements.editorLabel ? elements.editorLabel.value : "").trim();
    const quantityFieldKey = toSafeString_v1(elements.editorQuantityField ? elements.editorQuantityField.value : "").trim();
    const repeatedFieldKeys = getSelectedValues_v1(elements.editorRepeatedFields);
    const headerKey = toSafeString_v1(elements.editorHeaderKey ? elements.editorHeaderKey.value : "").trim();
    const maxItems = toSafeString_v1(elements.editorMaxItems ? elements.editorMaxItems.value : "").trim() || "10";
    const itemLabel = toSafeString_v1(elements.editorItemLabel ? elements.editorItemLabel.value : "").trim() || "Item";
    const currentKey = toSafeString_v1(elements.editorKey ? elements.editorKey.value : "").trim();
    const editingId = toSafeString_v1(state.editingId).trim();
    const key = currentKey || `qty_${normalizeKey_v1(label || itemLabel)}`;

    return {
      managerId: editingId || `tmp_${Date.now()}`,
      key,
      label,
      quantityFieldKey,
      repeatedFieldKeys,
      headerKey,
      maxItems,
      itemLabel
    };
  }

  function validateItem_v1(item, context) {
    const items = context && Array.isArray(context.items) ? context.items : [];
    const editingId = context && context.state ? toSafeString_v1(context.state.editingId).trim() : "";

    if (!item.label) {
      return {
        valid: false,
        message: "Informe o nome da regra."
      };
    }

    if (!item.quantityFieldKey) {
      return {
        valid: false,
        message: "Selecione o campo origem da quantidade."
      };
    }

    if (!Array.isArray(item.repeatedFieldKeys) || !item.repeatedFieldKeys.length) {
      return {
        valid: false,
        message: "Selecione ao menos um campo repetido."
      };
    }

    const parsedMaxItems = Number.parseInt(item.maxItems, 10);

    if (!Number.isFinite(parsedMaxItems) || parsedMaxItems <= 0) {
      return {
        valid: false,
        message: "Informe uma quantidade maxima valida."
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
        message: "Ja existe uma regra com esse nome."
      };
    }

    return { valid: true };
  }

  function hasDraft_v1(elements, manager) {
    return Boolean(
      (manager && manager.state && manager.state.editingId) ||
      toSafeString_v1(elements.editorLabel.value).trim() ||
      toSafeString_v1(elements.editorQuantityField.value).trim() ||
      getSelectedValues_v1(elements.editorRepeatedFields).length
    );
  }

  function bindCancel_v1(form, elements, manager) {
    if (!form || !elements.cancelButton || form.dataset.processQuantityCancelBoundV1 === "1") {
      return;
    }

    form.dataset.processQuantityCancelBoundV1 = "1";
    elements.cancelButton.dataset.appgenesisCancel = "1";
    elements.cancelButton.dataset.appgenesisCancelLocal = "1";

    form.addEventListener("appverbo:cancelled", (event) => {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== elements.cancelButton) {
        return;
      }

      manager.clearEditing();
    });
  }

  function bindSubmit_v1(form, elements, manager) {
    if (!form || !elements.submitButton || form.dataset.processQuantitySubmitBoundV1 === "1") {
      return;
    }

    form.dataset.processQuantitySubmitBoundV1 = "1";

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

    if (form.dataset.processQuantitySubmitNativeBoundV1 === "1") {
      return;
    }

    form.dataset.processQuantitySubmitNativeBoundV1 = "1";
    form.addEventListener("submit", () => {
      manager.syncHiddenInputs();
    });
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################

  function setupProcessQuantityFieldsManager_v1(form) {
    if (!form || form.dataset.processQuantityFieldsManagerBoundV1 === "1") {
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

    form.dataset.processQuantityFieldsManagerBoundV1 = "1";

    const optionCache = {
      staticOptions: snapshotSelectOptions_v1(elements.editorQuantityField)
        .concat(snapshotSelectOptions_v1(elements.editorRepeatedFields))
        .concat(snapshotSelectOptions_v1(elements.editorHeaderKey))
    };
    const manager = core.createConfigurableItemsManager_v1({
      root: form,
      itemName: "regra",
      itemNamePlural: "regras",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 20],
      initialItems: readInitialItems_v1(elements),
      selectors: {
        editorForm: ".process-quantity-fields-editor-grid-v1",
        table: "[data-process-quantity-table]",
        tableBody: "[data-process-quantity-table-body]",
        emptyState: "[data-process-quantity-empty]",
        pagination: "[data-process-quantity-pagination]",
        pageSize: "[data-process-quantity-page-size]",
        hiddenContainer: "[data-process-quantity-fields-hidden-container]",
        totalLabel: "[data-process-quantity-total-label]",
        searchInput: "[data-configurable-search]"
      },
      columns: [
        {
          key: "label",
          label: "Regra"
        },
        {
          key: "quantityFieldKey",
          label: "Campo origem",
          render: (item) => getOptionLabel_v1(elements.editorQuantityField, item.quantityFieldKey) || "-"
        },
        {
          key: "repeatedFieldKeys",
          label: "Campos repetidos",
          render: (item) => {
            return (item.repeatedFieldKeys || [])
              .map((fieldKey) => getOptionLabel_v1(elements.editorRepeatedFields, fieldKey) || fieldKey)
              .join(", ") || "-";
          }
        },
        {
          key: "headerKey",
          label: "Cabeçalho",
          render: (item) => getOptionLabel_v1(elements.editorHeaderKey, item.headerKey) || "Sem cabeçalho"
        },
        {
          key: "maxItems",
          label: "Limite",
          render: (item) => item.maxItems || "10"
        },
        {
          key: "itemLabel",
          label: "Item",
          render: (item) => item.itemLabel || "Item"
        }
      ],
      getItemId: (item, index) => item.managerId || item.__managerId || item.key || `quantity_${index + 1}`,
      readEditorItem: readEditorItem_v1,
      loadEditorItem: loadEditorItem_v1,
      clearEditor: clearEditor_v1,
      validateItem: validateItem_v1,
      syncHiddenInputs: syncHiddenInputs_v1
    });

    if (!manager) {
      form.dataset.processQuantityFieldsManagerBoundV1 = "";
      return null;
    }

    updateFieldOptions_v1(form, elements, manager, optionCache);
    bindFieldOptionsRefresh_v1(form, elements, manager, optionCache);
    bindCancel_v1(form, elements, manager);
    bindSubmit_v1(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function setupAllProcessQuantityFieldsManagers_v1() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(setupProcessQuantityFieldsManager_v1);
  }

  //###################################################################################
  // (6) BOOT
  //###################################################################################

  window.setupProcessQuantityFieldsManagerV1 = setupAllProcessQuantityFieldsManagers_v1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessQuantityFieldsManagers_v1);
  } else {
    setupAllProcessQuantityFieldsManagers_v1();
  }
})(window, document);
