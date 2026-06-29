//###################################################################################
// APPVERBOBRAGA - PROCESS FIELD OPTIONS RESOLVER V1
//###################################################################################

(function (window, document) {
  "use strict";

  const SUPPORTED_TYPES = new Set(["text", "number", "email", "phone", "date", "flag", "header", "list"]);
  const ADDITIONAL_FIELDS_ROOT_SELECTOR = "[data-process-additional-fields-manager-v3='1']";

  //###################################################################################
  // (1) HELPERS
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

  function normalizeFieldKey_v1(value) {
    return toSafeString_v1(value).trim().toLowerCase();
  }

  function normalizeMenuKey_v1(value) {
    return toSafeString_v1(value).trim().toLowerCase();
  }

  function normalizeFieldType_v1(value) {
    const cleanType = normalizeLookup_v1(value).replace(/_/g, "-");

    if (SUPPORTED_TYPES.has(cleanType)) {
      return cleanType;
    }

    return "text";
  }

  function getFieldGroup_v1(fieldType) {
    return normalizeFieldType_v1(fieldType) === "header" ? "header" : "field";
  }

  function stripHeaderSuffix_v1(label) {
    return toSafeString_v1(label)
      .replace(/\s*-\s*cabe[çc]alho\s*$/i, "")
      .trim();
  }

  function normalizeOption_v1(rawOption) {
    if (!rawOption || typeof rawOption !== "object") {
      return null;
    }

    const key = normalizeFieldKey_v1(rawOption.key);

    if (!key) {
      return null;
    }

    const fieldType = normalizeFieldType_v1(
      rawOption.fieldType ||
      rawOption.field_type ||
      rawOption.kind ||
      rawOption.type
    );

    return {
      key,
      label: stripHeaderSuffix_v1(rawOption.label || rawOption.text || key) || key,
      fieldType: fieldType === "field" ? "text" : fieldType
    };
  }

  function dedupeOptions_v1(options) {
    const normalizedOptions = [];
    const seenIdentities = new Set();

    (Array.isArray(options) ? options : []).forEach((rawOption) => {
      const option = normalizeOption_v1(rawOption);
      const optionIdentity = option
        ? `${getFieldGroup_v1(option.fieldType)}::${option.key}`
        : "";

      if (!option || seenIdentities.has(optionIdentity)) {
        return;
      }

      seenIdentities.add(optionIdentity);
      normalizedOptions.push(option);
    });

    return normalizedOptions;
  }

  function inferFieldTypeFromOption_v1(option) {
    const datasetType = option
      ? (
          option.dataset.processConfigKind ||
          option.dataset.fieldType ||
          option.dataset.type ||
          option.getAttribute("data-process-config-kind") ||
          option.getAttribute("data-field-type") ||
          option.getAttribute("data-type") ||
          ""
        )
      : "";
    const explicitType = normalizeFieldType_v1(datasetType);

    if (datasetType && explicitType) {
      return explicitType;
    }

    const optionText = normalizeLookup_v1(option ? option.textContent : "");
    return optionText.includes("cabecalho") ? "header" : "text";
  }

  function findScopeRoot_v1(scopeRoot) {
    if (scopeRoot && typeof scopeRoot.querySelector === "function") {
      return scopeRoot;
    }

    return document;
  }

  //###################################################################################
  // (2) SNAPSHOT DOS SELECTS
  //###################################################################################

  function createOptionSnapshot_v1(select) {
    if (!select || !select.options) {
      return [];
    }

    return dedupeOptions_v1(
      Array.from(select.options).map((option) => ({
        key: option.value,
        label: option.dataset.processConfigLabel || option.textContent || option.value,
        fieldType: inferFieldTypeFromOption_v1(option)
      }))
    );
  }

  //###################################################################################
  // (3) CAMPOS ADICIONAIS ATUAIS
  //###################################################################################

  function getAdditionalFieldsRoot_v1(scopeRoot) {
    const root = findScopeRoot_v1(scopeRoot);

    if (typeof root.matches === "function" && root.matches(ADDITIONAL_FIELDS_ROOT_SELECTOR)) {
      return root;
    }

    return root.querySelector(ADDITIONAL_FIELDS_ROOT_SELECTOR);
  }

  function getInputValues_v1(container, name) {
    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll(`[name='${name}']`)).map((input) => {
      return toSafeString_v1(input.value).trim();
    });
  }

  function readAdditionalFields_v1(scopeRoot) {
    const root = getAdditionalFieldsRoot_v1(scopeRoot);

    if (!root) {
      return [];
    }

    const hiddenContainer = root.querySelector("[data-additional-fields-hidden-container]");
    const legacyContainer = root.querySelector("[data-additional-fields-legacy-container]");
    const sourceContainer = hiddenContainer && hiddenContainer.querySelector("input[name='additional_field_key']")
      ? hiddenContainer
      : legacyContainer;

    if (!sourceContainer) {
      return [];
    }

    const keys = getInputValues_v1(sourceContainer, "additional_field_key");
    const labels = getInputValues_v1(sourceContainer, "additional_field_label");
    const types = getInputValues_v1(sourceContainer, "additional_field_type");
    const rowsCount = Math.max(keys.length, labels.length, types.length);
    const options = [];

    for (let index = 0; index < rowsCount; index += 1) {
      const key = normalizeFieldKey_v1(keys[index]);
      const label = stripHeaderSuffix_v1(labels[index] || key);
      const fieldType = normalizeFieldType_v1(types[index]);

      if (!key || !label) {
        continue;
      }

      options.push({
        key,
        label,
        fieldType
      });
    }

    return dedupeOptions_v1(options);
  }

  //###################################################################################
  // (4) RESOLVER DE PROCESSOS/SECOES/CAMPOS PARA LISTA AUTOMATICA
  //###################################################################################

  function getBootstrapSidebarMenuSettings_v1() {
    const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
    return Array.isArray(bootstrap.sidebarMenuSettings) ? bootstrap.sidebarMenuSettings : [];
  }

  function getBootstrapVisibleSidebarMenuKeys_v1() {
    const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
    const rawKeys = Array.isArray(bootstrap.visibleSidebarMenuKeys) ? bootstrap.visibleSidebarMenuKeys : [];

    return new Set(
      rawKeys
        .map((rawKey) => normalizeMenuKey_v1(rawKey))
        .filter(Boolean)
    );
  }

  function buildProcessFieldOptionMap_v1(setting) {
    const optionMap = new Map();
    const normalizedOptions = dedupeOptions_v1(
      Array.isArray(setting && setting.process_field_options)
        ? setting.process_field_options
        : []
    );

    normalizedOptions.forEach((option) => {
      optionMap.set(option.key, option);
    });

    return optionMap;
  }

  function buildProcessSourceSections_v1(setting) {
    const visibleRows = Array.isArray(setting && setting.process_visible_field_rows)
      ? setting.process_visible_field_rows
      : [];
    const optionMap = buildProcessFieldOptionMap_v1(setting);
    const sectionMap = new Map();
    const sectionOrder = [];
    const seenFieldBySection = new Map();

    function ensureSection(sectionKey, sectionLabel) {
      const cleanSectionKey = normalizeMenuKey_v1(sectionKey || "__geral__") || "__geral__";

      if (!sectionMap.has(cleanSectionKey)) {
        sectionMap.set(cleanSectionKey, {
          key: cleanSectionKey,
          label: stripHeaderSuffix_v1(sectionLabel || (cleanSectionKey === "__geral__" ? "Geral" : "Aba")) || "Aba",
          fields: []
        });
        sectionOrder.push(cleanSectionKey);
      }

      return sectionMap.get(cleanSectionKey);
    }

    visibleRows.forEach((row) => {
      if (!row || typeof row !== "object") {
        return;
      }

      const fieldKey = normalizeFieldKey_v1(row.field_key);
      if (!fieldKey) {
        return;
      }

      const fieldOption = optionMap.get(fieldKey);
      if (!fieldOption || normalizeFieldType_v1(fieldOption.fieldType) === "header") {
        return;
      }

      const headerKey = normalizeMenuKey_v1(row.header_key);
      const sectionKey = headerKey || "__geral__";
      const headerOption = headerKey ? optionMap.get(headerKey) : null;
      const section = ensureSection(
        sectionKey,
        headerOption ? headerOption.label : "Geral"
      );
      let seenFieldKeys = seenFieldBySection.get(sectionKey);

      if (!seenFieldKeys) {
        seenFieldKeys = new Set();
        seenFieldBySection.set(sectionKey, seenFieldKeys);
      }

      if (seenFieldKeys.has(fieldKey)) {
        return;
      }

      seenFieldKeys.add(fieldKey);
      section.fields.push({
        key: fieldOption.key,
        label: fieldOption.label,
        fieldType: fieldOption.fieldType
      });
    });

    const groupedSections = sectionOrder
      .map((sectionKey) => sectionMap.get(sectionKey))
      .filter((section) => section && Array.isArray(section.fields) && section.fields.length);

    if (groupedSections.length === 1 && groupedSections[0].key === "__geral__") {
      return groupedSections[0].fields.map((field) => ({
        key: `field:${field.key}`,
        label: field.label,
        fields: [field]
      }));
    }

    return groupedSections;
  }

  function getProcessSourceProcessOptions_v1() {
    const visibleKeys = getBootstrapVisibleSidebarMenuKeys_v1();
    const settings = getBootstrapSidebarMenuSettings_v1();

    return settings.reduce((options, setting) => {
      const processKey = normalizeMenuKey_v1(setting && setting.key);
      const processLabel = stripHeaderSuffix_v1(setting && setting.label) || processKey;

      if (!processKey) {
        return options;
      }

      if (visibleKeys.size && !visibleKeys.has(processKey)) {
        return options;
      }

      if (!buildProcessSourceSections_v1(setting).length) {
        return options;
      }

      options.push({
        key: processKey,
        label: processLabel
      });
      return options;
    }, []);
  }

  function getProcessSourceSectionsByProcessKey_v1(processKey) {
    const cleanProcessKey = normalizeMenuKey_v1(processKey);
    const settings = getBootstrapSidebarMenuSettings_v1();
    const matchedSetting = settings.find((setting) => {
      return normalizeMenuKey_v1(setting && setting.key) === cleanProcessKey;
    });

    if (!matchedSetting) {
      return [];
    }

    return buildProcessSourceSections_v1(matchedSetting);
  }

  function getProcessSourceSectionOptions_v1(processKey) {
    return getProcessSourceSectionsByProcessKey_v1(processKey).map((section) => ({
      key: normalizeMenuKey_v1(section && section.key),
      label: stripHeaderSuffix_v1(section && section.label) || normalizeMenuKey_v1(section && section.key)
    }));
  }

  function getProcessSourceFieldOptions_v1(processKey, sectionKey) {
    const cleanSectionKey = normalizeMenuKey_v1(sectionKey);
    const matchedSection = getProcessSourceSectionsByProcessKey_v1(processKey).find((section) => {
      return normalizeMenuKey_v1(section && section.key) === cleanSectionKey;
    });

    if (!matchedSection || !Array.isArray(matchedSection.fields)) {
      return [];
    }

    return matchedSection.fields.map((field) => ({
      key: normalizeFieldKey_v1(field && field.key),
      label: stripHeaderSuffix_v1(field && field.label) || normalizeFieldKey_v1(field && field.key),
      fieldType: normalizeFieldType_v1(field && field.fieldType)
    }));
  }

  function getProcessSourceProcessLabel_v1(processKey) {
    const cleanProcessKey = normalizeMenuKey_v1(processKey);
    const matchedOption = getProcessSourceProcessOptions_v1().find((option) => {
      return normalizeMenuKey_v1(option && option.key) === cleanProcessKey;
    });
    return matchedOption ? matchedOption.label : toSafeString_v1(processKey).trim();
  }

  function getProcessSourceSectionLabel_v1(processKey, sectionKey) {
    const cleanSectionKey = normalizeMenuKey_v1(sectionKey);
    const matchedOption = getProcessSourceSectionOptions_v1(processKey).find((option) => {
      return normalizeMenuKey_v1(option && option.key) === cleanSectionKey;
    });
    return matchedOption ? matchedOption.label : toSafeString_v1(sectionKey).trim();
  }

  function getProcessSourceFieldLabel_v1(processKey, sectionKey, fieldKey) {
    const cleanFieldKey = normalizeFieldKey_v1(fieldKey);
    const matchedOption = getProcessSourceFieldOptions_v1(processKey, sectionKey).find((option) => {
      return normalizeFieldKey_v1(option && option.key) === cleanFieldKey;
    });
    return matchedOption ? matchedOption.label : toSafeString_v1(fieldKey).trim();
  }

  //###################################################################################
  // (5) RESOLVER UNICO
  //###################################################################################

  function resolveScopeOptions_v1(scopeRoot, staticOptions) {
    const baseStaticOptions = dedupeOptions_v1(staticOptions).filter((option) => {
      return !option.key.startsWith("custom_");
    });
    const additionalOptions = readAdditionalFields_v1(scopeRoot);
    const fieldOptions = dedupeOptions_v1(baseStaticOptions.concat(additionalOptions));

    return {
      fieldOptions,
      selectableOptions: fieldOptions.filter((option) => option.fieldType !== "header"),
      headerOptions: fieldOptions.filter((option) => option.fieldType === "header"),
      additionalOptions
    };
  }

  function getOptionLabel_v1(options, key) {
    const cleanKey = normalizeFieldKey_v1(key);
    const matchedOption = dedupeOptions_v1(options).find((option) => option.key === cleanKey);
    return matchedOption ? matchedOption.label : toSafeString_v1(key).trim();
  }

  window.AppVerboProcessFieldOptionsResolverV1 = {
    createOptionSnapshot_v1,
    readAdditionalFields_v1,
    resolveScopeOptions_v1,
    getOptionLabel_v1,
    getProcessSourceProcessOptions_v1,
    getProcessSourceSectionOptions_v1,
    getProcessSourceFieldOptions_v1,
    getProcessSourceProcessLabel_v1,
    getProcessSourceSectionLabel_v1,
    getProcessSourceFieldLabel_v1,
    normalizeMenuKey_v1,
    normalizeFieldKey_v1,
    normalizeFieldType_v1
  };
})(window, document);
