//###################################################################################
// APPVERBOBRAGA - PROCESS SUBSEQUENT FIELDS MANAGER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const FORM_SELECTOR = "form[data-process-subsequent-fields-manager-v1='1']";
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
      window.AppVerboDialogV1 &&
      typeof window.AppVerboDialogV1.alert === "function"
    ) {
      window.AppVerboDialogV1.alert({
        title: "Validacao",
        message
      });
      return;
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[ProcessSubsequentFieldsManagerV1]", message);
    }
  }

  function submitNative_v1(form) {
    HTMLFormElement.prototype.submit.call(form);
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
    const previousValue = toSafeString_v1(select.value).trim();

    select.innerHTML = "";

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = safeConfig.placeholder || "Selecione";
    select.appendChild(emptyOption);

    (Array.isArray(options) ? options : []).forEach(function (item) {
      const option = document.createElement("option");
      option.value = item.key || "";
      option.textContent = item.label || item.key || "";
      select.appendChild(option);
    });

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

    rebuildSelectOptions_v1(elements.triggerField, resolved.selectableOptions, {
      placeholder: "Selecione"
    });
    rebuildSelectOptions_v1(elements.subsequentField, resolved.selectableOptions, {
      placeholder: "Selecione"
    });

    if (manager && typeof manager.render === "function") {
      manager.render();
    }
  }

  function bindFieldOptionsRefresh_v1(form, elements, manager, optionCache) {
    if (!form || form.dataset.processSubsequentOptionsBoundV1 === "1") {
      return;
    }

    form.dataset.processSubsequentOptionsBoundV1 = "1";

    document.addEventListener("appverbo:configurable-items-change", function (event) {
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
      pageSize: form.querySelector("[data-process-subsequent-fields-page-size]"),
      pagination: form.querySelector("[data-process-subsequent-fields-pagination]")
    };
  }

  function hasRequiredElements_v1(elements) {
    return Boolean(
      elements &&
      elements.legacyContainer &&
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.triggerField &&
      elements.subsequentField &&
      elements.operator &&
      elements.triggerValue &&
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

  function syncHiddenInputs_v1(context) {
    const elements = context && context.elements ? context.elements : null;
    const items = context && Array.isArray(context.items) ? context.items : [];

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    elements.hiddenContainer.innerHTML = "";

    items.forEach(function (item) {
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

  //###################################################################################
  // (4) EDITOR SUPERIOR
  //###################################################################################

  function clearEditor_v1(context) {
    const elements = context && context.elements ? context.elements : context;

    if (!elements) {
      return;
    }

    elements.editorKey.value = "";
    elements.triggerField.value = "";
    elements.subsequentField.value = "";
    elements.operator.value = "equals";
    elements.triggerValue.value = "";
  }

  function loadEditorItem_v1(item, context) {
    const elements = context && context.elements ? context.elements : null;

    if (!item || !elements) {
      return;
    }

    elements.editorKey.value = item.key || "";
    elements.triggerField.value = item.triggerField || "";
    elements.subsequentField.value = item.fieldKey || "";
    elements.operator.value = item.operator || "equals";
    elements.triggerValue.value = item.triggerValue || "";
    elements.triggerField.focus();
  }

  function readEditorItem_v1(context) {
    const state = context && context.state ? context.state : {};
    const elements = context && context.elements ? context.elements : {};
    const triggerField = toSafeString_v1(elements.triggerField ? elements.triggerField.value : "").trim();
    const fieldKey = toSafeString_v1(elements.subsequentField ? elements.subsequentField.value : "").trim();
    const operator = toSafeString_v1(elements.operator ? elements.operator.value : "").trim() || "equals";
    const triggerValue = toSafeString_v1(elements.triggerValue ? elements.triggerValue.value : "").trim();
    const currentKey = toSafeString_v1(elements.editorKey ? elements.editorKey.value : "").trim();
    const key = currentKey || "sub_" + normalizeKey_v1(triggerField + "_" + fieldKey + "_" + operator + "_" + Date.now());

    return {
      managerId: toSafeString_v1(state.editingId).trim() || "tmp_" + Date.now(),
      key: key,
      triggerField: triggerField,
      fieldKey: fieldKey,
      operator: operator,
      triggerValue: triggerValue
    };
  }

  function validateItem_v1(item, context) {
    const items = context && Array.isArray(context.items) ? context.items : [];
    const editingId = context && context.state ? toSafeString_v1(context.state.editingId).trim() : "";

    if (!item.triggerField) {
      return {
        valid: false,
        message: "Selecione o campo acionador."
      };
    }

    if (!item.fieldKey) {
      return {
        valid: false,
        message: "Selecione o campo subsequente."
      };
    }

    const duplicate = items.some(function (existing) {
      const existingId = toSafeString_v1(existing.__managerId || existing.managerId).trim();
      return existingId !== editingId
        && existing.triggerField === item.triggerField
        && existing.fieldKey === item.fieldKey
        && existing.operator === item.operator
        && existing.triggerValue === item.triggerValue;
    });

    if (duplicate) {
      return {
        valid: false,
        message: "Ja existe uma regra igual criada."
      };
    }

    return { valid: true };
  }

  function hasDraft_v1(elements, manager) {
    return Boolean(
      (manager && manager.state && manager.state.editingId) ||
      toSafeString_v1(elements.triggerField.value).trim() ||
      toSafeString_v1(elements.subsequentField.value).trim() ||
      toSafeString_v1(elements.triggerValue.value).trim() ||
      toSafeString_v1(elements.operator.value).trim() !== "equals"
    );
  }

  //###################################################################################
  // (5) ACOES
  //###################################################################################

  function bindCancel_v1(form, elements, manager) {
    if (!form || !elements.cancelButton || form.dataset.processSubsequentCancelBoundV1 === "1") {
      return;
    }

    form.dataset.processSubsequentCancelBoundV1 = "1";
    elements.cancelButton.dataset.appverboCancel = "1";
    elements.cancelButton.dataset.appverboCancelLocal = "1";

    form.addEventListener("appverbo:cancelled", function (event) {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== elements.cancelButton) {
        return;
      }

      manager.clearEditing();
    });
  }

  function bindSubmit_v1(form, elements, manager) {
    if (!form || !elements.submitButton || form.dataset.processSubsequentSubmitBoundV1 === "1") {
      return;
    }

    form.dataset.processSubsequentSubmitBoundV1 = "1";

    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (hasDraft_v1(elements, manager)) {
        const item = readEditorItem_v1({
          manager: manager,
          elements: manager.elements,
          state: manager.state
        });
        const validationResult = validateItem_v1(item, {
          manager: manager,
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

    if (form.dataset.processSubsequentSubmitNativeBoundV1 === "1") {
      return;
    }

    form.dataset.processSubsequentSubmitNativeBoundV1 = "1";
    form.addEventListener("submit", function () {
      manager.syncHiddenInputs();
    });
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function setupProcessSubsequentFieldsManager_v1(form) {
    if (!form || form.dataset.processSubsequentFieldsManagerBoundV1 === "1") {
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

    form.dataset.processSubsequentFieldsManagerBoundV1 = "1";

    const optionCache = {
      staticOptions: snapshotSelectOptions_v1(elements.triggerField)
        .concat(snapshotSelectOptions_v1(elements.subsequentField))
    };
    const manager = core.createConfigurableItemsManager_v1({
      root: form,
      itemName: "campo subsequente",
      itemNamePlural: "campos subsequentes",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 20],
      initialItems: readInitialItems_v1(elements),
      selectors: {
        editorForm: "[data-process-subsequent-field-editor-block]",
        table: "[data-process-subsequent-fields-table]",
        tableBody: "[data-process-subsequent-fields-table-body]",
        emptyState: "[data-process-subsequent-fields-empty]",
        pagination: "[data-process-subsequent-fields-pagination]",
        pageSize: "[data-process-subsequent-fields-page-size]",
        hiddenContainer: "[data-process-subsequent-fields-hidden-container]",
        totalLabel: "[data-process-subsequent-fields-total-label]",
        searchInput: "[data-configurable-search]"
      },
      columns: [
        {
          key: "triggerField",
          label: "Campo acionador",
          render: function (item) {
            return getOptionLabel_v1(elements.triggerField, item.triggerField) || "-";
          }
        },
        {
          key: "fieldKey",
          label: "Campo subsequente",
          render: function (item) {
            return getOptionLabel_v1(elements.subsequentField, item.fieldKey) || "-";
          }
        },
        {
          key: "operator",
          label: "Condição",
          render: function (item) {
            return getOperatorLabel_v1(item.operator);
          }
        },
        {
          key: "triggerValue",
          label: "Valor acionador",
          render: function (item) {
            return item.triggerValue || "-";
          }
        }
      ],
      getItemId: function (item, index) {
        return item.managerId || item.__managerId || item.key || ("subsequent_" + (index + 1));
      },
      readEditorItem: readEditorItem_v1,
      loadEditorItem: loadEditorItem_v1,
      clearEditor: clearEditor_v1,
      validateItem: validateItem_v1,
      syncHiddenInputs: syncHiddenInputs_v1
    });

    if (!manager) {
      form.dataset.processSubsequentFieldsManagerBoundV1 = "";
      return null;
    }

    updateFieldOptions_v1(form, elements, manager, optionCache);
    bindFieldOptionsRefresh_v1(form, elements, manager, optionCache);
    bindCancel_v1(form, elements, manager);
    bindSubmit_v1(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function setupAllProcessSubsequentFieldsManagers_v1() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(setupProcessSubsequentFieldsManager_v1);
  }

  //###################################################################################
  // (7) BOOT
  //###################################################################################

  window.setupProcessSubsequentFieldsManagerV1 = setupAllProcessSubsequentFieldsManagers_v1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupAllProcessSubsequentFieldsManagers_v1);
  } else {
    setupAllProcessSubsequentFieldsManagers_v1();
  }
})(window, document);
