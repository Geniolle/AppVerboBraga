//###################################################################################
// APPGENESIS - PROCESS ADDITIONAL FIELDS MANAGER V3
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const ROOT_SELECTOR = "[data-process-additional-fields-manager-v3]";
  const SUPPORTED_TYPES = new Set(["text", "number", "email", "phone", "date", "time", "flag", "header", "list"]);
  const TEXTUAL_TYPES = new Set(["text", "number", "email", "phone"]);

  const TYPE_LABELS = {
    text: "Texto",
    number: "Numero",
    email: "Email",
    phone: "Telefone",
    date: "Data",
    time: "Horário",
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
    const core = window.AppGenesisConfigurableItems || {};

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

  function getFieldGroup_v3(fieldType) {
    return normalizeFieldType_v3(fieldType) === "header" ? "header" : "field";
  }

  function buildGroupScopedFieldKey_v3(label, fieldType) {
    return normalizeFieldKey_v3(`${getFieldGroup_v3(fieldType)}_${label}`);
  }

  function normalizeListKey_v3(value) {
    return normalizeLookup_v3(value)
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function normalizeListSourceType_v3(value) {
    const clean = normalizeLookup_v3(value);
    if (clean === "automatic" || clean === "field_list" || clean === "active_menus" || clean === "profile_menu_tabs") return clean;
    return "manual";
  }

  function getProcessListsSourceElement_v3(root) {
    if (!root) {
      return null;
    }

    if (typeof root.matches === "function" && root.matches("[data-process-lists]")) {
      return root;
    }

    return root.querySelector("[data-process-lists]");
  }

  function readProcessListsPayload_v3(root) {
    const sourceElement = getProcessListsSourceElement_v3(root);

    if (!sourceElement) {
      return [];
    }

    const rawText = toSafeString_v3(sourceElement.dataset ? sourceElement.dataset.processLists : sourceElement.getAttribute("data-process-lists")).trim();

    if (!rawText) {
      return [];
    }

    try {
      const parsed = JSON.parse(rawText);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      if (window.console && typeof window.console.warn === "function") {
        window.console.warn("[ProcessAdditionalFieldsManagerV3] lista de processos invalida", error);
      }
      return [];
    }
  }

  function getProcessListOptions_v3(root) {
    const parsed = readProcessListsPayload_v3(root);
    const options = [];
    const seenKeys = new Set();

    parsed.forEach((rawItem) => {
      if (!rawItem || typeof rawItem !== "object") {
        return;
      }

      const key = normalizeListKey_v3(
        rawItem.key || rawItem.list_key || rawItem.process_list_key || rawItem.manual_list_key
      );
      const baseLabel = toSafeString_v3(
        rawItem.label || rawItem.name || rawItem.list_label || rawItem.process_list_label || rawItem.key
      ).trim();
      const statusLookup = toSafeString_v3(rawItem.status || "").trim().toLowerCase();
      const isActive = rawItem.is_active !== undefined
        ? Boolean(rawItem.is_active)
        : !["inativo", "inactive", "0", "false"].includes(statusLookup);
      const label = baseLabel ? (isActive ? baseLabel : `${baseLabel} (Inativa)`) : "";

      if (!key || !label || seenKeys.has(key)) {
        return;
      }

      seenKeys.add(key);
      options.push({ key, label, isActive });
    });

    return options;
  }

  function refreshProcessListOptions_v3(root, selectedValue) {
    const editor = getEditorRoot_v3(root);
    const listSelect = editor.querySelector("[data-additional-field-editor-list-key]");

    if (!listSelect) {
      return;
    }

    const selectedKey = normalizeListKey_v3(selectedValue);
    const options = getProcessListOptions_v3(root);
    const matchedOption = selectedKey
      ? options.find((option) => normalizeListKey_v3(option.key) === selectedKey)
      : null;

    listSelect.innerHTML = "";

    if (!options.length) {
      const option = document.createElement("option");
      option.value = selectedKey || "";
      option.textContent = selectedKey ? "Lista não encontrada" : "Nenhuma lista criada";
      option.disabled = !selectedKey;
      option.selected = true;
      listSelect.appendChild(option);
      listSelect.disabled = !selectedKey;
      listSelect.value = selectedKey || "";
      return;
    }

    const placeholderOption = document.createElement("option");
    placeholderOption.value = "";
    placeholderOption.textContent = "Selecione a lista";
    listSelect.appendChild(placeholderOption);

    options.forEach((option) => {
      const optionElement = document.createElement("option");
      optionElement.value = option.key;
      optionElement.textContent = option.label;
      listSelect.appendChild(optionElement);
    });

    let hasSelectedOption = Boolean(matchedOption);

    if (selectedKey && !matchedOption) {
      const option = document.createElement("option");
      option.value = selectedKey;
      option.textContent = "Lista não encontrada";
      option.selected = true;
      listSelect.appendChild(option);
      hasSelectedOption = true;
    }

    listSelect.disabled = false;
    listSelect.value = hasSelectedOption ? selectedKey : "";
  }

  function normalizeRequired_v3(value) {
    if (typeof value === "boolean") {
      return value;
    }

    return ["1", "true", "sim", "yes", "on"].includes(normalizeLookup_v3(value));
  }

  function showValidationMessage_v3(message) {
    const core = window.AppGenesisConfigurableItems || {};

    if (typeof core.showAlertDialog_v1 === "function") {
      core.showAlertDialog_v1({
        title: "Validacao",
        message
      });
      return;
    }

    if (window.console && typeof window.console.warn === "function") {
      window.console.warn("[ProcessAdditionalFieldsManagerV3]", message);
    }
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

  function getProcessFieldResolver_v3() {
    return window.AppGenesisProcessFieldOptionsResolverV1 || {};
  }

  function ensureSelectOption_v3(select, value, label) {
    if (!select) {
      return;
    }

    const cleanValue = toSafeString_v3(value).trim();
    if (!cleanValue) {
      return;
    }

    const matchedOption = Array.from(select.options || []).find((option) => {
      return toSafeString_v3(option.value).trim() === cleanValue;
    });

    if (matchedOption) {
      return;
    }

    const option = document.createElement("option");
    option.value = cleanValue;
    option.textContent = toSafeString_v3(label).trim() || cleanValue;
    option.dataset.appgenesisInjectedOption = "1";
    select.appendChild(option);
  }

  function replaceSelectOptions_v3(select, options, placeholder) {
    if (!select) {
      return;
    }

    const currentValue = toSafeString_v3(select.value).trim();
    select.innerHTML = "";

    if (placeholder) {
      const placeholderOption = document.createElement("option");
      placeholderOption.value = "";
      placeholderOption.textContent = placeholder;
      select.appendChild(placeholderOption);
    }

    (Array.isArray(options) ? options : []).forEach((option) => {
      if (!option || typeof option !== "object") {
        return;
      }

      const cleanValue = toSafeString_v3(option.key).trim();
      if (!cleanValue) {
        return;
      }

      const optionElement = document.createElement("option");
      optionElement.value = cleanValue;
      optionElement.textContent = toSafeString_v3(option.label || cleanValue).trim() || cleanValue;
      select.appendChild(optionElement);
    });

    if (currentValue) {
      ensureSelectOption_v3(select, currentValue, currentValue);
    }

    select.value = currentValue;
  }

  function getManualListLabelByKey_v3(root, listKey) {
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

  function getAutomaticSourceLabelParts_v3(processKey, sectionKey, fieldKey) {
    const resolver = getProcessFieldResolver_v3();
    const processLabel = typeof resolver.getProcessSourceProcessLabel_v1 === "function"
      ? resolver.getProcessSourceProcessLabel_v1(processKey)
      : toSafeString_v3(processKey).trim();
    const sectionLabel = typeof resolver.getProcessSourceSectionLabel_v1 === "function"
      ? resolver.getProcessSourceSectionLabel_v1(processKey, sectionKey)
      : toSafeString_v3(sectionKey).trim();
    const fieldLabel = typeof resolver.getProcessSourceFieldLabel_v1 === "function"
      ? resolver.getProcessSourceFieldLabel_v1(processKey, sectionKey, fieldKey)
      : toSafeString_v3(fieldKey).trim();

    return {
      processLabel,
      sectionLabel,
      fieldLabel
    };
  }

  function getListSourceSummary_v3(root, item) {
    if (normalizeFieldType_v3(item.fieldType) !== "list") {
      return "-";
    }

    const manualListKey = normalizeListKey_v3(item.manualListKey || item.listKey);
    const listSourceType = normalizeListSourceType_v3(item.listSourceType);

    if (manualListKey) {
      return `Lista: ${getManualListLabelByKey_v3(root, manualListKey)}`;
    }

    if (listSourceType === "active_menus") {
      return "Menus ativos";
    }

    if (listSourceType === "profile_menu_tabs") {
      return "Abas do processo selecionado";
    }

    if (listSourceType === "automatic" || listSourceType === "field_list") {
      const parts = getAutomaticSourceLabelParts_v3(
        item.automaticSourceProcessKey,
        item.automaticSourceSectionKey,
        item.automaticSourceFieldKey
      );
      const summaryParts = [
        toSafeString_v3(parts.processLabel).trim(),
        toSafeString_v3(parts.sectionLabel).trim(),
        toSafeString_v3(parts.fieldLabel).trim()
      ].filter(Boolean);

      const prefix = listSourceType === "field_list" ? "Lista de campo" : "Automática";
      return summaryParts.length
        ? `${prefix}: ${summaryParts.join(" > ")}`
        : `${prefix}: configuração incompleta`;
    }

    const manualCsvText = item.manualListItemsCsv || (item.manualListItems && item.manualListItems.length ? item.manualListItems.join(", ") : "");
    return manualCsvText ? `Manual: ${manualCsvText}` : "Manual: -";
  }

  function refreshAutomaticSourceOptions_v3(root, selectedValues) {
    const resolver = getProcessFieldResolver_v3();
    const editor = getEditorRoot_v3(root);
    const processSelect = editor.querySelector("[data-additional-field-editor-source-process-key]");
    const sectionSelect = editor.querySelector("[data-additional-field-editor-source-section-key]");
    const fieldSelect = editor.querySelector("[data-additional-field-editor-source-field-key]");
    const selectedProcessKey = toSafeString_v3(
      selectedValues && selectedValues.processKey !== undefined
        ? selectedValues.processKey
        : getInputValue_v3(editor, "[data-additional-field-editor-source-process-key]")
    ).trim();
    const selectedSectionKey = toSafeString_v3(
      selectedValues && selectedValues.sectionKey !== undefined
        ? selectedValues.sectionKey
        : getInputValue_v3(editor, "[data-additional-field-editor-source-section-key]")
    ).trim();
    const selectedFieldKey = toSafeString_v3(
      selectedValues && selectedValues.fieldKey !== undefined
        ? selectedValues.fieldKey
        : getInputValue_v3(editor, "[data-additional-field-editor-source-field-key]")
    ).trim();

    if (processSelect && typeof resolver.getProcessSourceProcessOptions_v1 === "function") {
      replaceSelectOptions_v3(
        processSelect,
        resolver.getProcessSourceProcessOptions_v1(root),
        "Selecione o processo"
      );
      ensureSelectOption_v3(
        processSelect,
        selectedProcessKey,
        typeof resolver.getProcessSourceProcessLabel_v1 === "function"
          ? resolver.getProcessSourceProcessLabel_v1(selectedProcessKey)
          : selectedProcessKey
      );
      processSelect.value = selectedProcessKey;
    }

    if (sectionSelect && typeof resolver.getProcessSourceSectionOptions_v1 === "function") {
      replaceSelectOptions_v3(
        sectionSelect,
        resolver.getProcessSourceSectionOptions_v1(selectedProcessKey),
        "Selecione a secao"
      );
      ensureSelectOption_v3(
        sectionSelect,
        selectedSectionKey,
        typeof resolver.getProcessSourceSectionLabel_v1 === "function"
          ? resolver.getProcessSourceSectionLabel_v1(selectedProcessKey, selectedSectionKey)
          : selectedSectionKey
      );
      sectionSelect.value = selectedSectionKey;
    }

    if (fieldSelect && typeof resolver.getProcessSourceFieldOptions_v1 === "function") {
      const currentListSourceType = normalizeListSourceType_v3(
        getInputValue_v3(editor, "[data-additional-field-editor-list-source-type]")
      );
      let rawFieldOptions = resolver
        .getProcessSourceFieldOptions_v1(selectedProcessKey, selectedSectionKey)
        .filter((opt) => opt && opt.fieldType !== "header");
      if (currentListSourceType === "field_list") {
        rawFieldOptions = rawFieldOptions.filter((opt) => opt && opt.fieldType === "list");
      }
      replaceSelectOptions_v3(fieldSelect, rawFieldOptions, "Selecione o campo");
      ensureSelectOption_v3(
        fieldSelect,
        selectedFieldKey,
        typeof resolver.getProcessSourceFieldLabel_v1 === "function"
          ? resolver.getProcessSourceFieldLabel_v1(selectedProcessKey, selectedSectionKey, selectedFieldKey)
          : selectedFieldKey
      );
      fieldSelect.value = selectedFieldKey;
    }
  }

  function resetListSourceFields_v3(root, options) {
    const editor = getEditorRoot_v3(root);
    const safeOptions = options && typeof options === "object" ? options : {};
    const resetSourceType = safeOptions.resetSourceType !== false;
    const resetManual = safeOptions.resetManual !== false;
    const resetAutomatic = safeOptions.resetAutomatic !== false;

    if (resetSourceType) {
      setInputValue_v3(editor, "[data-additional-field-editor-list-source-type]", "manual");
      setInputValue_v3(editor, "[data-additional-field-editor-list-key]", "");
    }

    if (resetManual) {
      setInputValue_v3(editor, "[data-additional-field-editor-manual-items]", "");
    }

    if (resetAutomatic) {
      setInputValue_v3(editor, "[data-additional-field-editor-source-process-key]", "");
      setInputValue_v3(editor, "[data-additional-field-editor-source-section-key]", "");
      setInputValue_v3(editor, "[data-additional-field-editor-source-field-key]", "");
      setInputValue_v3(editor, "[data-additional-field-editor-automatic-only-active]", "");
      refreshAutomaticSourceOptions_v3(root, {
        processKey: "",
        sectionKey: "",
        fieldKey: ""
      });
    }
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
    const listSourceTypes = getLegacyValues_v3(container, "additional_field_list_source_type");
    const manualListKeys = getLegacyValues_v3(container, "additional_field_manual_list_key");
    const manualListItemsCsvValues = getLegacyValues_v3(container, "additional_field_manual_list_items");
    const automaticSourceProcessKeys = getLegacyValues_v3(container, "additional_field_automatic_source_process_key");
    const automaticSourceSectionKeys = getLegacyValues_v3(container, "additional_field_automatic_source_section_key");
    const automaticSourceFieldKeys = getLegacyValues_v3(container, "additional_field_automatic_source_field_key");
    const automaticOnlyActiveValues = getLegacyValues_v3(container, "additional_field_automatic_only_active");

    const rowsCount = Math.max(
      keys.length,
      labels.length,
      types.length,
      requiredValues.length,
      sizes.length,
      listKeys.length,
      listSourceTypes.length,
      manualListKeys.length,
      automaticSourceProcessKeys.length,
      automaticSourceSectionKeys.length,
      automaticSourceFieldKeys.length,
      automaticOnlyActiveValues.length
    );

    const items = [];

    for (let index = 0; index < rowsCount; index += 1) {
      const fieldType = normalizeFieldType_v3(types[index] || "text");
      const key = normalizeFieldKey_v3(keys[index] || labels[index] || "");

      if (!key && !labels[index]) {
        continue;
      }

      const automaticSourceProcessKey = normalizeLookup_v3(automaticSourceProcessKeys[index]);
      const automaticSourceSectionKey = normalizeLookup_v3(automaticSourceSectionKeys[index]);
      const automaticSourceFieldKey = normalizeLookup_v3(automaticSourceFieldKeys[index]);
      const listSourceType = fieldType === "list"
        ? normalizeListSourceType_v3(
            listSourceTypes[index] ||
            (automaticSourceProcessKey || automaticSourceSectionKey || automaticSourceFieldKey
              ? "automatic"
              : "manual")
          )
        : "manual";
      const manualListKey = fieldType === "list"
        ? normalizeListKey_v3(manualListKeys[index] || listKeys[index])
        : "";
      const manualListItemsCsvRaw = fieldType === "list" && listSourceType === "manual"
        ? toSafeString_v3(manualListItemsCsvValues[index] || "").trim()
        : "";
      const manualListItemsParsed = manualListItemsCsvRaw
        ? manualListItemsCsvRaw.split(",").map(function(s) { return s.trim(); }).filter(Boolean)
        : [];

      items.push({
        id: key || `custom_field_${index + 1}`,
        key,
        label: toSafeString_v3(labels[index] || key),
        fieldType,
        isRequired: fieldType === "header" ? false : normalizeRequired_v3(requiredValues[index]),
        size: normalizeSize_v3(sizes[index], fieldType),
        listKey: fieldType === "list" && listSourceType === "manual" ? manualListKey : "",
        listSourceType,
        manualListKey,
        manualListItemsCsv: manualListItemsCsvRaw,
        manualListItems: manualListItemsParsed,
        automaticSourceProcessKey,
        automaticSourceSectionKey,
        automaticSourceFieldKey,
        automaticOnlyActive: fieldType === "list"
          ? normalizeRequired_v3(automaticOnlyActiveValues[index])
          : false,
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
    setInputValue_v3(editor, "[data-additional-field-editor-list-source-type]", "manual");
    setInputValue_v3(editor, "[data-additional-field-editor-list-key]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-manual-items]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-process-key]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-section-key]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-field-key]", "");
    setInputValue_v3(editor, "[data-additional-field-editor-automatic-only-active]", "");
    refreshProcessListOptions_v3(root, "");
    refreshAutomaticSourceOptions_v3(root, {
      processKey: "",
      sectionKey: "",
      fieldKey: ""
    });

    updateEditorVisibility_v3(root);

    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");

    if (submitButton) {
      submitButton.textContent = "Guardar";
    }
  }

  function loadEditorItem_v3(item, context) {
    const root = context.root;
    const editor = getEditorRoot_v3(root);
    const selectedListKey = normalizeListKey_v3(item.manualListKey || item.listKey);

    setInputValue_v3(editor, "[data-additional-field-editor-key]", item.key || "");
    setInputValue_v3(editor, "[data-additional-field-editor-label]", item.label || "");
    setInputValue_v3(editor, "[data-additional-field-editor-type]", item.fieldType || "text");
    setInputValue_v3(editor, "[data-additional-field-editor-size]", item.size || "");
    setInputValue_v3(editor, "[data-additional-field-editor-required]", item.isRequired ? "1" : "");
    setInputValue_v3(editor, "[data-additional-field-editor-list-source-type]", item.listSourceType || "manual");
    setInputValue_v3(editor, "[data-additional-field-editor-list-key]", selectedListKey);
    setInputValue_v3(editor, "[data-additional-field-editor-manual-items]", item.manualListItemsCsv || (item.manualListItems && item.manualListItems.length ? item.manualListItems.join(", ") : "") || "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-process-key]", item.automaticSourceProcessKey || "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-section-key]", item.automaticSourceSectionKey || "");
    setInputValue_v3(editor, "[data-additional-field-editor-source-field-key]", item.automaticSourceFieldKey || "");
    setInputValue_v3(editor, "[data-additional-field-editor-automatic-only-active]", item.automaticOnlyActive ? "1" : "");
    refreshProcessListOptions_v3(root, selectedListKey);
    refreshAutomaticSourceOptions_v3(root, {
      processKey: item.automaticSourceProcessKey || "",
      sectionKey: item.automaticSourceSectionKey || "",
      fieldKey: item.automaticSourceFieldKey || ""
    });

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
    const explicitRawKey = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-key]")).trim();
    const rawKey = explicitRawKey || label;
    const fieldType = normalizeFieldType_v3(getInputValue_v3(editor, "[data-additional-field-editor-type]"));
    const key = normalizeFieldKey_v3(rawKey);
    const selectedListKey = normalizeListKey_v3(
      getInputValue_v3(editor, "[data-additional-field-editor-list-key]")
    );
    const resolvedListKey = selectedListKey || "";

    return {
      id: key,
      key,
      explicitKey: normalizeFieldKey_v3(explicitRawKey),
      label,
      fieldType,
      isRequired: fieldType === "header"
        ? false
        : normalizeRequired_v3(getInputValue_v3(editor, "[data-additional-field-editor-required]")),
      size: normalizeSize_v3(getInputValue_v3(editor, "[data-additional-field-editor-size]"), fieldType),
      listSourceType: "manual",
      manualListKey: fieldType === "list" ? resolvedListKey : "",
      listKey: fieldType === "list" ? resolvedListKey : "",
      manualListItemsCsv: "",
      manualListItems: [],
      automaticSourceProcessKey: "",
      automaticSourceSectionKey: "",
      automaticSourceFieldKey: "",
      automaticOnlyActive: false
    };
  }

  function findGroupDuplicate_v3(item, context) {
    const editingId = toSafeString_v3(context.state.editingId);
    const itemGroup = getFieldGroup_v3(item.fieldType);
    const normalizedItemKey = normalizeLookup_v3(item.key);
    const normalizedItemLabel = normalizeLookup_v3(item.label);

    return context.items.find((existingItem) => {
      const sameId = toSafeString_v3(existingItem.__managerId) === editingId;

      if (sameId) {
        return false;
      }

      if (getFieldGroup_v3(existingItem.fieldType) !== itemGroup) {
        return false;
      }

      return (
        normalizeLookup_v3(existingItem.key) === normalizedItemKey ||
        normalizeLookup_v3(existingItem.label) === normalizedItemLabel
      );
    });
  }

  function buildUniqueFieldKey_v3(baseKey, context) {
    const editingId = toSafeString_v3(context.state.editingId);
    const normalizedBaseKey = normalizeFieldKey_v3(baseKey);
    const usedKeys = new Set(
      context.items
        .filter((existingItem) => toSafeString_v3(existingItem.__managerId) !== editingId)
        .map((existingItem) => normalizeLookup_v3(existingItem.key))
        .filter(Boolean)
    );

    let uniqueKey = normalizedBaseKey;
    let suffixIndex = 2;

    while (usedKeys.has(normalizeLookup_v3(uniqueKey))) {
      uniqueKey = `${normalizedBaseKey}_${suffixIndex}`;
      suffixIndex += 1;
    }

    return uniqueKey;
  }

  function resolvePreferredFieldKey_v3(item, context) {
    if (item.explicitKey) {
      return item.explicitKey;
    }

    const normalizedLabel = normalizeLookup_v3(item.label);
    const crossGroupLabelExists = context.items.some((existingItem) => {
      const sameId = toSafeString_v3(existingItem.__managerId) === toSafeString_v3(context.state.editingId);

      if (sameId) {
        return false;
      }

      return (
        normalizeLookup_v3(existingItem.label) === normalizedLabel &&
        getFieldGroup_v3(existingItem.fieldType) !== getFieldGroup_v3(item.fieldType)
      );
    });

    if (crossGroupLabelExists) {
      return buildGroupScopedFieldKey_v3(item.label, item.fieldType);
    }

    return item.key;
  }

  function ensureUniqueCrossGroupKey_v3(item, context) {
    const preferredKey = resolvePreferredFieldKey_v3(item, context);
    const normalizedItemKey = normalizeLookup_v3(preferredKey);
    const editingId = toSafeString_v3(context.state.editingId);
    const conflictingItem = context.items.find((existingItem) => {
      const sameId = toSafeString_v3(existingItem.__managerId) === editingId;

      if (sameId) {
        return false;
      }

      return normalizeLookup_v3(existingItem.key) === normalizedItemKey;
    });

    if (!conflictingItem) {
      return {
        ...item,
        id: preferredKey,
        key: preferredKey
      };
    }

    if (getFieldGroup_v3(conflictingItem.fieldType) === getFieldGroup_v3(item.fieldType)) {
      return {
        ...item,
        id: preferredKey,
        key: preferredKey
      };
    }

    const uniqueKey = buildUniqueFieldKey_v3(preferredKey, context);

    return {
      ...item,
      id: uniqueKey,
      key: uniqueKey
    };
  }

  function validateEditorItem_v3(item, context) {
    const selectedListKey = normalizeListKey_v3(item.manualListKey || item.listKey);

    if (!item.label) {
      return { valid: false, message: "Informe o nome do campo." };
    }

    if (!item.key) {
      return { valid: false, message: "Informe a chave do campo." };
    }

    if (item.fieldType === "list" && !selectedListKey) {
      return { valid: false, message: "Selecione o nome da lista." };
    }

    const duplicated = findGroupDuplicate_v3(item, context);

    if (duplicated) {
      return {
        valid: false,
        message: getFieldGroup_v3(item.fieldType) === "header"
          ? "Já existe um cabeçalho com este nome."
          : "Já existe um campo com este nome."
      };
    }

    return { valid: true };
  }

  function updateEditorVisibility_v3(root) {
    const editor = getEditorRoot_v3(root);
    const fieldType = normalizeFieldType_v3(getInputValue_v3(editor, "[data-additional-field-editor-type]"));
    const sizeWrap = editor.querySelector("[data-additional-field-size-wrap]");
    const listSourceWrap = editor.querySelector("[data-additional-field-list-source-wrap]");
    const automaticProcessWrap = editor.querySelector("[data-additional-field-automatic-process-wrap]");
    const automaticSectionWrap = editor.querySelector("[data-additional-field-automatic-section-wrap]");
    const automaticFieldWrap = editor.querySelector("[data-additional-field-automatic-field-wrap]");
    const automaticOnlyActiveWrap = editor.querySelector("[data-additional-field-automatic-only-active-wrap]");
    const requiredWrap = editor.querySelector("[data-additional-field-required-wrap]");
    const isListField = fieldType === "list";

    if (!isListField) {
      resetListSourceFields_v3(root, {
        resetSourceType: true,
        resetManual: true,
        resetAutomatic: true
      });
    }

    if (sizeWrap) {
      sizeWrap.style.display = TEXTUAL_TYPES.has(fieldType) ? "" : "none";
    }

    if (automaticProcessWrap) {
      automaticProcessWrap.style.display = "none";
    }

    if (automaticSectionWrap) {
      automaticSectionWrap.style.display = "none";
    }

    if (automaticFieldWrap) {
      automaticFieldWrap.style.display = "none";
    }

    if (automaticOnlyActiveWrap) {
      automaticOnlyActiveWrap.style.display = "none";
    }

    if (requiredWrap) {
      requiredWrap.style.display = fieldType === "header" ? "none" : "";
    }

    if (listSourceWrap) {
      listSourceWrap.style.display = isListField ? "" : "none";
      if (isListField) {
        refreshProcessListOptions_v3(root, getInputValue_v3(editor, "[data-additional-field-editor-list-key]"));
      }
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
        showValidationMessage_v3(validationResult.message);
      }

      return;
    }

    manager.addOrUpdate(ensureUniqueCrossGroupKey_v3(item, {
      manager,
      root,
      elements: manager.elements,
      state: manager.state,
      items: manager.getItems()
    }));
  }

  function hasDraft_v3(root, manager) {
    if (manager && manager.state && manager.state.editingId) {
      return true;
    }

    const editor = getEditorRoot_v3(root);

    return Boolean(
      getInputValue_v3(editor, "[data-additional-field-editor-label]").trim() ||
      getInputValue_v3(editor, "[data-additional-field-editor-key]").trim() ||
      getInputValue_v3(editor, "[data-additional-field-editor-list-key]").trim() ||
      getInputValue_v3(editor, "[data-additional-field-editor-manual-items]").trim()
    );
  }

  function bindGlobalCancelReaction_v3(root, cancelButton, manager, datasetKey) {
    if (!root || !cancelButton || !manager) {
      return;
    }

    const boundKey = datasetKey || "additionalFieldsCancelBoundV3";

    if (root.dataset[boundKey] === "1") {
      return;
    }

    root.dataset[boundKey] = "1";
    cancelButton.dataset.appgenesisCancel = "1";
    cancelButton.dataset.appgenesisCancelLocal = "1";
    cancelButton.__appgenesisLocalDraftCheckV1 = function () {
      return hasDraft_v3(root, manager);
    };

    root.addEventListener("appgenesis:cancelled", (event) => {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== cancelButton) {
        return;
      }

      manager.clearEditing();
    });
  }

  function bindEditorExtras_v3(root, manager) {
    if (root.dataset.additionalFieldsExtrasBoundV3 === "1") {
      return;
    }

    root.dataset.additionalFieldsExtrasBoundV3 = "1";

    const editor = getEditorRoot_v3(root);
    const typeSelect = editor.querySelector("[data-additional-field-editor-type]");
    const listSourceTypeSelect = editor.querySelector("[data-additional-field-editor-list-source-type]");
    const sourceProcessSelect = editor.querySelector("[data-additional-field-editor-source-process-key]");
    const sourceSectionSelect = editor.querySelector("[data-additional-field-editor-source-section-key]");
    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");
    const cancelButton = editor.querySelector("[data-additional-field-editor-cancel]");

    if (typeSelect) {
      typeSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root);
        updateEditorVisibility_v3(root);
      });
    }

    if (listSourceTypeSelect) {
      listSourceTypeSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root);
        updateEditorVisibility_v3(root);
      });
    }

    if (sourceProcessSelect) {
      sourceProcessSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root, {
          processKey: sourceProcessSelect.value,
          sectionKey: "",
          fieldKey: ""
        });
      });
    }

    if (sourceSectionSelect) {
      sourceSectionSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root, {
          processKey: sourceProcessSelect ? sourceProcessSelect.value : "",
          sectionKey: sourceSectionSelect.value,
          fieldKey: ""
        });
      });
    }

    if (submitButton) {
      submitButton.addEventListener("click", (event) => {
        event.preventDefault();
        submitEditorItem_v3(root, manager);
      });
    }

    if (cancelButton) {
      bindGlobalCancelReaction_v3(root, cancelButton, manager, "additionalFieldsCancelBoundV3");
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
      const listSourceType = normalizeListSourceType_v3(item.listSourceType);
      const manualListKey = normalizeListKey_v3(item.manualListKey || item.listKey);
      const manualItemsCsv = fieldType === "list" && listSourceType === "manual"
        ? toSafeString_v3(item.manualListItemsCsv || (item.manualListItems && item.manualListItems.length ? item.manualListItems.join(", ") : "")).trim()
        : "";

      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_key", item.key || ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_label", item.label || ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_type", fieldType));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_required", item.isRequired ? "1" : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_size", normalizeSize_v3(item.size, fieldType)));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_list_key", fieldType === "list" && listSourceType === "manual" ? manualListKey : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_list_source_type", fieldType === "list" ? listSourceType : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_manual_list_key", fieldType === "list" ? manualListKey : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_manual_list_items", manualItemsCsv));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_automatic_source_process_key", fieldType === "list" ? item.automaticSourceProcessKey || "" : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_automatic_source_section_key", fieldType === "list" ? item.automaticSourceSectionKey || "" : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_automatic_source_field_key", fieldType === "list" ? item.automaticSourceFieldKey || "" : ""));
      hiddenContainer.appendChild(createHiddenInput_v3("additional_field_automatic_only_active", fieldType === "list" && listSourceType === "automatic" && item.automaticOnlyActive ? "1" : ""));
    });
  }


