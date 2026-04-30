//###################################################################################
// APPVERBOBRAGA - PROCESS ADDITIONAL FIELDS MANAGER V3
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const ROOT_SELECTOR = "[data-process-additional-fields-manager-v3]";
  const SUPPORTED_TYPES = new Set(["text", "number", "email", "phone", "date", "flag", "header", "list"]);
  const TEXTUAL_TYPES = new Set(["text", "number", "email", "phone"]);

  const TYPE_LABELS = {
    text: "Texto",
    number: "Numero",
    email: "Email",
    phone: "Telefone",
    date: "Data",
    flag: "Sim/Nao",
    header: "Cabecalho",
    list: "Lista"
  };

  //###################################################################################
  // (2) HELPERS GERAIS
  //###################################################################################

  function toSafeString_v3(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeLookup_v3(value) {
    const core = window.AppVerboConfigurableItems || {};

    if (typeof core.normalizeLookup_v1 === "function") {
      return core.normalizeLookup_v1(value);
    }

    return toSafeString_v3(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeFieldType_v3(value) {
    const cleanType = normalizeLookup_v3(value).replace(/_/g, "-");

    if (SUPPORTED_TYPES.has(cleanType)) {
      return cleanType;
    }

    return "text";
  }

  function normalizeFieldKey_v3(value) {
    let cleanKey = normalizeLookup_v3(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");

    if (!cleanKey) {
      return "";
    }

    if (!cleanKey.startsWith("custom_")) {
      cleanKey = `custom_${cleanKey}`;
    }

    return cleanKey;
  }

  function normalizeListKey_v3(value) {
    return normalizeLookup_v3(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function normalizeRequired_v3(value) {
    if (typeof value === "boolean") {
      return value;
    }

    return ["1", "true", "sim", "yes", "on"].includes(normalizeLookup_v3(value));
  }

  function normalizeSize_v3(value, fieldType) {
    if (!TEXTUAL_TYPES.has(fieldType)) {
      return "";
    }

    const parsedSize = Number.parseInt(toSafeString_v3(value).trim(), 10);

    if (!Number.isFinite(parsedSize)) {
      return "255";
    }

    return String(Math.min(255, Math.max(1, parsedSize)));
  }

  function getFieldTypeLabel_v3(fieldType) {
    return TYPE_LABELS[normalizeFieldType_v3(fieldType)] || "Texto";
  }

  function getInputValue_v3(root, selector) {
    const element = root.querySelector(selector);

    if (!element) {
      return "";
    }

    if (element.type === "checkbox") {
      return element.checked ? "1" : "";
    }

    return toSafeString_v3(element.value);
  }

  function setInputValue_v3(root, selector, value) {
    const element = root.querySelector(selector);

    if (!element) {
      return;
    }

    if (element.type === "checkbox") {
      element.checked = normalizeRequired_v3(value);
      return;
    }

    element.value = toSafeString_v3(value);
  }

  function createHiddenInput_v3(name, value) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = toSafeString_v3(value);
    return input;
  }

  function getEditorRoot_v3(root) {
    return (
      root.querySelector("[data-additional-field-editor-block]") ||
      root.querySelector("[data-additional-field-editor-form]") ||
      root
    );
  }

  function getHiddenContainer_v3(root) {
    return root.querySelector("[data-additional-fields-hidden-container]");
  }

  function getLegacyContainer_v3(root) {
    return (
      root.querySelector("[data-additional-fields-legacy-container]") ||
      root.querySelector("[data-additional-fields-legacy]") ||
      root
    );
  }

  function getListLabelByKey_v3(root, listKey) {
    const cleanListKey = normalizeListKey_v3(listKey);

    if (!cleanListKey) {
      return "-";
    }

    const options = Array.from(
      root.querySelectorAll("[data-additional-field-editor-list-key] option")
    );

    const matchedOption = options.find((option) => {
      return normalizeListKey_v3(option.value) === cleanListKey;
    });

    if (matchedOption) {
      return matchedOption.textContent || cleanListKey;
    }

    return cleanListKey;
  }

  //###################################################################################
  // (3) LER CAMPOS EXISTENTES
  //###################################################################################

  function getLegacyValues_v3(container, name) {
    return Array.from(container.querySelectorAll(`[name="${name}"]`)).map((element) => {
      if (element.type === "checkbox") {
        return element.checked ? "1" : "";
      }

      return toSafeString_v3(element.value);
    });
  }

  function readLegacyAdditionalFields_v3(root) {
    const container = getLegacyContainer_v3(root);

    if (!container) {
      return [];
    }

    const keys = getLegacyValues_v3(container, "additional_field_key");
    const labels = getLegacyValues_v3(container, "additional_field_label");
    const types = getLegacyValues_v3(container, "additional_field_type");
    const requiredValues = getLegacyValues_v3(container, "additional_field_required");
    const sizes = getLegacyValues_v3(container, "additional_field_size");
    const listKeys = getLegacyValues_v3(container, "additional_field_list_key");

    const rowsCount = Math.max(
      keys.length,
      labels.length,
      types.length,
      requiredValues.length,
      sizes.length,
      listKeys.length
    );

    const items = [];

    for (let index = 0; index < rowsCount; index += 1) {
      const fieldType = normalizeFieldType_v3(types[index] || "text");
      const key = normalizeFieldKey_v3(keys[index] || labels[index] || "");

      if (!key && !labels[index]) {
        continue;
      }

      items.push({
        id: key || `custom_field_${index + 1}`,
        key,
        label: toSafeString_v3(labels[index] || key),
        fieldType,
        isRequired: fieldType === "header" ? false : normalizeRequired_v3(requiredValues[index]),
        size: normalizeSize_v3(sizes[index], fieldType),
        listKey: fieldType === "list" ? normalizeListKey_v3(listKeys[index]) : "",
        order: index + 1
      });
    }

    return items;
  }

  //###################################################################################
  // (4) EDITOR
  //###################################################################################

  function clearEditor_v3(context) {
    const root = context.root;
    const editor = getEditorRoot_v3(root);

    setInputValue_v3(editor, "[data-additional-field-editor-key]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-label]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-type]", "text");
    setInputValue_v3(editor, "[data-additional-field-editor-size]", "255");
    setInputValue_v3(editor, "[data-additional-field-editor-required]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-list-key]", "");

    updateEditorVisibility_v3(root);

    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");

    if (submitButton) {
      submitButton.textContent = "Guardar";
    }
  }

  function loadEditorItem_v3(item, context) {
    const root = context.root;
    const editor = getEditorRoot_v3(root);

    setInputValue_v3(editor, "[data-additional-field-editor-key]", item.key || "");
    setInputValue_v3(editor, "[data-additional-field-editor-label]", item.label || "");
    setInputValue_v3(editor, "[data-additional-field-editor-type]", item.fieldType || "text");
    setInputValue_v3(editor, "[data-additional-field-editor-size]", item.size || "");
    setInputValue_v3(editor, "[data-additional-field-editor-required]", item.isRequired ? "1" : "");
    setInputValue_v3(editor, "[data-additional-field-editor-list-key]", item.listKey || "");

    updateEditorVisibility_v3(root);

    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");

    if (submitButton) {
      submitButton.textContent = "Guardar";
    }
  }

  function readEditorItem_v3(context) {
    const root = context.root;
    const editor = getEditorRoot_v3(root);

    const label = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-label]")).trim();
    const rawKey = getInputValue_v3(editor, "[data-additional-field-editor-key]") || label;
    const fieldType = normalizeFieldType_v3(getInputValue_v3(editor, "[data-additional-field-editor-type]"));
    const key = normalizeFieldKey_v3(rawKey);

    return {
      id: key,
      key,
      label,
      fieldType,
      isRequired: fieldType === "header"
        ? false
        : normalizeRequired_v3(getInputValue_v3(editor, "[data-additional-field-editor-required]")),
      size: normalizeSize_v3(getInputValue_v3(editor, "[data-additional-field-editor-size]"), fieldType),
      listKey: fieldType === "list"
        ? normalizeListKey_v3(getInputValue_v3(editor, "[data-additional-field-editor-list-key]"))
        : ""
    };
  }

  function validateEditorItem_v3(item, context) {
    const editingId = toSafeString_v3(context.state.editingId);

    if (!item.label) {
      return { valid: false, message: "Informe o nome do campo." };
    }

    if (!item.key) {
      return { valid: false, message: "Informe a chave do campo." };
    }

    if (item.fieldType === "list" && !item.listKey) {
      return { valid: false, message: "Selecione a lista associada ao campo." };
    }

    const duplicated = context.items.some((existingItem) => {
      const sameKey = normalizeLookup_v3(existingItem.key) === normalizeLookup_v3(item.key);
      const sameId = toSafeString_v3(existingItem.__managerId) === editingId;
      return sameKey && !sameId;
    });

    if (duplicated) {
      return { valid: false, message: "Ja existe um campo com esta chave." };
    }

    return { valid: true };
  }

  function updateEditorVisibility_v3(root) {
    const editor = getEditorRoot_v3(root);
    const fieldType = normalizeFieldType_v3(getInputValue_v3(editor, "[data-additional-field-editor-type]"));
    const sizeWrap = editor.querySelector("[data-additional-field-size-wrap]");
    const listWrap = editor.querySelector("[data-additional-field-list-wrap]");
    const requiredWrap = editor.querySelector("[data-additional-field-required-wrap]");

    if (sizeWrap) {
      sizeWrap.style.display = TEXTUAL_TYPES.has(fieldType) ? "" : "none";
    }

    if (listWrap) {
      listWrap.style.display = fieldType === "list" ? "" : "none";
    }

    if (requiredWrap) {
      requiredWrap.style.display = fieldType === "header" ? "none" : "";
    }
  }

  function submitEditorItem_v3(root, manager) {
    const item = readEditorItem_v3({
      manager,
      root,
      elements: manager.elements,
      state: manager.state
    });

    const validationResult = validateEditorItem_v3(item, {
      manager,
      root,
      elements: manager.elements,
      state: manager.state,
      items: manager.getItems()
    });

    if (validationResult && validationResult.valid === false) {
      if (validationResult.message) {
        window.alert(validationResult.message);
      }

      return;
    }

    manager.addOrUpdate(item);
  }

  function bindEditorExtras_v3(root, manager) {
    if (root.dataset.additionalFieldsExtrasBoundV3 === "1") {
      return;
    }

    root.dataset.additionalFieldsExtrasBoundV3 = "1";

    const editor = getEditorRoot_v3(root);
    const typeSelect = editor.querySelector("[data-additional-field-editor-type]");
    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");
    const cancelButton = editor.querySelector("[data-additional-field-editor-cancel]");

    if (typeSelect) {
      typeSelect.addEventListener("change", () => updateEditorVisibility_v3(root));
    }

    if (submitButton) {
      submitButton.addEventListener("click", (event) => {
        event.preventDefault();
        submitEditorItem_v3(root, manager);
      });
    }

    if (cancelButton) {
      cancelButton.addEventListener("click", (event) => {
        event.preventDefault();
        manager.clearEditing();
        clearEditor_v3({ root });
      });
    }

    updateEditorVisibility_v3(root);
  }

  //###################################################################################
  // (5) SINCRONIZAR INPUTS PARA O BACKEND
  //###################################################################################

  function syncHiddenInputs_v3(context) {
    const root = context.root;
    const hiddenContainer = getHiddenContainer_v3(root);

    if (!hiddenContainer) {
      return;
    }

    hiddenContainer.innerHTML = "";

    context.items.forEach((item) => {
      const fieldType = normalizeFieldType_v3(item.fieldType);

      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_key", item.key || ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_label", item.label || ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_type", fieldType));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_required", item.isRequired ? "1" : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_size", normalizeSize_v3(item.size, fieldType)));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_list_key", fieldType === "list" ? item.listKey || "" : ""));
    });
  }


// APPVERBO_ADDITIONAL_FIELDS_SAVE_FROM_TOP_V4_START

  //###################################################################################
  // (8) EDITOR SUPERIOR - GUARDAR E SUBMIT PELO BLOCO DE CIMA
  //###################################################################################

  function setEditorSubmitLabel_v4(root) {
    const editor = getEditorRoot_v3(root);
    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");

    if (submitButton) {
      submitButton.textContent = "Guardar";
    }
  }

  function clearEditor_v4(context) {
    clearEditor_v3(context);
    setEditorSubmitLabel_v4(context.root);
  }

  function loadEditorItem_v4(item, context) {
    loadEditorItem_v3(item, context);
    setEditorSubmitLabel_v4(context.root);
  }

  function hasEditorDraft_v4(root, manager) {
    const editor = getEditorRoot_v3(root);
    const label = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-label]")).trim();
    const fieldType = normalizeFieldType_v3(getInputValue_v3(editor, "[data-additional-field-editor-type]"));
    const size = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-size]")).trim();
    const listKey = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-list-key]")).trim();
    const isRequired = normalizeRequired_v3(getInputValue_v3(editor, "[data-additional-field-editor-required]"));

    if (manager && manager.state && manager.state.editingId) {
      return true;
    }

    return Boolean(
      label ||
      listKey ||
      isRequired ||
      fieldType !== "text" ||
      (size && size !== "255" && size !== "30")
    );
  }

  function submitAdditionalFieldsForm_v4(root, manager) {
    const parentForm = root.closest("form");

    if (manager && typeof manager.syncHiddenInputs === "function") {
      manager.syncHiddenInputs();
    }

    if (!parentForm) {
      return;
    }

    if (typeof parentForm.requestSubmit === "function") {
      parentForm.requestSubmit();
      return;
    }

    parentForm.submit();
  }

  function submitEditorItem_v4(root, manager) {
    if (hasEditorDraft_v4(root, manager)) {
      const item = readEditorItem_v3({
        manager,
        root,
        elements: manager.elements,
        state: manager.state
      });

      const validationResult = validateEditorItem_v3(item, {
        manager,
        root,
        elements: manager.elements,
        state: manager.state,
        items: manager.getItems()
      });

      if (validationResult && validationResult.valid === false) {
        if (validationResult.message) {
          window.alert(validationResult.message);
        }

        return;
      }

      manager.addOrUpdate(item);
    }

    submitAdditionalFieldsForm_v4(root, manager);
  }

  function bindEditorExtras_v4(root, manager) {
    if (root.dataset.additionalFieldsExtrasBoundV4 === "1") {
      return;
    }

    root.dataset.additionalFieldsExtrasBoundV4 = "1";

    const editor = getEditorRoot_v3(root);
    const typeSelect = editor.querySelector("[data-additional-field-editor-type]");
    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");
    const cancelButton = editor.querySelector("[data-additional-field-editor-cancel]");

    if (typeSelect) {
      typeSelect.addEventListener("change", () => updateEditorVisibility_v3(root));
    }

    if (submitButton) {
      submitButton.textContent = "Guardar";
      submitButton.addEventListener("click", (event) => {
        event.preventDefault();
        submitEditorItem_v4(root, manager);
      });
    }

    if (cancelButton) {
      cancelButton.textContent = "Cancelar";
      cancelButton.addEventListener("click", (event) => {
        event.preventDefault();
        manager.clearEditing();
        clearEditor_v4({ root });
      });
    }

    updateEditorVisibility_v3(root);
  }

