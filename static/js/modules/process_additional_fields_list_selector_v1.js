//###################################################################################
// APPGENESIS - PROCESS ADDITIONAL FIELDS LIST SELECTOR V1
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const ROOT_SELECTOR = '[data-process-additional-fields-manager-v3="1"]';
  const LIST_TYPE = "list";
  const MANUAL_SOURCE_TYPE = "manual";
  const EDITOR_TYPE_SELECTOR = "[data-additional-field-editor-type]";
  const EDITOR_LIST_VALUE_SELECTOR = "[data-additional-field-editor-manual-items]";
  const EDITOR_LIST_WRAP_SELECTOR = "[data-additional-field-list-wrap]";
  const EDITOR_SUBMIT_SELECTOR = "[data-additional-field-editor-submit]";
  const HIDDEN_SOURCE_SELECTORS = [
    "[data-additional-field-list-source-wrap]",
    "[data-additional-field-automatic-process-wrap]",
    "[data-additional-field-automatic-section-wrap]",
    "[data-additional-field-automatic-field-wrap]",
    "[data-additional-field-automatic-only-active-wrap]"
  ];

  //###################################################################################
  // (2) HELPERS
  //###################################################################################

  function toSafeString_v1(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeLookup_v1(value) {
    return toSafeString_v1(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeKey_v1(value) {
    return normalizeLookup_v1(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function normalizeStatus_v1(value) {
    const cleanStatus = normalizeLookup_v1(value);
    return cleanStatus === "inativo" || cleanStatus === "inactive" ? "inativo" : "ativo";
  }

  function showValidationMessage_v1(message) {
    const core = window.AppGenesisConfigurableItems || {};

    if (typeof core.showAlertDialog_v1 === "function") {
      core.showAlertDialog_v1({
        title: "Validação",
        message
      });
      return;
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[ProcessAdditionalFieldsListSelectorV1]", message);
    }
  }

  function parseJsonArray_v1(rawValue) {
    const cleanValue = toSafeString_v1(rawValue).trim();

    if (!cleanValue) {
      return [];
    }

    try {
      const parsedValue = JSON.parse(cleanValue);
      return Array.isArray(parsedValue) ? parsedValue : [];
    } catch (error) {
      return [];
    }
  }

  //###################################################################################
  // (3) CATÁLOGO DE LISTAS DO PROCESSO
  //###################################################################################

  function readProcessListsFromDataset_v1(root) {
    const sourceElement = root.querySelector("[data-process-lists]");
    return parseJsonArray_v1(sourceElement ? sourceElement.dataset.processLists : "");
  }

  function readProcessListsFromLegacyContainer_v1(root) {
    const settingsCard = root.closest("#settings-menu-edit-card") || document;
    const rows = Array.from(
      settingsCard.querySelectorAll("[data-process-lists-legacy-container] [data-process-list-row]")
    );

    return rows.map((row) => {
      const readValue = (name) => {
        const input = row.querySelector(`[name="${name}"]`);
        return input ? input.value : "";
      };

      return {
        key: readValue("process_list_key"),
        label: readValue("process_list_label"),
        status: readValue("process_list_status")
      };
    });
  }

  function buildProcessListsCatalog_v1(root) {
    const rawLists = readProcessListsFromDataset_v1(root);
    const sourceLists = rawLists.length ? rawLists : readProcessListsFromLegacyContainer_v1(root);
    const items = [];
    const byKey = new Map();
    const keyByLabel = new Map();

    sourceLists.forEach((rawList) => {
      if (!rawList || typeof rawList !== "object") {
        return;
      }

      const key = normalizeKey_v1(rawList.key || rawList.list_key || rawList.process_list_key);
      const label = toSafeString_v1(rawList.label || rawList.name || key).trim();

      if (!key || !label || byKey.has(key)) {
        return;
      }

      const item = {
        key,
        label,
        status: normalizeStatus_v1(rawList.status)
      };

      items.push(item);
      byKey.set(key, item);

      const normalizedLabel = normalizeLookup_v1(label);
      if (normalizedLabel && !keyByLabel.has(normalizedLabel)) {
        keyByLabel.set(normalizedLabel, key);
      }
    });

    return { items, byKey, keyByLabel };
  }

  //###################################################################################
  // (4) ESTADO DOS CAMPOS DO TIPO LISTA
  //###################################################################################

  function readInitialFieldListKeys_v1(root) {
    const fieldListKeys = new Map();
    const fieldTypes = new Map();
    const rows = Array.from(
      root.querySelectorAll("[data-additional-fields-legacy-container] .process-additional-field-row")
    );

    rows.forEach((row) => {
      const readValue = (name) => {
        const input = row.querySelector(`[name="${name}"]`);
        return input ? input.value : "";
      };

      const fieldKey = normalizeKey_v1(readValue("additional_field_key") || row.dataset.fieldKey);
      const fieldType = normalizeLookup_v1(readValue("additional_field_type"));
      const listSourceType = normalizeLookup_v1(
        readValue("additional_field_list_source_type") || MANUAL_SOURCE_TYPE
      );
      const listKey = normalizeKey_v1(
        readValue("additional_field_manual_list_key") || readValue("additional_field_list_key")
      );

      if (!fieldKey) {
        return;
      }

      fieldTypes.set(fieldKey, fieldType);

      if (fieldType === LIST_TYPE && listSourceType === MANUAL_SOURCE_TYPE && listKey) {
        fieldListKeys.set(fieldKey, listKey);
      }
    });

    return { fieldListKeys, fieldTypes };
  }

  function resolveListKeyFromValue_v1(value, catalog) {
    const cleanKey = normalizeKey_v1(value);

    if (cleanKey && catalog.byKey.has(cleanKey)) {
      return cleanKey;
    }

    return catalog.keyByLabel.get(normalizeLookup_v1(value)) || "";
  }

  function updateFieldListStateFromItems_v1(state, items) {
    (Array.isArray(items) ? items : []).forEach((item) => {
      if (!item || typeof item !== "object") {
        return;
      }

      const fieldKey = normalizeKey_v1(item.key || item.id || item.__managerId);
      const fieldType = normalizeLookup_v1(item.fieldType || item.field_type);

      if (!fieldKey) {
        return;
      }

      state.fieldTypes.set(fieldKey, fieldType);

      if (fieldType !== LIST_TYPE) {
        state.fieldListKeys.delete(fieldKey);
        return;
      }

      const listSourceType = normalizeLookup_v1(
        item.listSourceType || item.list_source_type || MANUAL_SOURCE_TYPE
      );

      if (listSourceType !== MANUAL_SOURCE_TYPE) {
        state.fieldListKeys.delete(fieldKey);
        return;
      }

      const selectedListKey =
        normalizeKey_v1(item.manualListKey || item.manual_list_key || item.listKey || item.list_key) ||
        resolveListKeyFromValue_v1(
          item.manualListItemsCsv || item.manual_list_items_csv || "",
          state.catalog
        );

      if (selectedListKey) {
        state.fieldListKeys.set(fieldKey, selectedListKey);
      }
    });
  }

  //###################################################################################
  // (5) EDITOR - CAMPO NOME DA LISTA
  //###################################################################################

  function appendListOption_v1(select, item) {
    const option = document.createElement("option");
    option.value = item.key;
    option.textContent = item.status === "inativo" ? `${item.label} (Inativa)` : item.label;
    select.appendChild(option);
  }

  function ensureUnavailableListOption_v1(select, listKey) {
    const cleanListKey = normalizeKey_v1(listKey);

    if (!cleanListKey) {
      return;
    }

    const optionExists = Array.from(select.options || []).some((option) => {
      return normalizeKey_v1(option.value) === cleanListKey;
    });

    if (optionExists) {
      return;
    }

    const option = document.createElement("option");
    option.value = cleanListKey;
    option.textContent = `Lista indisponível (${cleanListKey})`;
    option.dataset.appgenesisUnavailableList = "1";
    select.appendChild(option);
  }

  function createListSelect_v1(root, state) {
    const wrapper = root.querySelector(EDITOR_LIST_WRAP_SELECTOR);
    const currentField = root.querySelector(EDITOR_LIST_VALUE_SELECTOR);

    if (!wrapper || !currentField) {
      return null;
    }

    const label = wrapper.querySelector("label");
    if (label) {
      label.textContent = "Nome da Lista";
    }

    if (currentField.tagName === "SELECT") {
      currentField.setAttribute("data-additional-field-editor-list-key", "");
      return currentField;
    }

    const select = document.createElement("select");
    select.id = currentField.id || "process-additional-field-editor-list-key";
    select.className = currentField.className || "";
    select.setAttribute("data-additional-field-editor-manual-items", "");
    select.setAttribute("data-additional-field-editor-list-key", "");
    select.setAttribute("aria-label", "Nome da Lista");

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = state.catalog.items.length
      ? "Selecione a lista"
      : "Nenhuma lista criada na aba Listas";
    select.appendChild(placeholder);

    state.catalog.items.forEach((item) => appendListOption_v1(select, item));
    currentField.replaceWith(select);

    return select;
  }

  function forceManualListSource_v1(root) {
    const sourceSelect = root.querySelector("[data-additional-field-editor-list-source-type]");

    if (sourceSelect) {
      sourceSelect.value = MANUAL_SOURCE_TYPE;
    }
  }

  function updateEditorVisibility_v1(root, state) {
    const typeSelect = root.querySelector(EDITOR_TYPE_SELECTOR);
    const listWrapper = root.querySelector(EDITOR_LIST_WRAP_SELECTOR);
    const isListField = normalizeLookup_v1(typeSelect ? typeSelect.value : "") === LIST_TYPE;

    HIDDEN_SOURCE_SELECTORS.forEach((selector) => {
      const element = root.querySelector(selector);
      if (!element) {
        return;
      }
      element.hidden = true;
      element.style.display = "none";
    });

    if (listWrapper) {
      listWrapper.hidden = !isListField;
      listWrapper.style.display = isListField ? "" : "none";
    }

    if (state.listSelect) {
      state.listSelect.disabled = !isListField || state.catalog.items.length === 0;
      if (!isListField) {
        state.listSelect.value = "";
      }
    }

    if (isListField) {
      forceManualListSource_v1(root);
    }
  }

  function loadEditorListValue_v1(state, fieldKey) {
    if (!state.listSelect) {
      return;
    }

    const cleanFieldKey = normalizeKey_v1(fieldKey);
    const listKey = state.fieldListKeys.get(cleanFieldKey) || "";

    if (listKey) {
      ensureUnavailableListOption_v1(state.listSelect, listKey);
    }

    state.listSelect.value = listKey;
  }

  //###################################################################################
  // (6) TABELA DOS CAMPOS ADICIONAIS
  //###################################################################################

  function getListDisplayLabel_v1(state, listKey) {
    const cleanListKey = normalizeKey_v1(listKey);
    const item = state.catalog.byKey.get(cleanListKey);

    if (!item) {
      return cleanListKey ? `Lista indisponível (${cleanListKey})` : "-";
    }

    return item.status === "inativo" ? `${item.label} (Inativa)` : item.label;
  }

  function renderListSummaries_v1(root, state) {
    const rows = Array.from(
      root.querySelectorAll("[data-configurable-table-body] tr[data-configurable-item-id]")
    );

    rows.forEach((row) => {
      const fieldKey = normalizeKey_v1(row.dataset.configurableItemId);
      const listKey = state.fieldListKeys.get(fieldKey);

      if (!listKey || state.fieldTypes.get(fieldKey) !== LIST_TYPE) {
        return;
      }

      const cells = row.querySelectorAll("td");
      const listSourceCell = cells.length >= 5 ? cells[4] : null;
      const displayValue = getListDisplayLabel_v1(state, listKey);

      if (listSourceCell && listSourceCell.textContent !== displayValue) {
        listSourceCell.textContent = displayValue;
      }
    });
  }

  function scheduleListSummariesRender_v1(root, state) {
    if (state.renderScheduled) {
      return;
    }

    state.renderScheduled = true;
    window.requestAnimationFrame(() => {
      state.renderScheduled = false;
      renderListSummaries_v1(root, state);
    });
  }

  //###################################################################################
  // (7) PAYLOAD PARA O BACKEND
  //###################################################################################

  function getNamedInputs_v1(container, name) {
    return Array.from(container.querySelectorAll(`[name="${name}"]`));
  }

  function rewriteHiddenListReferences_v1(root, state) {
    const hiddenContainer = root.querySelector("[data-additional-fields-hidden-container]");

    if (!hiddenContainer) {
      return;
    }

    const fieldKeys = getNamedInputs_v1(hiddenContainer, "additional_field_key");
    const fieldTypes = getNamedInputs_v1(hiddenContainer, "additional_field_type");
    const listKeys = getNamedInputs_v1(hiddenContainer, "additional_field_list_key");
    const listSourceTypes = getNamedInputs_v1(hiddenContainer, "additional_field_list_source_type");
    const manualListKeys = getNamedInputs_v1(hiddenContainer, "additional_field_manual_list_key");
    const manualItems = getNamedInputs_v1(hiddenContainer, "additional_field_manual_list_items");
    const automaticProcessKeys = getNamedInputs_v1(
      hiddenContainer,
      "additional_field_automatic_source_process_key"
    );
    const automaticSectionKeys = getNamedInputs_v1(
      hiddenContainer,
      "additional_field_automatic_source_section_key"
    );
    const automaticFieldKeys = getNamedInputs_v1(
      hiddenContainer,
      "additional_field_automatic_source_field_key"
    );
    const automaticOnlyActiveValues = getNamedInputs_v1(
      hiddenContainer,
      "additional_field_automatic_only_active"
    );

    fieldKeys.forEach((fieldKeyInput, index) => {
      const fieldKey = normalizeKey_v1(fieldKeyInput.value);
      const fieldType = normalizeLookup_v1(fieldTypes[index] ? fieldTypes[index].value : "");

      if (!fieldKey || fieldType !== LIST_TYPE) {
        return;
      }

      const manualItemValue = manualItems[index] ? manualItems[index].value : "";
      const selectedListKey =
        state.fieldListKeys.get(fieldKey) ||
        resolveListKeyFromValue_v1(manualItemValue, state.catalog);

      if (!selectedListKey) {
        return;
      }

      state.fieldListKeys.set(fieldKey, selectedListKey);
      state.fieldTypes.set(fieldKey, LIST_TYPE);

      if (listKeys[index]) listKeys[index].value = selectedListKey;
      if (manualListKeys[index]) manualListKeys[index].value = selectedListKey;
      if (listSourceTypes[index]) listSourceTypes[index].value = MANUAL_SOURCE_TYPE;
      if (manualItems[index]) manualItems[index].value = "";
      if (automaticProcessKeys[index]) automaticProcessKeys[index].value = "";
      if (automaticSectionKeys[index]) automaticSectionKeys[index].value = "";
      if (automaticFieldKeys[index]) automaticFieldKeys[index].value = "";
      if (automaticOnlyActiveValues[index]) automaticOnlyActiveValues[index].value = "";
    });
  }

  function validateListSelectionBeforeSubmit_v1(event, root, state) {
    const submitButton = root.querySelector(EDITOR_SUBMIT_SELECTOR);
    const submitter = event.submitter || document.activeElement;

    if (submitter && submitButton && submitter !== submitButton) {
      return;
    }

    const typeSelect = root.querySelector(EDITOR_TYPE_SELECTOR);
    const isListField = normalizeLookup_v1(typeSelect ? typeSelect.value : "") === LIST_TYPE;

    if (!isListField) {
      return;
    }

    const selectedListKey = normalizeKey_v1(state.listSelect ? state.listSelect.value : "");

    if (selectedListKey) {
      return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();
    showValidationMessage_v1(
      state.catalog.items.length
        ? "Selecione o Nome da Lista."
        : "Crie primeiro uma lista na aba Listas e depois selecione-a neste campo."
    );
  }

  //###################################################################################
  // (8) EVENTOS
  //###################################################################################

  function bindEditorEvents_v1(root, state) {
    const typeSelect = root.querySelector(EDITOR_TYPE_SELECTOR);
    const form = root.closest("form") || root;

    if (typeSelect) {
      typeSelect.addEventListener("change", () => {
        window.setTimeout(() => updateEditorVisibility_v1(root, state), 0);
      });
    }

    root.addEventListener("appgenesis:configurable-items-change", (event) => {
      const detail = event && event.detail ? event.detail : {};
      updateFieldListStateFromItems_v1(state, detail.items);
      scheduleListSummariesRender_v1(root, state);
    });

    document.addEventListener("click", (event) => {
      const editButton = event.target.closest(
        '[data-configurable-action="edit"][data-configurable-item-id]'
      );

      if (editButton && root.contains(editButton)) {
        const fieldKey = editButton.dataset.configurableItemId;
        window.setTimeout(() => {
          loadEditorListValue_v1(state, fieldKey);
          updateEditorVisibility_v1(root, state);
        }, 0);
        return;
      }

      const createButton = event.target.closest("[data-configurable-create-trigger]");
      if (createButton) {
        const targetSelector = toSafeString_v1(createButton.dataset.configurableManagerTarget).trim();
        if (targetSelector && document.querySelector(targetSelector) === root) {
          window.setTimeout(() => {
            if (state.listSelect) state.listSelect.value = "";
            updateEditorVisibility_v1(root, state);
          }, 0);
        }
      }
    });

    root.addEventListener("appgenesis:cancelled", () => {
      window.setTimeout(() => {
        if (state.listSelect) state.listSelect.value = "";
        updateEditorVisibility_v1(root, state);
      }, 0);
    });

    if (form && form.dataset.additionalFieldListSelectorBoundV1 !== "1") {
      form.dataset.additionalFieldListSelectorBoundV1 = "1";

      form.addEventListener(
        "submit",
        (event) => validateListSelectionBeforeSubmit_v1(event, root, state),
        true
      );

      form.addEventListener("submit", (event) => {
        if (event.defaultPrevented) {
          return;
        }
        rewriteHiddenListReferences_v1(root, state);
      });
    }

    const tableBody = root.querySelector("[data-configurable-table-body]");
    if (tableBody && typeof window.MutationObserver === "function") {
      const observer = new MutationObserver(() => {
        scheduleListSummariesRender_v1(root, state);
      });
      observer.observe(tableBody, { childList: true });
    }
  }

  //###################################################################################
  // (9) INICIALIZACAO
  //###################################################################################

  function setupOneProcessAdditionalFieldsListSelectorV1_v1(root) {
    if (!root || root.dataset.additionalFieldListSelectorReadyV1 === "1") {
      return null;
    }

    const initialState = readInitialFieldListKeys_v1(root);
    const state = {
      catalog: buildProcessListsCatalog_v1(root),
      fieldListKeys: initialState.fieldListKeys,
      fieldTypes: initialState.fieldTypes,
      listSelect: null,
      renderScheduled: false
    };

    state.listSelect = createListSelect_v1(root, state);

    if (!state.listSelect) {
      return null;
    }

    root.dataset.additionalFieldListSelectorReadyV1 = "1";
    forceManualListSource_v1(root);
    updateEditorVisibility_v1(root, state);
    bindEditorEvents_v1(root, state);
    scheduleListSummariesRender_v1(root, state);

    return state;
  }

  function setupProcessAdditionalFieldsListSelectorV1() {
    return Array.from(document.querySelectorAll(ROOT_SELECTOR))
      .map((root) => setupOneProcessAdditionalFieldsListSelectorV1_v1(root))
      .filter(Boolean);
  }

  window.setupProcessAdditionalFieldsListSelectorV1 = setupProcessAdditionalFieldsListSelectorV1;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupProcessAdditionalFieldsListSelectorV1);
  } else {
    setupProcessAdditionalFieldsListSelectorV1();
  }
})(window, document);