// APPGENESIS_ADDITIONAL_FIELDS_SAVE_FROM_TOP_V4_START

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
    const selectedListKey = toSafeString_v3(getInputValue_v3(editor, "[data-additional-field-editor-list-key]")).trim();
    const isRequired = normalizeRequired_v3(getInputValue_v3(editor, "[data-additional-field-editor-required]"));

    if (manager && manager.state && manager.state.editingId) {
      return true;
    }

    return Boolean(
      label ||
      selectedListKey ||
      isRequired ||
      (fieldType === "list" && selectedListKey) ||
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

  function submitEditorDraft_v4(root, manager) {
    if (!hasEditorDraft_v4(root, manager)) {
      return true;
    }

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
        showValidationMessage_v3(validationResult.message);
      }

      return false;
    }

    manager.addOrUpdate(ensureUniqueCrossGroupKey_v3(item, {
      manager,
      root,
      elements: manager.elements,
      state: manager.state,
      items: manager.getItems()
    }));
    return true;
  }

  function bindEditorExtras_v4(root, manager) {
    if (root.dataset.additionalFieldsExtrasBoundV4 === "1") {
      return;
    }

    root.dataset.additionalFieldsExtrasBoundV4 = "1";

    const editor = getEditorRoot_v3(root);
    const parentForm = root.closest("form");
    const typeSelect = editor.querySelector("[data-additional-field-editor-type]");
    const listSourceTypeSelect = editor.querySelector("[data-additional-field-editor-list-source-type]");
    const sourceProcessSelect = editor.querySelector("[data-additional-field-editor-source-process-key]");
    const sourceSectionSelect = editor.querySelector("[data-additional-field-editor-source-section-key]");
    const submitButton = editor.querySelector("[data-additional-field-editor-submit]");
    const cancelButton = editor.querySelector("[data-additional-field-editor-cancel]");

    if (typeSelect) {
      typeSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root);
        updateEditorVisibility_v3(root);
      });
    }

    if (listSourceTypeSelect) {
      listSourceTypeSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root);
        updateEditorVisibility_v3(root);
      });
    }

    if (sourceProcessSelect) {
      sourceProcessSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root, {
          processKey: sourceProcessSelect.value,
          sectionKey: "",
          fieldKey: ""
        });
      });
    }

    if (sourceSectionSelect) {
      sourceSectionSelect.addEventListener("change", () => {
        refreshAutomaticSourceOptions_v3(root, {
          processKey: sourceProcessSelect ? sourceProcessSelect.value : "",
          sectionKey: sourceSectionSelect.value,
          fieldKey: ""
        });
      });
    }

    if (submitButton) {
      submitButton.textContent = "Guardar";
    }

    if (cancelButton) {
      cancelButton.textContent = "Cancelar";
      bindGlobalCancelReaction_v3(root, cancelButton, manager, "additionalFieldsCancelBoundV4");
    }

    if (parentForm && parentForm.dataset.additionalFieldsTopSubmitBoundV4 !== "1") {
      parentForm.dataset.additionalFieldsTopSubmitBoundV4 = "1";

      parentForm.addEventListener("submit", (event) => {
        const submitter = event.submitter || document.activeElement;

        if (!submitter || submitter !== submitButton) {
          return;
        }

        try {
          const canSubmit = submitEditorDraft_v4(root, manager);

          if (canSubmit === false) {
            event.preventDefault();
            return;
          }

          manager.syncHiddenInputs();
        } catch (error) {
          event.preventDefault();
          throw error;
        }
      });
    }

    updateEditorVisibility_v3(root);
  }

// APPGENESIS_ADDITIONAL_FIELDS_SAVE_FROM_TOP_V4_END

  //###################################################################################
  // (6) CRIAR MANAGER
  //###################################################################################

  function setupOneProcessAdditionalFieldsManagerV3_v3(root) {
    if (!root || root.dataset.additionalFieldsManagerReadyV3 === "1") {
      return null;
    }

    const core = window.AppGenesisConfigurableItems || {};

    if (typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const initialItems = readLegacyAdditionalFields_v3(root);

    const manager = core.createConfigurableItemsManager_v1({
      root,
      itemName: "campo",
      itemNamePlural: "campos",
      createTitle: "Criar campo adicional",
      editTitle: "Editar campo adicional",
      pageSizeDefault: core.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1,
      pageSizeOptions: core.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1,
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
          key: "listSource",
          label: "Lista/Fonte",
          render: function (item) {
            return getListSourceSummary_v3(root, item);
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
    refreshProcessListOptions_v3(root, "");
    refreshAutomaticSourceOptions_v3(root);
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