// APPVERBO_ADDITIONAL_FIELDS_SAVE_FROM_TOP_V4_END

  //###################################################################################
  // (6) CRIAR MANAGER
  //###################################################################################

  function setupOneProcessAdditionalFieldsManagerV3_v3(root) {
    if (!root || root.dataset.additionalFieldsManagerReadyV3 === "1") {
      return null;
    }

    const core = window.AppVerboConfigurableItems || {};

    if (typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const initialItems = readLegacyAdditionalFields_v3(root);

    const manager = core.createConfigurableItemsManager_v1({
      root,
      itemName: "campo",
      itemNamePlural: "campos",
      pageSizeDefault: 5,
      pageSizeOptions: [5, 10, 25],
      initialItems,
      selectors: {
        editorForm: "[data-additional-field-editor-block]",
        table: "[data-configurable-table]",
        tableBody: "[data-configurable-table-body]",
        emptyState: "[data-configurable-empty]",
        pagination: "[data-configurable-pagination]",
        pageSize: "[data-configurable-page-size]",
        hiddenContainer: "[data-additional-fields-hidden-container]",
        totalLabel: "[data-configurable-total-label]"
      },
      columns: [
        {
          key: "label",
          label: "Nome do campo adicional"
        },
        {
          key: "fieldType",
          label: "Tipo do campo",
          render: function (item) {
            return getFieldTypeLabel_v3(item.fieldType);
          }
        },
        {
          key: "isRequired",
          label: "Obrigatorio",
          render: function (item) {
            return item.isRequired ? "Sim" : "Nao";
          }
        },
        {
          key: "size",
          label: "Tamanho",
          render: function (item) {
            return item.size || "-";
          }
        },
        {
          key: "listKey",
          label: "Lista",
          render: function (item) {
            return item.fieldType === "list" ? getListLabelByKey_v3(root, item.listKey) : "-";
          }
        }
      ],
      getItemId: function (item, index) {
        return item.key || item.id || `custom_field_${index + 1}`;
      },
      readEditorItem: readEditorItem_v3,
      loadEditorItem: loadEditorItem_v4,
      clearEditor: clearEditor_v4,
      validateItem: validateEditorItem_v3,
      syncHiddenInputs: syncHiddenInputs_v3
    });

    if (!manager) {
      return null;
    }

    root.dataset.additionalFieldsManagerReadyV3 = "1";
    bindEditorExtras_v4(root, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function setupProcessAdditionalFieldsManagerV3() {
    const roots = Array.from(document.querySelectorAll(ROOT_SELECTOR));

    if (!roots.length) {
      return [];
    }

    return roots
      .map((root) => setupOneProcessAdditionalFieldsManagerV3_v3(root))
      .filter(Boolean);
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  window.setupProcessAdditionalFieldsManagerV3 = setupProcessAdditionalFieldsManagerV3;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupProcessAdditionalFieldsManagerV3);
  } else {
    setupProcessAdditionalFieldsManagerV3();
  }
})(window, document);
