//###################################################################################
// (1) PROCESS SECTIONS BUILDER V1
//###################################################################################
(function registerProcessSectionsBuilderV1() {
  "use strict";

  function buildProcessSections(options = {}) {
    const {
      setting = {},
      processValuesByField = {},
      helpers = {}
    } = options;

    const {
      normalizeMenuKey,
      getProcessQuantityRepeatedFieldKeys,
      toSentenceCaseText,
      normalizeProcessFieldType,
      normalizeProcessFieldSize,
      normalizeProcessFieldRequired,
      getProcessStorageKey
    } = helpers;

    const processRows = Array.isArray(setting.process_visible_field_rows)
      ? setting.process_visible_field_rows
      : [];
    const visibleFieldOrder = Array.isArray(setting.process_visible_fields)
      ? setting.process_visible_fields
      : [];
    const quantityRepeatedFieldKeys = getProcessQuantityRepeatedFieldKeys(setting);
    const optionMetaByKey = new Map();
    const processListsByKey = new Map();
    const processLists = Array.isArray(setting.process_lists) ? setting.process_lists : [];
    processLists.forEach((processList) => {
      const listKey = normalizeMenuKey(processList && processList.key);
      if (!listKey) {
        return;
      }
      processListsByKey.set(
        listKey,
        Array.isArray(processList.items) ? processList.items.map((item) => String(item || "").trim()).filter(Boolean) : []
      );
    });
    const processOptions = Array.isArray(setting.process_field_options)
      ? setting.process_field_options
      : [];
    processOptions.forEach((option) => {
      const optionKey = normalizeMenuKey(option.key);
      if (!optionKey) {
        return;
      }
      const optionLabel = toSentenceCaseText(option.label) || optionKey;
      const optionType = normalizeProcessFieldType(option.field_type);
      const optionSize = normalizeProcessFieldSize(option.size, optionType);
      const optionRequiredRaw = Object.prototype.hasOwnProperty.call(option, "is_required")
        ? option.is_required
        : option.required;
      optionMetaByKey.set(optionKey, {
        label: optionLabel,
        fieldType: optionType,
        size: optionSize,
        listKey: normalizeMenuKey(option.list_key || option.listKey),
        listOptions: processListsByKey.get(normalizeMenuKey(option.list_key || option.listKey)) || [],
        isRequired: normalizeProcessFieldRequired(optionRequiredRaw)
      });
    });

    function buildFieldEntry(fieldKey, fieldMeta = {}) {
      const normalizedFieldType = normalizeProcessFieldType(fieldMeta.fieldType);
      const storageKey = getProcessStorageKey(setting.key, fieldKey);
      const fieldValue = processValuesByField[fieldKey];
      return {
        key: fieldKey,
        label: toSentenceCaseText(fieldMeta.label || fieldKey),
        fieldType: normalizedFieldType === "header" ? "text" : normalizedFieldType,
        size: normalizeProcessFieldSize(fieldMeta.size, normalizedFieldType),
        isRequired: Boolean(fieldMeta.isRequired),
        listKey: normalizeMenuKey(fieldMeta.listKey),
        listOptions: Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions.slice() : [],
        value: typeof fieldValue === "string" ? fieldValue : "",
        storageKey
      };
    }

    function buildSectionsFromVisibleFieldOrder() {
      if (!visibleFieldOrder.length) {
        return [];
      }

      const sectionMap = new Map();
      const sectionOrder = [];
      const seenFieldBySection = new Map();
      let activeSectionKey = "__geral__";

      function ensureSection(sectionKey, sectionLabel) {
        const cleanSectionKey = String(sectionKey || "__geral__");
        if (!sectionMap.has(cleanSectionKey)) {
          sectionMap.set(cleanSectionKey, {
            key: cleanSectionKey,
            label: cleanSectionKey === "__geral__"
              ? "Geral"
              : toSentenceCaseText(sectionLabel || "Aba"),
            fields: []
          });
          sectionOrder.push(cleanSectionKey);
        }
        return sectionMap.get(cleanSectionKey);
      }

      visibleFieldOrder.forEach((rawFieldKey) => {
        const fieldKey = normalizeMenuKey(rawFieldKey);
        if (!fieldKey) {
          return;
        }
        if (quantityRepeatedFieldKeys.has(fieldKey)) {
          return;
        }

        const fieldMeta = optionMetaByKey.get(fieldKey) || {};
        const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
        const fieldLabel = toSentenceCaseText(fieldMeta.label || fieldKey);

        if (fieldType === "header") {
          activeSectionKey = fieldKey;
          ensureSection(fieldKey, fieldLabel);
          return;
        }

        const sectionKey = activeSectionKey || "__geral__";
        const sectionMeta = optionMetaByKey.get(sectionKey) || {};
        const sectionLabel = sectionKey === "__geral__"
          ? "Geral"
          : toSentenceCaseText(sectionMeta.label || sectionKey);
        const section = ensureSection(sectionKey, sectionLabel);
        let seenFieldKeys = seenFieldBySection.get(sectionKey);
        if (!seenFieldKeys) {
          seenFieldKeys = new Set();
          seenFieldBySection.set(sectionKey, seenFieldKeys);
        }
        if (seenFieldKeys.has(fieldKey)) {
          return;
        }
        seenFieldKeys.add(fieldKey);
        section.fields.push(buildFieldEntry(fieldKey, fieldMeta));
      });

      return sectionOrder
        .map((sectionKey) => sectionMap.get(sectionKey))
        .filter(Boolean);
    }

    if (!processRows.length) {
      const fallbackSections = buildSectionsFromVisibleFieldOrder();
      if (fallbackSections.length === 1 && fallbackSections[0].key === "__geral__") {
        return fallbackSections[0].fields.map((field) => ({
          key: `field:${field.key}`,
          label: field.label,
          fields: [field]
        }));
      }
      return fallbackSections;
    }

    const sectionMap = new Map();
    const sectionOrder = [];
    const seenFieldBySection = new Map();

    function ensureSection(sectionKey, sectionLabel) {
      const cleanSectionKey = String(sectionKey || "__geral__");
      if (!sectionMap.has(cleanSectionKey)) {
        sectionMap.set(cleanSectionKey, {
          key: cleanSectionKey,
          label: cleanSectionKey === "__geral__"
            ? "Geral"
            : toSentenceCaseText(sectionLabel || "Aba"),
          fields: []
        });
        sectionOrder.push(cleanSectionKey);
      }
      return sectionMap.get(cleanSectionKey);
    }

    processRows.forEach((row) => {
      const fieldKey = normalizeMenuKey(row.field_key);
      if (!fieldKey) {
        return;
      }
      if (quantityRepeatedFieldKeys.has(fieldKey)) {
        return;
      }
      const headerKey = normalizeMenuKey(row.header_key);
      const sectionKey = headerKey || "__geral__";
      const sectionLabel = headerKey
        ? toSentenceCaseText((optionMetaByKey.get(headerKey) || {}).label || headerKey)
        : "Geral";
      const section = ensureSection(sectionKey, sectionLabel);
      let seenFieldKeys = seenFieldBySection.get(sectionKey);
      if (!seenFieldKeys) {
        seenFieldKeys = new Set();
        seenFieldBySection.set(sectionKey, seenFieldKeys);
      }
      if (seenFieldKeys.has(fieldKey)) {
        return;
      }
      seenFieldKeys.add(fieldKey);
      const fieldMeta = optionMetaByKey.get(fieldKey) || {};
      section.fields.push(buildFieldEntry(fieldKey, fieldMeta));
    });

    visibleFieldOrder.forEach((rawFieldKey) => {
      const fieldKey = normalizeMenuKey(rawFieldKey);
      if (!fieldKey || sectionMap.has(fieldKey)) {
        return;
      }
      const fieldMeta = optionMetaByKey.get(fieldKey) || {};
      if (normalizeProcessFieldType(fieldMeta.fieldType) !== "header") {
        return;
      }
      ensureSection(fieldKey, toSentenceCaseText(fieldMeta.label || fieldKey));
    });

    const groupedSections = sectionOrder
      .map((sectionKey) => sectionMap.get(sectionKey))
      .filter(Boolean);

    if (groupedSections.length === 1 && groupedSections[0].key === "__geral__") {
      return groupedSections[0].fields.map((field) => ({
        key: `field:${field.key}`,
        label: field.label,
        fields: [field]
      }));
    }
    return groupedSections;
  }

  window.APPVERBO_BUILD_PROCESS_SECTIONS_V1 = buildProcessSections;
})();
