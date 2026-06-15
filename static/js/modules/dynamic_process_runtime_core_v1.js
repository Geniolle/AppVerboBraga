// APPVERBO_DYNAMIC_PROCESS_RUNTIME_CORE_V1_MODULE_START
(function registerDynamicProcessRuntimeCoreV1Module() {
  "use strict";

  window.APPVERBO_SETUP_DYNAMIC_PROCESS_RUNTIME_CORE_V1 = function setupDynamicProcessRuntimeCoreV1(
    options
  ) {
    const deps = options && typeof options === "object" ? options : {};
    function buildProcessOptionMetaMap(setting) {
      const metaByKey = new Map();
      const processListsByKey = buildProcessListMetaMap(setting);

      const processOptions = Array.isArray(setting && setting.process_field_options)
        ? setting.process_field_options
        : [];
      processOptions.forEach((option) => {
        const optionKey = normalizeMenuKey(option && option.key);
        if (!optionKey) {
          return;
        }
        const fieldType = normalizeProcessFieldType(option.field_type);
        const listKey = normalizeMenuKey(option.list_key || option.listKey);
        const optionRequiredRaw = Object.prototype.hasOwnProperty.call(option || {}, "is_required")
          ? option.is_required
          : option.required;
        metaByKey.set(optionKey, {
          key: optionKey,
          label: toSentenceCaseText(option.label || optionKey) || optionKey,
          fieldType,
          size: normalizeProcessFieldSize(option.size, fieldType),
          listKey,
          listSourceKey: (processListsByKey.get(listKey) || {}).sourceKey || "",
          listOptions: Array.isArray((processListsByKey.get(listKey) || {}).items)
            ? (processListsByKey.get(listKey) || {}).items.slice()
            : [],
          listOptionRows: Array.isArray((processListsByKey.get(listKey) || {}).optionRows)
            ? (processListsByKey.get(listKey) || {}).optionRows.slice()
            : [],
          isRequired: normalizeProcessFieldRequired(optionRequiredRaw)
        });
      });

      return metaByKey;
    }

    function normalizeProcessListOptionRowsV1(optionRows) {
      if (!Array.isArray(optionRows)) {
        return [];
      }

      return optionRows
        .map((row) => {
          const rawRow = row && typeof row === "object" ? row : {};
          const value = String(rawRow.value || rawRow.label || "").trim();
          const label = String(rawRow.label || rawRow.value || "").trim();
          if (!value && !label) {
            return null;
          }
          return {
            value,
            label,
            menuKey: normalizeMenuKey(rawRow.menu_key || rawRow.menuKey),
            sectionKey: normalizeMenuKey(
              rawRow.section_key || rawRow.sectionKey || rawRow.session_key || rawRow.sessionKey
            ),
            sectionLabel: String(
              rawRow.section_label ||
                rawRow.sectionLabel ||
                rawRow.session_label ||
                rawRow.sessionLabel ||
                ""
            ).trim()
          };
        })
        .filter(Boolean);
    }

    function buildProcessListMetaMap(setting) {
      const processListsByKey = new Map();
      const processLists = Array.isArray(setting && setting.process_lists)
        ? setting.process_lists
        : [];

      processLists.forEach((processList) => {
        const listKey = normalizeMenuKey(processList && processList.key);
        if (!listKey) {
          return;
        }

        processListsByKey.set(listKey, {
          key: listKey,
          sourceKey: normalizeDynamicProcessListSourceKeyV1(
            processList && (processList.source_key || processList.sourceKey)
          ),
          items: Array.isArray(processList && processList.items)
            ? processList.items.map((item) => String(item || "").trim()).filter(Boolean)
            : [],
          optionRows: normalizeProcessListOptionRowsV1(
            processList && (processList.option_rows || processList.optionRows)
          )
        });
      });

      return processListsByKey;
    }

    function resolveDynamicProcessListControlValueV1(
      renderedInputsByFieldKey,
      processValuesByField,
      fieldKey
    ) {
      const cleanFieldKey = normalizeMenuKey(fieldKey);
      if (!cleanFieldKey) {
        return "";
      }

      const renderedControl =
        renderedInputsByFieldKey instanceof Map
          ? renderedInputsByFieldKey.get(cleanFieldKey)
          : null;

      if (renderedControl) {
        if (renderedControl.tagName && String(renderedControl.tagName).toLowerCase() === "select") {
          return String(renderedControl.value || "").trim();
        }
        if (renderedControl.type === "checkbox") {
          return renderedControl.checked ? "1" : "0";
        }
        return String(renderedControl.value || "").trim();
      }

      return String((processValuesByField && processValuesByField[cleanFieldKey]) || "").trim();
    }

    function resolveDynamicProcessSessionControllerFieldKeyV1(
      sectionFields,
      processSetting,
      processListMetaByKey,
      targetFieldKey
    ) {
      const candidates = [];
      const seenFieldKeys = new Set();
      const sources = [];

      if (Array.isArray(sectionFields)) {
        sources.push(sectionFields);
      }
      if (Array.isArray(processSetting && processSetting.process_field_options)) {
        sources.push(processSetting.process_field_options);
      }

      sources.forEach((fields) => {
        fields.forEach((field) => {
          const fieldKey = normalizeMenuKey(field && field.key);
          const listKey = normalizeMenuKey(field && (field.listKey || field.list_key));
          if (
            !fieldKey ||
            fieldKey === normalizeMenuKey(targetFieldKey) ||
            seenFieldKeys.has(fieldKey)
          ) {
            return;
          }
          const listMeta =
            processListMetaByKey instanceof Map ? processListMetaByKey.get(listKey) : null;
          if (!listMeta || listMeta.sourceKey !== "sidebar_sections") {
            return;
          }
          seenFieldKeys.add(fieldKey);
          candidates.push({
            key: fieldKey,
            label: String((field && field.label) || fieldKey).trim(),
            listSourceKey: String(listMeta.sourceKey || "").trim()
          });
        });
      });

      if (!candidates.length) {
        return "";
      }

      const explicitSessionCandidate = candidates.find((candidate) => {
        const lookupValue = normalizeLookupText(`${candidate.key} ${candidate.label}`);
        return lookupValue.includes("sessao");
      });

      return explicitSessionCandidate || candidates[0];
    }

    function normalizeDynamicProcessSelectOptionRowsV1(rawOptions) {
      if (!Array.isArray(rawOptions)) {
        return [];
      }

      return rawOptions
        .map((rawOption) => {
          if (rawOption && typeof rawOption === "object" && !Array.isArray(rawOption)) {
            const value = String(rawOption.value || rawOption.label || "").trim();
            const label = String(rawOption.label || rawOption.value || "").trim();
            if (!value && !label) {
              return null;
            }
            return {
              value,
              label,
              menuKey: normalizeMenuKey(rawOption.menuKey || rawOption.menu_key),
              sectionKey: normalizeMenuKey(rawOption.sectionKey || rawOption.section_key),
              sectionLabel: String(rawOption.sectionLabel || rawOption.section_label || "").trim(),
              isAllOption: Boolean(rawOption.isAllOption)
            };
          }

          const optionValue = String(rawOption || "").trim();
          if (!optionValue) {
            return null;
          }
          return {
            value: optionValue,
            label: optionValue,
            menuKey: "",
            sectionKey: "",
            sectionLabel: "",
            isAllOption: false
          };
        })
        .filter(Boolean);
    }

    function normalizeDynamicProcessTableKeyV1(rawValue) {
      return normalizeLookupText(rawValue)
        .replace(/[^a-z0-9_]+/g, "_")
        .replace(/_+/g, "_")
        .replace(/^_|_$/g, "");
    }

    function extractDynamicProcessTableSourceKeyV1(listSourceKey) {
      const cleanSourceKey = String(listSourceKey || "")
        .trim()
        .toLowerCase();
      if (!cleanSourceKey) {
        return "";
      }
      if (cleanSourceKey.indexOf("table:") === 0) {
        return normalizeDynamicProcessTableKeyV1(cleanSourceKey.slice("table:".length));
      }
      if (cleanSourceKey.indexOf("table_") === 0) {
        return normalizeDynamicProcessTableKeyV1(cleanSourceKey.slice("table_".length));
      }
      return "";
    }

    function normalizeDynamicProcessListSourceKeyV1(listSourceKey) {
      const cleanSourceKey = normalizeMenuKey(listSourceKey);
      if (!cleanSourceKey) {
        return "";
      }

      const tableKey = extractDynamicProcessTableSourceKeyV1(cleanSourceKey);
      if (tableKey) {
        return `table_${tableKey}`;
      }

      return cleanSourceKey;
    }

    function isDynamicProcessAutomaticListSourceV1(listSourceKey) {
      const cleanSourceKey = normalizeDynamicProcessListSourceKeyV1(listSourceKey);
      return (
        cleanSourceKey === "users" ||
        cleanSourceKey === "sidebar_sections" ||
        cleanSourceKey === "sidebar_menus_by_section" ||
        cleanSourceKey.indexOf("table_") === 0
      );
    }

    function buildDynamicProcessAllOptionLabelV1(field) {
      const rawLabel = String((field && (field.label || field.key)) || "").trim();
      const labelLookup = normalizeLookupText(rawLabel);
      const sourceKey = normalizeDynamicProcessListSourceKeyV1(field && field.listSourceKey);

      if (labelLookup.includes("subprocess")) {
        return "Todos os subprocessos";
      }
      if (labelLookup.includes("processo")) {
        return "Todos os processos";
      }
      if (labelLookup.includes("sessao")) {
        return "Todas as sessões";
      }
      if (labelLookup.includes("perfil")) {
        return "Todos os perfis";
      }
      if (
        labelLookup.includes("utilizador") ||
        labelLookup.includes("usuario") ||
        labelLookup.includes("user")
      ) {
        return "Todos os utilizadores";
      }
      if (labelLookup.includes("entidade")) {
        return "Todas as entidades";
      }
      if (labelLookup.includes("empresa")) {
        return "Todas as empresas";
      }
      if (labelLookup.includes("departamento")) {
        return "Todos os departamentos";
      }
      if (labelLookup.includes("menu")) {
        return "Todos os menus";
      }
      if (labelLookup.includes("musica")) {
        return "Todas as músicas";
      }

      if (sourceKey === "sidebar_sections") {
        return "Todas as sessões";
      }
      if (sourceKey === "sidebar_menus_by_section") {
        return "Todos os subprocessos";
      }
      if (sourceKey === "users" || sourceKey === "table_users") {
        return "Todos os utilizadores";
      }
      if (sourceKey === "table_profiles" || sourceKey === "table_user_profiles") {
        return "Todos os perfis";
      }
      if (sourceKey === "table_entities") {
        return "Todas as entidades";
      }
      if (sourceKey === "table_departments") {
        return "Todos os departamentos";
      }
      if (sourceKey === "table_members") {
        return "Todos os membros";
      }
      if (sourceKey === "table_roles") {
        return "Todos os perfis";
      }
      if (sourceKey === "table_songs") {
        return "Todas as músicas";
      }

      if (rawLabel) {
        return `Todos os valores de ${rawLabel.toLowerCase()}`;
      }

      return "Todos";
    }

    function buildDynamicProcessAllOptionRowV1(field) {
      if (!isDynamicProcessAutomaticListSourceV1(field && field.listSourceKey)) {
        return null;
      }

      const allOptionLabel = buildDynamicProcessAllOptionLabelV1(field);
      if (!allOptionLabel) {
        return null;
      }

      return {
        value: allOptionLabel,
        label: allOptionLabel,
        menuKey: "",
        sectionKey: "",
        sectionLabel: "",
        isAllOption: true
      };
    }

    function prependDynamicProcessAllOptionRowV1(field, optionRows) {
      const normalizedRows = normalizeDynamicProcessSelectOptionRowsV1(optionRows);
      const allOptionRow = buildDynamicProcessAllOptionRowV1(field);

      if (!allOptionRow) {
        return normalizedRows;
      }

      const allOptionLookup = normalizeLookupText(allOptionRow.value);
      const filteredRows = normalizedRows.filter((row) => {
        const rowLookup = normalizeLookupText((row && (row.value || row.label)) || "");
        return rowLookup !== allOptionLookup;
      });

      return [allOptionRow].concat(filteredRows);
    }

    function isDynamicProcessAllOptionValueV1(rawValue, field) {
      const allOptionRow = buildDynamicProcessAllOptionRowV1(field);
      if (!allOptionRow) {
        return false;
      }

      const cleanValue = normalizeLookupText(rawValue);
      const allOptionLookup = normalizeLookupText(allOptionRow.value);
      return Boolean(cleanValue) && cleanValue === allOptionLookup;
    }

    function resolveDynamicProcessListOptionsForFieldV1(options) {
      const field = options && options.field ? options.field : {};
      const processSetting = options && options.processSetting ? options.processSetting : {};
      const processValuesByField =
        options && options.processValuesByField ? options.processValuesByField : {};
      const renderedInputsByFieldKey =
        options && options.renderedInputsByFieldKey ? options.renderedInputsByFieldKey : null;
      const sectionFields = Array.isArray(options && options.sectionFields)
        ? options.sectionFields
        : [];
      const processListMetaByKey =
        options && options.processListMetaByKey instanceof Map
          ? options.processListMetaByKey
          : buildProcessListMetaMap(processSetting);

      const listKey = normalizeMenuKey(field && field.listKey);
      const listMeta = processListMetaByKey.get(listKey);
      const normalizedField = Object.assign({}, field, {
        listSourceKey: normalizeDynamicProcessListSourceKeyV1(
          (field && field.listSourceKey) || (listMeta && listMeta.sourceKey) || ""
        )
      });
      const baseOptionRows = normalizeDynamicProcessSelectOptionRowsV1(
        Array.isArray(field && field.listOptionRows) && field.listOptionRows.length
          ? field.listOptionRows
          : Array.isArray(field && field.listOptions)
            ? field.listOptions
            : []
      );

      if (!listMeta) {
        return prependDynamicProcessAllOptionRowV1(normalizedField, baseOptionRows);
      }

      const sourceOptionRows = normalizeDynamicProcessSelectOptionRowsV1(
        Array.isArray(listMeta.optionRows) && listMeta.optionRows.length
          ? listMeta.optionRows
          : Array.isArray(listMeta.items)
            ? listMeta.items
            : baseOptionRows
      );

      if (listMeta.sourceKey !== "sidebar_menus_by_section") {
        return prependDynamicProcessAllOptionRowV1(
          normalizedField,
          sourceOptionRows.length ? sourceOptionRows : baseOptionRows
        );
      }

      const sessionControllerField = resolveDynamicProcessSessionControllerFieldKeyV1(
        sectionFields,
        processSetting,
        processListMetaByKey,
        field && field.key
      );

      if (!sessionControllerField || !sessionControllerField.key) {
        return prependDynamicProcessAllOptionRowV1(
          normalizedField,
          sourceOptionRows.length ? sourceOptionRows : baseOptionRows
        );
      }

      const sessionValue = resolveDynamicProcessListControlValueV1(
        renderedInputsByFieldKey,
        processValuesByField,
        sessionControllerField.key
      );

      if (!sessionValue) {
        return [];
      }

      if (isDynamicProcessAllOptionValueV1(sessionValue, sessionControllerField)) {
        return prependDynamicProcessAllOptionRowV1(normalizedField, sourceOptionRows);
      }

      const sessionLookup = normalizeLookupText(sessionValue);
      const filteredOptions = [];
      const seenOptions = new Set();

      sourceOptionRows.forEach((row) => {
        const optionLabel = String((row && (row.label || row.value)) || "").trim();
        const sectionKeyLookup = normalizeLookupText((row && row.sectionKey) || "");
        const sectionLabelLookup = normalizeLookupText((row && row.sectionLabel) || "");

        if (!optionLabel) {
          return;
        }
        if (sessionLookup !== sectionKeyLookup && sessionLookup !== sectionLabelLookup) {
          return;
        }

        const optionLookup = normalizeLookupText(optionLabel);
        if (seenOptions.has(optionLookup)) {
          return;
        }

        seenOptions.add(optionLookup);
        filteredOptions.push({
          value: String((row && (row.value || row.label)) || "").trim(),
          label: optionLabel,
          menuKey: normalizeMenuKey((row && row.menuKey) || ""),
          sectionKey: normalizeMenuKey((row && row.sectionKey) || ""),
          sectionLabel: String((row && row.sectionLabel) || "").trim(),
          isAllOption: Boolean(row && row.isAllOption)
        });
      });

      return prependDynamicProcessAllOptionRowV1(normalizedField, filteredOptions);
    }

    function replaceDynamicProcessSelectOptionsV1(selectEl, optionRows, selectedValue) {
      if (!selectEl) {
        return;
      }

      const cleanSelectedValue = String(selectedValue || "").trim();
      const normalizedOptionRows = normalizeDynamicProcessSelectOptionRowsV1(optionRows);

      selectEl.innerHTML = "";

      const placeholderEl = document.createElement("option");
      placeholderEl.value = "";
      placeholderEl.textContent = "Selecione";
      selectEl.appendChild(placeholderEl);

      let hasSelectedValue = !cleanSelectedValue;
      normalizedOptionRows.forEach((optionRow) => {
        const optionEl = document.createElement("option");
        optionEl.value = String((optionRow && (optionRow.value || optionRow.label)) || "").trim();
        optionEl.textContent = String(
          (optionRow && (optionRow.label || optionRow.value)) || ""
        ).trim();
        if (optionEl.value === cleanSelectedValue) {
          hasSelectedValue = true;
        }
        selectEl.appendChild(optionEl);
      });

      selectEl.value = hasSelectedValue ? cleanSelectedValue : "";
    }

    function refreshDynamicProcessDependentListFieldsV1(options) {
      const sectionFields = Array.isArray(options && options.sectionFields)
        ? options.sectionFields
        : [];
      const processSetting = options && options.processSetting ? options.processSetting : {};
      const processValuesByField =
        options && options.processValuesByField ? options.processValuesByField : {};
      const renderedInputsByFieldKey =
        options && options.renderedInputsByFieldKey instanceof Map
          ? options.renderedInputsByFieldKey
          : null;
      const processListMetaByKey =
        options && options.processListMetaByKey instanceof Map
          ? options.processListMetaByKey
          : buildProcessListMetaMap(processSetting);
      const preferredValuesByFieldKey =
        options &&
        options.preferredValuesByFieldKey &&
        typeof options.preferredValuesByFieldKey === "object"
          ? options.preferredValuesByFieldKey
          : {};

      if (!renderedInputsByFieldKey || !sectionFields.length) {
        return;
      }

      sectionFields.forEach((field) => {
        const fieldKey = normalizeMenuKey(field && field.key);
        const listKey = normalizeMenuKey(field && (field.listKey || field.list_key));
        const listMeta = processListMetaByKey.get(listKey);
        if (!fieldKey || !listMeta || listMeta.sourceKey !== "sidebar_menus_by_section") {
          return;
        }

        const selectEl = renderedInputsByFieldKey.get(fieldKey);
        if (!selectEl || String(selectEl.tagName || "").toLowerCase() !== "select") {
          return;
        }

        const preferredValue = Object.prototype.hasOwnProperty.call(
          preferredValuesByFieldKey,
          fieldKey
        )
          ? String(preferredValuesByFieldKey[fieldKey] || "").trim()
          : String(selectEl.value || "").trim();

        const nextOptions = resolveDynamicProcessListOptionsForFieldV1({
          field,
          sectionFields,
          processSetting,
          processValuesByField,
          renderedInputsByFieldKey,
          processListMetaByKey
        });

        replaceDynamicProcessSelectOptionsV1(selectEl, nextOptions, preferredValue);
      });
    }

    function collectCurrentDynamicProcessQuantityValues(menuKey) {
      const cleanMenuKey = normalizeMenuKey(menuKey);
      const baseValues =
        menuProcessQuantityValuesMap &&
        menuProcessQuantityValuesMap[cleanMenuKey] &&
        typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
          ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
          : {};
      if (!dynamicProcessEditFormEl) {
        return baseValues;
      }

      const payloadInputs = dynamicProcessEditFormEl.querySelectorAll(
        "[name^='process_quantity_payload__']"
      );
      payloadInputs.forEach((inputEl) => {
        const ruleKey = normalizeMenuKey(
          String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, "")
        );
        if (!ruleKey) {
          return;
        }
        try {
          const parsed = JSON.parse(String(inputEl.value || "[]"));
          baseValues[ruleKey] = normalizeProcessQuantityItems(parsed);
        } catch (error) {
          baseValues[ruleKey] = [];
        }
      });

      const fieldInputs = dynamicProcessEditFormEl.querySelectorAll(
        "[data-process-quantity-field-key]"
      );
      fieldInputs.forEach((controlEl) => {
        const ruleKey = normalizeMenuKey(controlEl.getAttribute("data-process-quantity-rule-key"));
        const itemIndex = Number.parseInt(
          String(controlEl.getAttribute("data-process-quantity-index") || "").trim(),
          10
        );
        const fieldKey = normalizeMenuKey(
          controlEl.getAttribute("data-process-quantity-field-key")
        );
        if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0) {
          return;
        }
        if (!Array.isArray(baseValues[ruleKey])) {
          baseValues[ruleKey] = [];
        }
        while (baseValues[ruleKey].length <= itemIndex) {
          baseValues[ruleKey].push({});
        }
        const itemValues = baseValues[ruleKey][itemIndex];
        if (controlEl.type === "checkbox") {
          itemValues[fieldKey] = controlEl.checked ? "1" : "0";
          return;
        }
        itemValues[fieldKey] = String(controlEl.value || "").trim();
      });

      return baseValues;
    }

    function syncDynamicProcessQuantityHiddenInputs(menuKey, quantityValuesByRule) {
      if (!dynamicProcessEditFormEl) {
        return;
      }
      dynamicProcessEditFormEl
        .querySelectorAll("[data-process-quantity-payload='1']")
        .forEach((inputEl) => inputEl.remove());

      const cleanMenuKey = normalizeMenuKey(menuKey);
      Object.keys(quantityValuesByRule || {}).forEach((rawRuleKey) => {
        const ruleKey = normalizeMenuKey(rawRuleKey);
        if (!ruleKey) {
          return;
        }
        const hiddenInputEl = document.createElement("input");
        hiddenInputEl.type = "hidden";
        hiddenInputEl.name = `process_quantity_payload__${ruleKey}`;
        hiddenInputEl.value = JSON.stringify(
          normalizeProcessQuantityItems(quantityValuesByRule[ruleKey])
        );
        hiddenInputEl.setAttribute("data-process-quantity-payload", "1");
        hiddenInputEl.setAttribute("data-process-quantity-menu-key", cleanMenuKey);
        hiddenInputEl.setAttribute("data-process-quantity-rule-key", ruleKey);
        dynamicProcessEditFormEl.appendChild(hiddenInputEl);
      });
    }

    function collectCurrentMeuPerfilQuantityValues() {
      const cleanMenuKey = MEU_PERFIL_MENU_KEY;
      const baseValues =
        menuProcessQuantityValuesMap &&
        menuProcessQuantityValuesMap[cleanMenuKey] &&
        typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
          ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
          : {};
      const personalCardEl = document.getElementById("perfil-pessoal-card");
      const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
      if (!formEl) {
        return baseValues;
      }

      formEl.querySelectorAll("[data-meu-perfil-quantity-payload='1']").forEach((inputEl) => {
        const ruleKey = normalizeMenuKey(
          String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, "")
        );
        if (!ruleKey) {
          return;
        }
        try {
          baseValues[ruleKey] = normalizeProcessQuantityItems(
            JSON.parse(String(inputEl.value || "[]"))
          );
        } catch (error) {
          baseValues[ruleKey] = [];
        }
      });

      formEl.querySelectorAll("[data-meu-perfil-quantity-field-key]").forEach((controlEl) => {
        const ruleKey = normalizeMenuKey(
          controlEl.getAttribute("data-meu-perfil-quantity-rule-key")
        );
        const fieldKey = normalizeMenuKey(
          controlEl.getAttribute("data-meu-perfil-quantity-field-key")
        );
        const itemIndex = Number.parseInt(
          String(controlEl.getAttribute("data-meu-perfil-quantity-index") || "").trim(),
          10
        );
        if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0) {
          return;
        }
        if (!Array.isArray(baseValues[ruleKey])) {
          baseValues[ruleKey] = [];
        }
        while (baseValues[ruleKey].length <= itemIndex) {
          baseValues[ruleKey].push({});
        }
        if (controlEl.type === "checkbox") {
          baseValues[ruleKey][itemIndex][fieldKey] = controlEl.checked ? "1" : "0";
          return;
        }
        baseValues[ruleKey][itemIndex][fieldKey] = String(controlEl.value || "").trim();
      });

      return baseValues;
    }

    function syncMeuPerfilQuantityHiddenInputs(quantityValuesByRule) {
      const personalCardEl = document.getElementById("perfil-pessoal-card");
      const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
      if (!formEl) {
        return;
      }

      formEl
        .querySelectorAll("[data-meu-perfil-quantity-payload='1']")
        .forEach((inputEl) => inputEl.remove());

      if (window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE) {
        return;
      }

      Object.keys(quantityValuesByRule || {}).forEach((rawRuleKey) => {
        const ruleKey = normalizeMenuKey(rawRuleKey);
        if (!ruleKey) {
          return;
        }
        const hiddenInputEl = document.createElement("input");
        hiddenInputEl.type = "hidden";
        hiddenInputEl.name = `process_quantity_payload__${ruleKey}`;
        hiddenInputEl.value = JSON.stringify(
          normalizeProcessQuantityItems(quantityValuesByRule[ruleKey])
        );
        hiddenInputEl.setAttribute("data-meu-perfil-quantity-payload", "1");
        formEl.appendChild(hiddenInputEl);
      });
    }

    function renderMeuPerfilQuantityGroups() {
      if (
        window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE &&
        window.__APPVERBO_QUANTITY_READONLY_RENDERER_V2_ACTIVE
      ) {
        return;
      }

      const personalCardEl = document.getElementById("perfil-pessoal-card");
      const readonlyGridEl = personalCardEl
        ? personalCardEl.querySelector(".profile-readonly .personal-grid")
        : null;
      const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
      const editGridEl = formEl ? formEl.querySelector(".personal-grid") : null;
      const useV4QuantityEditor = Boolean(window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE);
      const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
      const normalizedRules = normalizeProcessQuantityRules(
        setting && setting.process_quantity_fields
      );
      if (!readonlyGridEl && !editGridEl) {
        return;
      }

      if (readonlyGridEl) {
        readonlyGridEl
          .querySelectorAll("[data-meu-perfil-quantity-generated='1']")
          .forEach((node) => node.remove());
      }
      if (editGridEl && !useV4QuantityEditor) {
        editGridEl
          .querySelectorAll("[data-meu-perfil-quantity-generated='1']")
          .forEach((node) => node.remove());
      }

      if (!setting || !normalizedRules.length) {
        syncMeuPerfilQuantityHiddenInputs({});
        return;
      }

      const processValuesByField = collectCurrentMeuPerfilProcessValues();
      const quantityValuesByRule = collectCurrentMeuPerfilQuantityValues();
      const nextQuantityValuesByRule = { ...quantityValuesByRule };
      const optionMetaByKey = buildProcessOptionMetaMap(setting);
      const activeSectionKey = normalizeMenuKey(
        meuPerfilSelectedProfileSection ||
          (profilePersonalSections[0] && profilePersonalSections[0].key) ||
          ""
      );

      normalizedRules.forEach((rule) => {
        const ruleSectionKey = normalizeMenuKey(rule.headerKey || activeSectionKey || "");
        if (ruleSectionKey && activeSectionKey && ruleSectionKey !== activeSectionKey) {
          return;
        }
        const readOnlyAnchorEl = readonlyGridEl
          ? readonlyGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`)
          : null;
        const editAnchorEl = editGridEl
          ? editGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`)
          : null;

        const sourceValueRaw = Number.parseInt(
          String(processValuesByField[rule.quantityFieldKey] || "").trim(),
          10
        );
        const desiredCount = Number.isFinite(sourceValueRaw)
          ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
          : 0;
        const sourceIndex = profilePersonalVisibleFields.indexOf(rule.quantityFieldKey);
        const baseOrder =
          sourceIndex >= 0
            ? (sourceIndex + 1) * 10
            : (profilePersonalVisibleFields.length + 1) * 10;
        if (readOnlyAnchorEl) {
          readOnlyAnchorEl.style.order = String(baseOrder);
        }
        if (editAnchorEl) {
          editAnchorEl.style.order = String(baseOrder);
        }
        const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
        const nextItems = [];
        for (let index = 0; index < desiredCount; index += 1) {
          nextItems.push(
            existingItems[index] && typeof existingItems[index] === "object"
              ? { ...existingItems[index] }
              : {}
          );
        }
        nextQuantityValuesByRule[rule.key] = nextItems;

        if (readonlyGridEl && nextItems.length) {
          const groupEl = document.createElement("div");
          groupEl.className = "personal-item";
          groupEl.style.gridColumn = "1 / -1";
          groupEl.style.order = String(baseOrder + 1);
          groupEl.setAttribute("data-profile-section-pane", ruleSectionKey || "");
          groupEl.setAttribute("data-meu-perfil-quantity-generated", "1");

          const titleEl = document.createElement("span");
          titleEl.className = "personal-label";
          titleEl.textContent = rule.label;
          groupEl.appendChild(titleEl);

          nextItems.forEach((itemValues, index) => {
            const itemWrapEl = document.createElement("div");
            itemWrapEl.className = "dynamic-process-quantity-item";
            itemWrapEl.style.marginTop = index === 0 ? "8px" : "12px";

            const itemHeadingEl = document.createElement("strong");
            itemHeadingEl.className = "personal-value";
            itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
            itemWrapEl.appendChild(itemHeadingEl);

            rule.repeatedFieldKeys.forEach((fieldKey) => {
              const fieldMeta = optionMetaByKey.get(fieldKey) || {};
              const valueRowEl = document.createElement("div");
              valueRowEl.className = "dynamic-process-quantity-value-row";

              const valueLabelEl = document.createElement("span");
              valueLabelEl.className = "dynamic-process-quantity-value-label";
              valueLabelEl.textContent = `${fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey}:`;

              const rawValue = String(itemValues[fieldKey] || "").trim();
              const valueTextEl = document.createElement("strong");
              valueTextEl.className = "personal-value";
              valueTextEl.textContent =
                normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
                  ? isTruthyFlagValue(rawValue)
                    ? "Sim"
                    : "Não"
                  : rawValue || "-";

              valueRowEl.appendChild(valueLabelEl);
              valueRowEl.appendChild(valueTextEl);
              itemWrapEl.appendChild(valueRowEl);
            });

            groupEl.appendChild(itemWrapEl);
          });

          if (readOnlyAnchorEl && readOnlyAnchorEl.parentNode === readonlyGridEl) {
            readonlyGridEl.insertBefore(groupEl, readOnlyAnchorEl.nextSibling);
          } else {
            readonlyGridEl.appendChild(groupEl);
          }
        }

        if (editGridEl && !useV4QuantityEditor && nextItems.length) {
          const blockEl = document.createElement("div");
          blockEl.className = "field full dynamic-process-quantity-editor-block";
          blockEl.style.order = String(baseOrder + 1);
          blockEl.setAttribute("data-profile-section-pane", ruleSectionKey || "");
          blockEl.setAttribute("data-meu-perfil-quantity-generated", "1");
          blockEl.setAttribute("data-meu-perfil-quantity-source-key", rule.quantityFieldKey);

          const titleEl = document.createElement("label");
          titleEl.className = "dynamic-process-quantity-title";
          titleEl.textContent = rule.label;
          blockEl.appendChild(titleEl);

          nextItems.forEach((itemValues, index) => {
            const itemWrapEl = document.createElement("div");
            itemWrapEl.className = "dynamic-process-quantity-item-edit";

            const itemHeadingEl = document.createElement("h4");
            itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
            itemWrapEl.appendChild(itemHeadingEl);

            const itemGridEl = document.createElement("div");
            itemGridEl.className = "grid settings-general-grid";

            rule.repeatedFieldKeys.forEach((fieldKey) => {
              const fieldMeta = optionMetaByKey.get(fieldKey) || {};
              const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
              const fieldContainerEl = document.createElement("div");
              fieldContainerEl.className = "field";

              const inputId = `meu_perfil_quantity_${rule.key}_${index}_${fieldKey}`.replace(
                /[^a-z0-9_]+/gi,
                "_"
              );
              const currentValue = String(itemValues[fieldKey] || "").trim();
              const labelEl = document.createElement("label");
              labelEl.setAttribute("for", inputId);
              labelEl.textContent = fieldMeta.isRequired
                ? `${fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey} *`
                : fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey;
              fieldContainerEl.appendChild(labelEl);

              let controlEl = null;
              if (fieldType === "flag") {
                const wrapperEl = document.createElement("label");
                wrapperEl.className = "profile-custom-flag-control";
                controlEl = document.createElement("input");
                controlEl.type = "checkbox";
                controlEl.value = "1";
                controlEl.checked = isTruthyFlagValue(currentValue);
                wrapperEl.appendChild(controlEl);
                const spanEl = document.createElement("span");
                spanEl.textContent = "Ativo";
                wrapperEl.appendChild(spanEl);
                fieldContainerEl.appendChild(wrapperEl);
              } else if (fieldType === "list") {
                controlEl = document.createElement("select");
                const placeholderEl = document.createElement("option");
                placeholderEl.value = "";
                placeholderEl.textContent = "Selecione";
                controlEl.appendChild(placeholderEl);
                prependDynamicProcessAllOptionRowV1(
                  fieldMeta,
                  Array.isArray(fieldMeta.listOptionRows) && fieldMeta.listOptionRows.length
                    ? fieldMeta.listOptionRows
                    : Array.isArray(fieldMeta.listOptions)
                      ? fieldMeta.listOptions
                      : []
                ).forEach((optionRow) => {
                  const optionEl = document.createElement("option");
                  optionEl.value = String(
                    (optionRow && (optionRow.value || optionRow.label)) || ""
                  ).trim();
                  optionEl.textContent = String(
                    (optionRow && (optionRow.label || optionRow.value)) || ""
                  ).trim();
                  optionEl.selected = optionEl.value === currentValue;
                  controlEl.appendChild(optionEl);
                });
                fieldContainerEl.appendChild(controlEl);
              } else {
                controlEl = document.createElement("input");
                controlEl.type =
                  fieldType === "email"
                    ? "email"
                    : fieldType === "phone"
                      ? "tel"
                      : fieldType === "number"
                        ? "number"
                        : fieldType === "date"
                          ? "date"
                          : "text";
                controlEl.value = currentValue;
                if (fieldType === "date" && !currentValue) {
                  controlEl.placeholder = "dd/mm/aaaa";
                }
                if (fieldMeta.size && processTextualTypes.has(fieldType)) {
                  controlEl.maxLength = Number(fieldMeta.size) || 255;
                }
                fieldContainerEl.appendChild(controlEl);
              }

              if (!controlEl) {
                return;
              }
              controlEl.id = inputId;
              controlEl.name = `process_quantity_field__${rule.key}__${index}__${fieldKey}`;
              if (fieldMeta.isRequired && fieldType !== "flag") {
                controlEl.required = true;
              }
              controlEl.setAttribute("data-meu-perfil-quantity-rule-key", rule.key);
              controlEl.setAttribute("data-meu-perfil-quantity-index", String(index));
              controlEl.setAttribute("data-meu-perfil-quantity-field-key", fieldKey);
              ["input", "change"].forEach((eventName) => {
                controlEl.addEventListener(eventName, () => {
                  syncMeuPerfilQuantityHiddenInputs(collectCurrentMeuPerfilQuantityValues());
                });
              });

              itemGridEl.appendChild(fieldContainerEl);
            });

            itemWrapEl.appendChild(itemGridEl);
            blockEl.appendChild(itemWrapEl);
          });

          if (editAnchorEl && editAnchorEl.parentNode === editGridEl) {
            editGridEl.insertBefore(blockEl, editAnchorEl.nextSibling);
          } else {
            editGridEl.appendChild(blockEl);
          }
        }
      });

      if (!useV4QuantityEditor) {
        syncMeuPerfilQuantityHiddenInputs(nextQuantityValuesByRule);
      }
      if (typeof window.reorderMeuPerfilProfileFields === "function") {
        window.reorderMeuPerfilProfileFields();
      }
    }

    function renderDynamicProcessQuantityGroups(
      menuKey,
      setting,
      selectedSection,
      sectionFields,
      processValuesByField,
      processQuantityValuesByRule
    ) {
      const cleanMenuKey = normalizeMenuKey(menuKey);
      const normalizedRules = normalizeProcessQuantityRules(
        setting && setting.process_quantity_fields
      );
      if (!normalizedRules.length) {
        syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
        return;
      }

      const selectedSectionKey =
        normalizeMenuKey(selectedSection && selectedSection.key) || "__geral__";
      const optionMetaByKey = buildProcessOptionMetaMap(setting);
      const currentSectionFieldKeys = new Set(
        Array.isArray(sectionFields)
          ? sectionFields.map((field) => normalizeMenuKey(field && field.key)).filter(Boolean)
          : []
      );
      const rulesForSection = normalizedRules.filter((rule) => {
        if (rule.headerKey) {
          return rule.headerKey === selectedSectionKey;
        }
        return currentSectionFieldKeys.has(rule.quantityFieldKey);
      });

      if (!rulesForSection.length) {
        syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, processQuantityValuesByRule || {});
        return;
      }

      const nextQuantityValuesByRule = {
        ...(processQuantityValuesByRule && typeof processQuantityValuesByRule === "object"
          ? processQuantityValuesByRule
          : {})
      };

      rulesForSection.forEach((rule) => {
        const sourceValueRaw = Number.parseInt(
          String(processValuesByField[rule.quantityFieldKey] || "").trim(),
          10
        );
        const desiredCount = Number.isFinite(sourceValueRaw)
          ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
          : 0;
        const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
        const nextItems = [];

        for (let index = 0; index < desiredCount; index += 1) {
          nextItems.push(
            existingItems[index] && typeof existingItems[index] === "object"
              ? { ...existingItems[index] }
              : {}
          );
        }

        nextQuantityValuesByRule[rule.key] = nextItems;

        if (dynamicProcessReadOnlyGridEl) {
          const readOnlyBlockEl = document.createElement("div");
          readOnlyBlockEl.className = "dynamic-process-quantity-group";

          const readOnlyTitleEl = document.createElement("div");
          readOnlyTitleEl.className = "dynamic-process-quantity-title";
          readOnlyTitleEl.textContent = rule.label;
          readOnlyBlockEl.appendChild(readOnlyTitleEl);

          if (!nextItems.length) {
            const emptyEl = document.createElement("p");
            emptyEl.className = "empty";
            emptyEl.textContent = `Sem ${String(rule.itemLabel || "item").toLowerCase()}s registados.`;
            readOnlyBlockEl.appendChild(emptyEl);
          } else {
            nextItems.forEach((itemValues, index) => {
              const itemCardEl = document.createElement("div");
              itemCardEl.className = "personal-item dynamic-process-quantity-item";

              const itemLabelEl = document.createElement("span");
              itemLabelEl.className = "personal-label";
              itemLabelEl.textContent = `${rule.itemLabel} ${index + 1}`;
              itemCardEl.appendChild(itemLabelEl);

              rule.repeatedFieldKeys.forEach((fieldKey) => {
                const fieldMeta = optionMetaByKey.get(fieldKey) || {};
                const valueRowEl = document.createElement("div");
                valueRowEl.className = "dynamic-process-quantity-value-row";

                const valueLabelEl = document.createElement("span");
                valueLabelEl.className = "dynamic-process-quantity-value-label";
                valueLabelEl.textContent = `${fieldMeta.label || fieldKey}:`;

                const rawValue = String(itemValues[fieldKey] || "").trim();
                const valueTextEl = document.createElement("strong");
                valueTextEl.className = "personal-value";
                valueTextEl.textContent =
                  normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
                    ? isTruthyFlagValue(rawValue)
                      ? "Sim"
                      : "Não"
                    : rawValue || "-";

                valueRowEl.appendChild(valueLabelEl);
                valueRowEl.appendChild(valueTextEl);
                itemCardEl.appendChild(valueRowEl);
              });

              readOnlyBlockEl.appendChild(itemCardEl);
            });
          }

          dynamicProcessReadOnlyGridEl.appendChild(readOnlyBlockEl);
        }

        if (dynamicProcessEditGridEl) {
          const editBlockEl = document.createElement("div");
          editBlockEl.className = "field full dynamic-process-quantity-editor-block";
          editBlockEl.dataset.processQuantityRuleKey = rule.key;

          const blockTitleEl = document.createElement("label");
          blockTitleEl.className = "dynamic-process-quantity-title";
          blockTitleEl.textContent = rule.label;
          editBlockEl.appendChild(blockTitleEl);

          if (!nextItems.length) {
            const emptyEl = document.createElement("p");
            emptyEl.className = "empty";
            emptyEl.textContent = `Informe ${rule.quantityFieldKey === rule.itemLabel ? "uma quantidade" : "a quantidade"} para gerar blocos.`;
            editBlockEl.appendChild(emptyEl);
          } else {
            nextItems.forEach((itemValues, index) => {
              const itemWrapEl = document.createElement("div");
              itemWrapEl.className = "dynamic-process-quantity-item-edit";

              const itemHeadingEl = document.createElement("h4");
              itemHeadingEl.textContent = `${rule.itemLabel} ${index + 1}`;
              itemWrapEl.appendChild(itemHeadingEl);

              const itemGridEl = document.createElement("div");
              itemGridEl.className = "grid settings-general-grid";

              rule.repeatedFieldKeys.forEach((fieldKey) => {
                const fieldMeta = optionMetaByKey.get(fieldKey) || {};
                const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
                const fieldContainerEl = document.createElement("div");
                fieldContainerEl.className = "field";

                const inputId =
                  `dynamic_quantity_${cleanMenuKey}_${rule.key}_${index}_${fieldKey}`.replace(
                    /[^a-z0-9_]+/gi,
                    "_"
                  );
                const currentValue = String(itemValues[fieldKey] || "").trim();

                const labelEl = document.createElement("label");
                labelEl.setAttribute("for", inputId);
                labelEl.textContent = fieldMeta.isRequired
                  ? `${fieldMeta.label || fieldKey} *`
                  : fieldMeta.label || fieldKey;
                fieldContainerEl.appendChild(labelEl);

                if (fieldType === "flag") {
                  const wrapperEl = document.createElement("label");
                  wrapperEl.className = "profile-custom-flag-control";

                  const inputEl = document.createElement("input");
                  inputEl.id = inputId;
                  inputEl.type = "checkbox";
                  inputEl.value = "1";
                  inputEl.checked = isTruthyFlagValue(currentValue);
                  inputEl.defaultChecked = inputEl.checked;
                  inputEl.setAttribute("data-process-quantity-rule-key", rule.key);
                  inputEl.setAttribute("data-process-quantity-index", String(index));
                  inputEl.setAttribute("data-process-quantity-field-key", fieldKey);

                  const textEl = document.createElement("span");
                  textEl.textContent = "Ativo";

                  wrapperEl.appendChild(inputEl);
                  wrapperEl.appendChild(textEl);
                  fieldContainerEl.appendChild(wrapperEl);
                } else if (fieldType === "list") {
                  const selectEl = document.createElement("select");
                  selectEl.id = inputId;
                  selectEl.required = Boolean(fieldMeta.isRequired);
                  selectEl.setAttribute("data-process-quantity-rule-key", rule.key);
                  selectEl.setAttribute("data-process-quantity-index", String(index));
                  selectEl.setAttribute("data-process-quantity-field-key", fieldKey);

                  const defaultOptionEl = document.createElement("option");
                  defaultOptionEl.value = "";
                  defaultOptionEl.textContent = "Selecione";
                  selectEl.appendChild(defaultOptionEl);

                  prependDynamicProcessAllOptionRowV1(
                    fieldMeta,
                    Array.isArray(fieldMeta.listOptionRows) && fieldMeta.listOptionRows.length
                      ? fieldMeta.listOptionRows
                      : Array.isArray(fieldMeta.listOptions)
                        ? fieldMeta.listOptions
                        : []
                  ).forEach((optionRow) => {
                    const optionEl = document.createElement("option");
                    optionEl.value = String(
                      (optionRow && (optionRow.value || optionRow.label)) || ""
                    );
                    optionEl.textContent = String(
                      (optionRow && (optionRow.label || optionRow.value)) || ""
                    );
                    if (optionEl.value === currentValue) {
                      optionEl.selected = true;
                    }
                    selectEl.appendChild(optionEl);
                  });

                  fieldContainerEl.appendChild(selectEl);
                } else {
                  const inputEl = document.createElement("input");
                  const normalizedValue =
                    fieldType === "date" ? normalizeDateInputValue(currentValue) : currentValue;
                  inputEl.id = inputId;
                  inputEl.type = getDynamicProcessInputType(fieldType);
                  inputEl.value = normalizedValue;
                  inputEl.defaultValue = normalizedValue;
                  inputEl.required = Boolean(fieldMeta.isRequired);
                  if (fieldType === "number") {
                    inputEl.inputMode = "numeric";
                  }
                  if (
                    typeof fieldMeta.size === "number" &&
                    fieldMeta.size > 0 &&
                    processTextualTypes.has(fieldType)
                  ) {
                    inputEl.maxLength = fieldMeta.size;
                  }
                  inputEl.setAttribute("data-process-quantity-rule-key", rule.key);
                  inputEl.setAttribute("data-process-quantity-index", String(index));
                  inputEl.setAttribute("data-process-quantity-field-key", fieldKey);
                  fieldContainerEl.appendChild(inputEl);
                }

                itemGridEl.appendChild(fieldContainerEl);
              });

              itemWrapEl.appendChild(itemGridEl);
              editBlockEl.appendChild(itemWrapEl);
            });
          }

          dynamicProcessEditGridEl.appendChild(editBlockEl);
        }
      });

      syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, nextQuantityValuesByRule);
    }

    function collectCurrentDynamicProcessValues(menuKey) {
      const cleanMenuKey = normalizeMenuKey(menuKey);
      const baseValues =
        menuProcessValuesMap &&
        menuProcessValuesMap[cleanMenuKey] &&
        typeof menuProcessValuesMap[cleanMenuKey] === "object"
          ? { ...menuProcessValuesMap[cleanMenuKey] }
          : {};
      if (!dynamicProcessEditFormEl) {
        return baseValues;
      }

      const controls = dynamicProcessEditFormEl.querySelectorAll("[name^='process_field__']");
      controls.forEach((controlEl) => {
        const fieldKey = normalizeMenuKey(
          String(controlEl.getAttribute("name") || "").replace(/^process_field__/, "")
        );
        if (!fieldKey) {
          return;
        }
        if (controlEl.type === "checkbox") {
          baseValues[fieldKey] = controlEl.checked ? "1" : "0";
          return;
        }
        baseValues[fieldKey] = String(controlEl.value || "").trim();
      });

      return baseValues;
    }

    function renderDynamicProcessCard(menuKey, sectionKey, options = {}) {
      if (!dynamicProcessCardEl) {
        return;
      }
      const preserveInteractionState = Boolean(options && options.preserveInteractionState);
      const wasEditing = dynamicProcessCardEl.classList.contains("editing");
      const wasCreateCardEditing = dynamicProcessCreateCardEl
        ? dynamicProcessCreateCardEl.classList.contains("is-editing")
        : false;
      const previousHistoryAction = dynamicProcessHistoryActionInputEl
        ? String(dynamicProcessHistoryActionInputEl.value || "").trim()
        : "";
      const previousHistoryRecordId = dynamicProcessHistoryRecordIdInputEl
        ? String(dynamicProcessHistoryRecordIdInputEl.value || "").trim()
        : "";
      const previousSubmitLabel = dynamicProcessSubmitBtnEl
        ? String(dynamicProcessSubmitBtnEl.textContent || "").trim()
        : "";
      const cleanMenuKey = normalizeMenuKey(menuKey);
      const dynamicProcessReadOnlyMode = readOnlyDynamicProcessMenuKeys.has(cleanMenuKey);
      const useEmpresaFourColumnsLayoutV1 = cleanMenuKey === "empresa";
      dynamicProcessCardEl.classList.toggle(
        "appverbo-empresa-layout-4cols-v1",
        useEmpresaFourColumnsLayoutV1
      );
      const dynamicProcessHeaderEditToggleEl =
        typeof document !== "undefined"
          ? document.getElementById("dynamic-process-header-edit-toggle")
          : null;
      const useInlineHeaderEditToggle = cleanMenuKey === "empresa";
      const menuData = dynamicProcessDataByMenu[cleanMenuKey];
      const processSetting = getSidebarMenuSetting(cleanMenuKey);
      const processListMetaByKey = buildProcessListMetaMap(processSetting);
      const currentProcessValuesByField = collectCurrentDynamicProcessValues(cleanMenuKey);
      const currentProcessQuantityValuesByRule =
        collectCurrentDynamicProcessQuantityValues(cleanMenuKey);
      if (!preserveInteractionState) {
        dynamicProcessCardEl.classList.remove("editing");
        dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
      }
      dynamicProcessCardEl.classList.remove("dynamic-process-open");
      dynamicProcessCardEl.classList.remove("dynamic-process-history-mode");
      if (dynamicProcessCreateCardEl && !preserveInteractionState) {
        dynamicProcessCreateCardEl.classList.remove("is-editing");
      }

      if (dynamicProcessReadOnlyGridEl) {
        dynamicProcessReadOnlyGridEl.innerHTML = "";
      }
      if (dynamicProcessEditGridEl) {
        dynamicProcessEditGridEl.innerHTML = "";
      }
      if (dynamicProcessHistoryBlockEl) {
        dynamicProcessHistoryBlockEl.style.display = "none";
      }
      if (dynamicProcessHistoryActiveCardEl) {
        dynamicProcessHistoryActiveCardEl.style.display = "none";
      }
      if (dynamicProcessHistoryInactiveCardEl) {
        dynamicProcessHistoryInactiveCardEl.style.display = "none";
      }

      if (!menuData) {
        if (dynamicProcessTitleEl) {
          dynamicProcessTitleEl.textContent = "Processo";
        }
        if (dynamicProcessDescriptionEl) {
          dynamicProcessDescriptionEl.textContent = "Campos configurados para este processo.";
        }
        if (dynamicProcessSectionLabelEl) {
          dynamicProcessSectionLabelEl.textContent = "";
        }
        if (dynamicProcessMenuKeyInputEl) {
          dynamicProcessMenuKeyInputEl.value = "";
          dynamicProcessMenuKeyInputEl.defaultValue = "";
        }
        if (dynamicProcessSectionKeyInputEl) {
          dynamicProcessSectionKeyInputEl.value = "";
          dynamicProcessSectionKeyInputEl.defaultValue = "";
        }
        if (dynamicProcessEditToggleEl) {
          dynamicProcessEditToggleEl.style.display = "none";
        }
        if (dynamicProcessHeaderEditToggleEl) {
          dynamicProcessHeaderEditToggleEl.style.display = "none";
        }
        if (dynamicProcessCreateCardEl) {
          dynamicProcessCreateCardEl.style.display = "none";
        }
        if (dynamicProcessHistoryActionInputEl) {
          dynamicProcessHistoryActionInputEl.value =
            preserveInteractionState && previousHistoryAction ? previousHistoryAction : "create";
        }
        if (dynamicProcessHistoryRecordIdInputEl) {
          dynamicProcessHistoryRecordIdInputEl.value = preserveInteractionState
            ? previousHistoryRecordId
            : "";
        }
        if (dynamicProcessSubmitBtnEl) {
          dynamicProcessSubmitBtnEl.textContent =
            preserveInteractionState && previousSubmitLabel ? previousSubmitLabel : "Guardar";
        }
        if (dynamicProcessEmptyEl) {
          dynamicProcessEmptyEl.style.display = "";
          dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
        }
        syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
        return;
      }

      const hiddenTargets = getHiddenProcessTargets(
        processSetting ? processSetting.process_subsequent_fields : [],
        currentProcessValuesByField
      );
      const fieldSectionMap = getFieldSectionMap(processSetting);
      const visibleSections = menuData.sections.filter(
        (section) => !hiddenTargets.has(normalizeMenuKey(section && section.key))
      );
      if (itemsEl) {
        const submenuLinks = itemsEl.querySelectorAll(
          ".submenu-item[data-dynamic-process-section]"
        );
        submenuLinks.forEach((linkEl) => {
          const linkSectionKey = normalizeMenuKey(linkEl.dataset.dynamicProcessSection);
          linkEl.style.display = hiddenTargets.has(linkSectionKey) ? "none" : "";
        });
      }

      const cleanSectionKey = String(
        sectionKey || selectedDynamicSectionByMenu[cleanMenuKey] || ""
      ).trim();
      let selectedSection = visibleSections.find(
        (section) => String(section.key || "") === cleanSectionKey
      );
      if (!selectedSection) {
        selectedSection = visibleSections[0];
      }
      if (selectedSection) {
        selectedDynamicSectionByMenu[cleanMenuKey] = String(selectedSection.key || "");
        if (itemsEl) {
          const selectedLinkEl = itemsEl.querySelector(
            `.submenu-item[data-dynamic-process-section="${String(selectedSection.key || "").replace(/"/g, '\\"')}"]`
          );
          if (selectedLinkEl) {
            setActiveSubmenu("#dynamic-process-card", selectedLinkEl);
          }
        }
      }

      const menuLabel = toSentenceCaseText(menuData.menuLabel || "Processo");
      const sectionLabel = selectedSection
        ? toSentenceCaseText(selectedSection.label || "Campos")
        : "Campos";
      const cleanSectionLabel = normalizeLookupText(sectionLabel).replace(/\s+/g, " ");
      const normalizedSectionKeyForLayout = normalizeMenuKey(
        selectedSection ? selectedSection.key || "" : ""
      );
      const forceSingleRowLayout =
        cleanSectionLabel === "dados de extrato" ||
        cleanSectionLabel === "dados-de-extrato" ||
        cleanSectionLabel === "dados_de_extrato" ||
        cleanSectionLabel === "dadosdeextrato" ||
        normalizedSectionKeyForLayout === "dados_de_extrato" ||
        normalizedSectionKeyForLayout === "dados-de-extrato";
      [dynamicProcessEditGridEl, dynamicProcessReadOnlyGridEl].forEach((gridEl) => {
        if (!gridEl) {
          return;
        }
        gridEl.classList.toggle("appverbo-dynamic-process-single-row-v1", forceSingleRowLayout);
      });
      const absenceProcessMode = isAbsenceProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
      const historyProcessMode = isHistoryProcessMenu(cleanMenuKey, menuLabel, sectionLabel);
      const historyRecordLabels = getHistoryRecordLabels(cleanMenuKey, menuLabel, sectionLabel);
      const stateHistoryMode = historyProcessMode && !absenceProcessMode;
      const showStateField = stateHistoryMode;
      dynamicProcessCardEl.classList.toggle("dynamic-process-open", absenceProcessMode);
      dynamicProcessCardEl.classList.toggle("dynamic-process-history-mode", stateHistoryMode);
      if (!stateHistoryMode) {
        dynamicProcessCardEl.classList.remove("dynamic-process-history-show-readonly");
      }
      if (dynamicProcessReadOnlyEl) {
        if (stateHistoryMode) {
          const showReadOnlyPreview = dynamicProcessCardEl.classList.contains(
            "dynamic-process-history-show-readonly"
          );
          dynamicProcessReadOnlyEl.style.display = showReadOnlyPreview ? "" : "none";
        } else {
          dynamicProcessReadOnlyEl.style.display = "";
        }
      }

      if (dynamicProcessTitleEl) {
        dynamicProcessTitleEl.textContent = sectionLabel || menuLabel;
      }
      if (dynamicProcessDescriptionEl) {
        dynamicProcessDescriptionEl.textContent =
          "Campos visíveis definidos na configuração desta pasta.";
      }
      if (dynamicProcessSectionLabelEl) {
        dynamicProcessSectionLabelEl.textContent = `Pasta: ${menuLabel} | Aba: ${sectionLabel}`;
      }
      if (dynamicProcessMenuKeyInputEl) {
        dynamicProcessMenuKeyInputEl.value = cleanMenuKey;
        dynamicProcessMenuKeyInputEl.defaultValue = cleanMenuKey;
      }
      if (dynamicProcessSectionKeyInputEl) {
        const resolvedSectionKey = String(selectedSection ? selectedSection.key || "" : "");
        dynamicProcessSectionKeyInputEl.value = resolvedSectionKey;
        dynamicProcessSectionKeyInputEl.defaultValue = resolvedSectionKey;
      }
      if (dynamicProcessHistoryActionInputEl) {
        dynamicProcessHistoryActionInputEl.value =
          preserveInteractionState && previousHistoryAction ? previousHistoryAction : "create";
      }
      if (dynamicProcessHistoryRecordIdInputEl) {
        dynamicProcessHistoryRecordIdInputEl.value = preserveInteractionState
          ? previousHistoryRecordId
          : "";
      }
      if (dynamicProcessSubmitBtnEl) {
        dynamicProcessSubmitBtnEl.textContent =
          preserveInteractionState && previousSubmitLabel ? previousSubmitLabel : "Guardar";
      }

      const selectedSectionKey = normalizeMenuKey(selectedSection ? selectedSection.key : "");
      const useAuthorizationProfileFourColumnsLayoutV1 =
        cleanMenuKey === "administrativo" && selectedSectionKey === "custom_perfil_de_autorizacao";
      dynamicProcessCardEl.classList.toggle(
        "appverbo-admin-authorization-layout-4cols-v1",
        useAuthorizationProfileFourColumnsLayoutV1
      );
      const sectionFields =
        selectedSection && Array.isArray(selectedSection.fields)
          ? selectedSection.fields.filter((field) => {
              const fieldKey = normalizeMenuKey(field && field.key);
              const fieldSectionKey = fieldSectionMap.get(fieldKey) || selectedSectionKey;
              return !hiddenTargets.has(fieldKey) && !hiddenTargets.has(fieldSectionKey);
            })
          : [];
      const hasQuantityRulesForSection = normalizeProcessQuantityRules(
        processSetting ? processSetting.process_quantity_fields : []
      ).some((rule) =>
        rule.headerKey
          ? rule.headerKey === selectedSectionKey
          : sectionFields.some(
              (field) => normalizeMenuKey(field && field.key) === rule.quantityFieldKey
            )
      );
      if (!sectionFields.length && !hasQuantityRulesForSection) {
        if (dynamicProcessEditToggleEl) {
          dynamicProcessEditToggleEl.style.display = "none";
        }
        if (dynamicProcessHeaderEditToggleEl) {
          dynamicProcessHeaderEditToggleEl.style.display = "none";
        }
        if (dynamicProcessCreateCardEl) {
          dynamicProcessCreateCardEl.style.display = "none";
        }
        if (dynamicProcessEmptyEl) {
          dynamicProcessEmptyEl.style.display = "";
          dynamicProcessEmptyEl.textContent = "Sem campos configurados para esta aba.";
        }
        if (dynamicProcessHistoryBlockEl) {
          dynamicProcessHistoryBlockEl.style.display = "none";
        }
        if (dynamicProcessHistoryActiveCardEl) {
          dynamicProcessHistoryActiveCardEl.style.display = "none";
        }
        if (dynamicProcessHistoryInactiveCardEl) {
          dynamicProcessHistoryInactiveCardEl.style.display = "none";
        }
        syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, currentProcessQuantityValuesByRule);
        return;
      }

      const shouldShowEditToggle =
        !dynamicProcessReadOnlyMode &&
        !absenceProcessMode &&
        (sectionFields.length || hasQuantityRulesForSection);
      let editToggleLabel = "Editar";
      if (historyProcessMode) {
        const createActionLabel = toSentenceCaseText(
          selectedSection && selectedSection.label
            ? selectedSection.label
            : historyRecordLabels.singular || "registo"
        );
        editToggleLabel = `Criar ${createActionLabel}`;
      }

      if (dynamicProcessEditToggleEl) {
        dynamicProcessEditToggleEl.style.display = shouldShowEditToggle ? "" : "none";
        dynamicProcessEditToggleEl.textContent = editToggleLabel;
      }

      if (dynamicProcessHeaderEditToggleEl) {
        dynamicProcessHeaderEditToggleEl.style.display =
          useInlineHeaderEditToggle && shouldShowEditToggle ? "" : "none";
        dynamicProcessHeaderEditToggleEl.textContent = editToggleLabel;
      }

      if (dynamicProcessCreateCardEl) {
        const showCreateCard = shouldShowEditToggle && !useInlineHeaderEditToggle;
        dynamicProcessCreateCardEl.style.display = showCreateCard ? "" : "none";
        if (!showCreateCard) {
          dynamicProcessCreateCardEl.classList.remove("is-editing");
        } else if (preserveInteractionState && wasCreateCardEditing) {
          dynamicProcessCreateCardEl.classList.add("is-editing");
        }
      }
      if (dynamicProcessEmptyEl) {
        dynamicProcessEmptyEl.style.display = "none";
      }

      const renderedInputsByFieldKey = new Map();
      const initialDynamicProcessListValuesByFieldKey = {};
      const bootstrapEntityInternalNumber = String(
        (window.__APPVERBO_BOOTSTRAP__ || {}).currentEntityInternalNumber || ""
      ).trim();
      const isEntityInternalNumberField = (fieldKey, fieldLabel) => {
        const cleanFieldKey = normalizeMenuKey(fieldKey);
        if (
          cleanFieldKey === "numero_entidade" ||
          cleanFieldKey === "custom_n_cliente" ||
          cleanFieldKey === "entity_internal_number"
        ) {
          return true;
        }
        const cleanFieldLabel = normalizeLookupText(fieldLabel || "");
        return (
          cleanFieldLabel === "nº entidade" ||
          cleanFieldLabel === "numero entidade" ||
          cleanFieldLabel === "numero_entidade" ||
          cleanFieldLabel === "n entidade"
        );
      };
      sectionFields.forEach((field) => {
        const fieldKey = normalizeMenuKey(field.key);
        if (!fieldKey) {
          return;
        }
        const fieldLabel = toSentenceCaseText(field.label || fieldKey);
        const fieldType = normalizeProcessFieldType(field.fieldType);
        const fieldSize = normalizeProcessFieldSize(field.size, fieldType);
        const fieldRequired = Boolean(field.isRequired) && fieldType !== "flag";
        const isEmpresaInternalNumber =
          isEmpresaReadOnlyField(cleanMenuKey, fieldKey) ||
          (cleanMenuKey === "contacto_geral" &&
            (fieldKey === "custom_n_cliente" || fieldKey === "custom_n_user"));
        const isEmpresaLogoUpload = isEmpresaLogoUploadField(cleanMenuKey, fieldKey);
        const isEmpresaLogoCurrent = isEmpresaLogoCurrentField(cleanMenuKey, fieldKey);
        const isContactMembershipImportFileField =
          cleanMenuKey === "contacto_geral" &&
          normalizeMenuKey(selectedSection ? selectedSection.key || "" : "") ===
            "custom_input_ficheiro_header" &&
          normalizeLookupText(field.label || fieldKey).includes("ficheiro");
        const hasLiveFieldValue = Object.prototype.hasOwnProperty.call(
          currentProcessValuesByField,
          fieldKey
        );
        const liveFieldValue = hasLiveFieldValue
          ? String(currentProcessValuesByField[fieldKey] || "").trim()
          : "";
        let readOnlyValue =
          preserveInteractionState && hasLiveFieldValue
            ? liveFieldValue
            : String(field.value || "").trim();
        if (
          isEntityInternalNumberField(fieldKey, fieldLabel) &&
          !readOnlyValue &&
          bootstrapEntityInternalNumber
        ) {
          readOnlyValue = bootstrapEntityInternalNumber;
        }
        if (
          cleanMenuKey === "contacto_geral" &&
          fieldKey === "custom_n_cliente" &&
          !readOnlyValue
        ) {
          readOnlyValue = String(
            window.__APPVERBO_BOOTSTRAP__.currentEntityInternalNumber || ""
          ).trim();
        }
        if (cleanMenuKey === "contacto_geral" && fieldKey === "custom_n_user" && !readOnlyValue) {
          readOnlyValue = "Automático";
        }
        const fieldValue = absenceProcessMode ? "" : readOnlyValue;
        let editDefaultValue = historyProcessMode
          ? preserveInteractionState && hasLiveFieldValue
            ? liveFieldValue
            : ""
          : preserveInteractionState && hasLiveFieldValue
            ? liveFieldValue
            : fieldValue;
        if (
          cleanMenuKey === "contacto_geral" &&
          fieldKey === "custom_n_cliente" &&
          !editDefaultValue
        ) {
          editDefaultValue = String(
            window.__APPVERBO_BOOTSTRAP__.currentEntityInternalNumber || ""
          ).trim();
        }
        if (
          cleanMenuKey === "contacto_geral" &&
          fieldKey === "custom_n_user" &&
          !editDefaultValue
        ) {
          editDefaultValue = "Automático";
        }
        if (
          isEntityInternalNumberField(fieldKey, fieldLabel) &&
          !editDefaultValue &&
          bootstrapEntityInternalNumber
        ) {
          editDefaultValue = bootstrapEntityInternalNumber;
        }
        if (
          cleanMenuKey === "administrativo" &&
          selectedSectionKey === "custom_perfil_de_autorizacao" &&
          fieldKey === "custom_entidade" &&
          !editDefaultValue
        ) {
          editDefaultValue = liveFieldValue || String(
            currentProcessValuesByField["custom_entidade"] || ""
          ).trim();
        }
        if (
          cleanMenuKey === "administrativo" &&
          selectedSectionKey === "custom_perfil_de_autorizacao" &&
          fieldKey === "custom_visibilidade" &&
          !editDefaultValue
        ) {
          editDefaultValue = liveFieldValue || String(
            currentProcessValuesByField["custom_visibilidade"] || ""
          ).trim();
        }

        if (dynamicProcessReadOnlyGridEl) {
          const readOnlyItemEl = document.createElement("div");
          readOnlyItemEl.className = "personal-item";
          readOnlyItemEl.dataset.processFieldKey = fieldKey;

          const labelEl = document.createElement("span");
          labelEl.className = "personal-label";
          labelEl.textContent = fieldLabel;

          const valueEl = document.createElement("strong");
          valueEl.className = "personal-value";
          let handledReadOnlyValue = false;
          if (isEmpresaLogoUpload) {
            valueEl.textContent = "Selecione um ficheiro no modo de edição.";
          } else if (isEmpresaLogoCurrent) {
            if (fieldValue) {
              const logoWrapperEl = document.createElement("div");
              logoWrapperEl.className = "entity-edit-current-logo-preview";

              const logoImageEl = document.createElement("img");
              logoImageEl.className = "entity-edit-current-logo-image";
              logoImageEl.src = fieldValue;
              logoImageEl.alt = "Logo atual da entidade";

              logoWrapperEl.appendChild(logoImageEl);
              readOnlyItemEl.appendChild(labelEl);
              readOnlyItemEl.appendChild(logoWrapperEl);
              handledReadOnlyValue = true;
            } else {
              valueEl.textContent = "-";
            }
          } else if (fieldType === "flag") {
            valueEl.textContent = isTruthyFlagValue(fieldValue) ? "Sim" : "Não";
          } else if (fieldType === "currency") {
            valueEl.textContent = fieldValue ? formatCurrencyValue(fieldValue) : "-";
          } else if (fieldType === "file") {
            valueEl.textContent = "-";
          } else {
            valueEl.textContent = fieldValue || "-";
          }

          if (!handledReadOnlyValue) {
            readOnlyItemEl.appendChild(labelEl);
            readOnlyItemEl.appendChild(valueEl);
          }
          dynamicProcessReadOnlyGridEl.appendChild(readOnlyItemEl);
        }

        if (dynamicProcessEditGridEl) {
          const fieldContainerEl = document.createElement("div");
          fieldContainerEl.className = "field";
          fieldContainerEl.dataset.processFieldKey = fieldKey;

          const inputId =
            `dynamic_process_${cleanMenuKey}_${String(selectedSection ? selectedSection.key || "" : "")}_${fieldKey}`.replace(
              /[^a-z0-9_]+/gi,
              "_"
            );
          const inputName = `process_field__${fieldKey}`;

          const labelEl = document.createElement("label");
          labelEl.setAttribute("for", inputId);
          labelEl.textContent = fieldRequired ? `${fieldLabel} *` : fieldLabel;

          if (isEmpresaLogoCurrent) {
            const hiddenInputEl = document.createElement("input");
            hiddenInputEl.type = "hidden";
            hiddenInputEl.name = inputName;
            hiddenInputEl.value = editDefaultValue;
            hiddenInputEl.defaultValue = editDefaultValue;

            const previewEl = document.createElement("div");
            previewEl.className = "entity-edit-current-logo-preview";

            if (editDefaultValue) {
              const removeInputId = `${inputId}_remove`;

              const removeInputEl = document.createElement("input");
              removeInputEl.id = removeInputId;
              removeInputEl.className = "entity-edit-remove-logo-input";
              removeInputEl.type = "checkbox";
              removeInputEl.name = "process_field__entity_logo_remove";
              removeInputEl.value = "1";

              const removeLabelEl = document.createElement("label");
              removeLabelEl.setAttribute("for", removeInputId);
              removeLabelEl.className = "entity-edit-remove-logo-btn";
              removeLabelEl.title = "Remover logo atual";
              removeLabelEl.setAttribute("aria-label", "Remover logo atual");
              removeLabelEl.innerHTML = "&#10005;";

              const imageEl = document.createElement("img");
              imageEl.className = "entity-edit-current-logo-image";
              imageEl.src = editDefaultValue;
              imageEl.alt = "Logo atual da entidade";

              const removePlaceholderEl = document.createElement("div");
              removePlaceholderEl.className = "entity-edit-remove-logo-placeholder";
              removePlaceholderEl.textContent =
                "Logo marcado para remoção. Clique em Guardar para confirmar.";

              previewEl.appendChild(removeInputEl);
              previewEl.appendChild(removeLabelEl);
              previewEl.appendChild(imageEl);
              previewEl.appendChild(removePlaceholderEl);
            } else {
              const emptyEl = document.createElement("strong");
              emptyEl.className = "personal-value";
              emptyEl.textContent = "-";
              previewEl.appendChild(emptyEl);
            }

            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(previewEl);
            fieldContainerEl.appendChild(hiddenInputEl);
          } else if (isEmpresaLogoUpload) {
            const inputEl = document.createElement("input");
            inputEl.id = inputId;
            inputEl.name = inputName;
            inputEl.type = "file";
            inputEl.accept = "image/png,image/jpeg,image/webp,image/gif,image/svg+xml";
            renderedInputsByFieldKey.set(fieldKey, inputEl);

            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(inputEl);
          } else if (fieldType === "flag") {
            const wrapperEl = document.createElement("label");
            wrapperEl.className = "profile-custom-flag-control";

            const inputEl = document.createElement("input");
            inputEl.id = inputId;
            inputEl.type = "checkbox";
            inputEl.name = inputName;
            inputEl.value = "1";
            inputEl.checked = isTruthyFlagValue(editDefaultValue);
            inputEl.defaultChecked = inputEl.checked;

            const textEl = document.createElement("span");
            textEl.textContent = "Ativo";

            wrapperEl.appendChild(inputEl);
            wrapperEl.appendChild(textEl);
            renderedInputsByFieldKey.set(fieldKey, inputEl);

            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(wrapperEl);
          } else if (fieldType === "list") {
            const selectEl = document.createElement("select");
            selectEl.id = inputId;
            selectEl.name = inputName;
            selectEl.required = fieldRequired;
            initialDynamicProcessListValuesByFieldKey[fieldKey] = editDefaultValue;

            const defaultOptionEl = document.createElement("option");
            defaultOptionEl.value = "";
            defaultOptionEl.textContent = "Selecione";
            selectEl.appendChild(defaultOptionEl);

            const listOptions = resolveDynamicProcessListOptionsForFieldV1({
              field,
              sectionFields,
              processSetting,
              processValuesByField: currentProcessValuesByField,
              renderedInputsByFieldKey,
              processListMetaByKey
            });
            listOptions.forEach((optionRow) => {
              const optionEl = document.createElement("option");
              optionEl.value = String((optionRow && (optionRow.value || optionRow.label)) || "");
              optionEl.textContent = String(
                (optionRow && (optionRow.label || optionRow.value)) || ""
              );
              if (optionEl.value === editDefaultValue) {
                optionEl.selected = true;
              }
              selectEl.appendChild(optionEl);
            });

            renderedInputsByFieldKey.set(fieldKey, selectEl);
            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(selectEl);
          } else if (fieldType === "file") {
            // ── file picker with auto-import ──────────────────────────────────
            const fileInputEl = document.createElement("input");
            fileInputEl.type = "file";
            fileInputEl.accept = ".txt,.csv,.xlsx";
            fileInputEl.className = "appverbo-field-file-input-v1";

            const fileBtnEl = document.createElement("label");
            fileBtnEl.className = "appverbo-field-file-btn-v1";

            const fileNameEl = document.createElement("span");
            fileNameEl.className = "appverbo-field-file-name-v1";
            fileNameEl.textContent = "Selecionar ficheiro...";

            fileBtnEl.appendChild(fileInputEl);
            fileBtnEl.appendChild(fileNameEl);

            const fileFeedbackEl = document.createElement("p");
            fileFeedbackEl.className = "appverbo-field-file-feedback-v1";
            fileFeedbackEl.style.display = "none";

            fileInputEl.addEventListener("change", function () {
              const selectedFile = fileInputEl.files && fileInputEl.files[0];
              if (!selectedFile) return;
              fileNameEl.textContent = selectedFile.name;
              fileFeedbackEl.style.display = "none";
              fileFeedbackEl.className = "appverbo-field-file-feedback-v1";

              const formData = new FormData();
              formData.append("file", selectedFile);
              fileInputEl.disabled = true;
              fileFeedbackEl.textContent = "A importar...";
              fileFeedbackEl.style.display = "";

              fetch("/import/mt940/upload", { method: "POST", body: formData, credentials: "same-origin" })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                  fileInputEl.disabled = false;
                  fileInputEl.value = "";
                  fileNameEl.textContent = "Selecionar ficheiro...";
                  if (data.status === "ok" || data.status === "partial") {
                    fileFeedbackEl.textContent =
                      "Importado: " + data.linhas_inseridas + " registo(s). " +
                      data.duplicadas_ignoradas + " duplicado(s) ignorado(s)." +
                      (data.errors && data.errors.length ? " Avisos: " + data.errors.join("; ") : "");
                    fileFeedbackEl.className = "appverbo-field-file-feedback-v1 is-success";
                    setTimeout(function () { window.location.reload(); }, 800);
                  } else {
                    fileFeedbackEl.textContent = "Erro: " + (data.detail || JSON.stringify(data));
                    fileFeedbackEl.className = "appverbo-field-file-feedback-v1 is-error";
                  }
                })
                .catch(function (err) {
                  fileInputEl.disabled = false;
                  fileFeedbackEl.textContent = "Erro de rede: " + err;
                  fileFeedbackEl.className = "appverbo-field-file-feedback-v1 is-error";
                });
            });

            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(fileBtnEl);
            fieldContainerEl.appendChild(fileFeedbackEl);
          } else {
            const inputValue =
              fieldType === "date" ? normalizeDateInputValue(editDefaultValue) : editDefaultValue;
            const controlEl =
              fieldType === "textarea"
                ? document.createElement("textarea")
                : document.createElement("input");
            controlEl.id = inputId;
            controlEl.name = inputName;
            controlEl.required = fieldRequired;
            if (fieldType === "textarea") {
              controlEl.value = inputValue;
              controlEl.defaultValue = inputValue;
              controlEl.rows = 10;
              controlEl.classList.add("appverbo-dynamic-process-textarea-v1");
            } else {
              if (isContactMembershipImportFileField) {
                controlEl.type = "file";
                controlEl.accept = ".csv,.xlsx";
              } else {
                controlEl.type = getDynamicProcessInputType(fieldType);
                controlEl.value = inputValue;
                controlEl.defaultValue = inputValue;
              }
              if (fieldType === "date" && typeof controlEl.showPicker === "function") {
                const openDatePicker = () => {
                  try {
                    controlEl.showPicker();
                  } catch (error) {
                    // Some browsers block showPicker outside trusted user events.
                  }
                };
                controlEl.addEventListener("click", openDatePicker);
                controlEl.addEventListener("focus", openDatePicker);
              }
              if (fieldType === "number") {
                controlEl.inputMode = "numeric";
              }
              if (fieldType === "currency") {
                controlEl.inputMode = "decimal";
                if (!controlEl.value) {
                  controlEl.placeholder = "0,00";
                }
              }
            }
            if (
              typeof fieldSize === "number" &&
              fieldSize > 0 &&
              processTextualTypes.has(fieldType)
            ) {
              controlEl.maxLength = fieldSize;
            }
            if (isEmpresaInternalNumber || isEntityInternalNumberField(fieldKey, fieldLabel)) {
              controlEl.readOnly = true;
              controlEl.disabled = true;
              controlEl.classList.add("readonly-field");
              controlEl.required = false;
            }
            if (
              cleanMenuKey === "administrativo" &&
              selectedSectionKey === "custom_perfil_de_autorizacao" &&
              fieldKey === "custom_entidade"
            ) {
              controlEl.readOnly = true;
              controlEl.disabled = true;
              controlEl.classList.add("readonly-field");
              controlEl.required = false;
            }
            renderedInputsByFieldKey.set(fieldKey, controlEl);

            fieldContainerEl.appendChild(labelEl);
            fieldContainerEl.appendChild(controlEl);
          }

          dynamicProcessEditGridEl.appendChild(fieldContainerEl);
        }
      });

      refreshDynamicProcessDependentListFieldsV1({
        sectionFields,
        processSetting,
        processValuesByField: currentProcessValuesByField,
        renderedInputsByFieldKey,
        processListMetaByKey,
        preferredValuesByFieldKey: initialDynamicProcessListValuesByFieldKey
      });

      const dependentListControllerFieldKeys = new Set();
      sectionFields.forEach((field) => {
        const listKey = normalizeMenuKey(field && (field.listKey || field.list_key));
        const listMeta = processListMetaByKey.get(listKey);
        if (!listMeta || listMeta.sourceKey !== "sidebar_menus_by_section") {
          return;
        }

        const controllerField = resolveDynamicProcessSessionControllerFieldKeyV1(
          sectionFields,
          processSetting,
          processListMetaByKey,
          field && field.key
        );
        if (controllerField && controllerField.key) {
          dependentListControllerFieldKeys.add(normalizeMenuKey(controllerField.key));
        }
      });

      dependentListControllerFieldKeys.forEach((fieldKey) => {
        const controllerEl = renderedInputsByFieldKey.get(fieldKey);
        if (!controllerEl || typeof controllerEl.addEventListener !== "function") {
          return;
        }

        const refreshDependentListFields = () => {
          refreshDynamicProcessDependentListFieldsV1({
            sectionFields,
            processSetting,
            processValuesByField: currentProcessValuesByField,
            renderedInputsByFieldKey,
            processListMetaByKey
          });
        };

        controllerEl.addEventListener("input", refreshDependentListFields);
        controllerEl.addEventListener("change", refreshDependentListFields);
      });

      if (showStateField && dynamicProcessEditGridEl) {
        const stateFieldEl = document.createElement("div");
        stateFieldEl.className = "field";

        const stateInputId =
          `dynamic_process_${cleanMenuKey}_${String(selectedSection ? selectedSection.key || "" : "")}_estado`.replace(
            /[^a-z0-9_]+/gi,
            "_"
          );

        const stateLabelEl = document.createElement("label");
        stateLabelEl.setAttribute("for", stateInputId);
        stateLabelEl.textContent = "Estado";

        const stateSelectEl = document.createElement("select");
        stateSelectEl.id = stateInputId;
        stateSelectEl.name = "process_state";
        stateSelectEl.innerHTML = `
      <option value="ativo" selected>Ativo</option>
      <option value="inativo">Inativo</option>
    `;

        stateFieldEl.appendChild(stateLabelEl);
        stateFieldEl.appendChild(stateSelectEl);
        dynamicProcessEditGridEl.appendChild(stateFieldEl);

        const entityNumberAlreadyRendered =
          renderedInputsByFieldKey.has("numero_entidade") ||
          renderedInputsByFieldKey.has("custom_n_cliente") ||
          renderedInputsByFieldKey.has("entity_internal_number");

        if (bootstrapEntityInternalNumber && !entityNumberAlreadyRendered) {
          const entityNumFieldEl = document.createElement("div");
          entityNumFieldEl.className = "field";

          const entityNumInputId =
            `dynamic_process_${cleanMenuKey}_numero_entidade`.replace(/[^a-z0-9_]+/gi, "_");

          const entityNumLabelEl = document.createElement("label");
          entityNumLabelEl.setAttribute("for", entityNumInputId);
          entityNumLabelEl.textContent = "Nº Entidade";

          const entityNumInputEl = document.createElement("input");
          entityNumInputEl.id = entityNumInputId;
          entityNumInputEl.name = "numero_entidade";
          entityNumInputEl.type = "text";
          entityNumInputEl.value = bootstrapEntityInternalNumber;
          entityNumInputEl.readOnly = true;
          entityNumInputEl.setAttribute("readonly", "readonly");
          entityNumInputEl.setAttribute("aria-readonly", "true");
          entityNumInputEl.className = "readonly-field";

          entityNumFieldEl.appendChild(entityNumLabelEl);
          entityNumFieldEl.appendChild(entityNumInputEl);
          dynamicProcessEditGridEl.appendChild(entityNumFieldEl);
        }
      }

      if (absenceProcessMode) {
        setupAbsenceDateRangeValidation(sectionFields, renderedInputsByFieldKey);
      }

      renderDynamicProcessQuantityGroups(
        cleanMenuKey,
        processSetting,
        selectedSection,
        sectionFields,
        currentProcessValuesByField,
        currentProcessQuantityValuesByRule
      );

      if (historyProcessMode) {
        renderDynamicProcessHistory(
          cleanMenuKey,
          selectedSection ? selectedSection.key || "" : "",
          sectionLabel,
          sectionFields,
          historyRecordLabels
        );
      } else {
        if (dynamicProcessHistoryBlockEl) {
          dynamicProcessHistoryBlockEl.style.display = "none";
        }
        if (dynamicProcessHistoryActiveCardEl) {
          dynamicProcessHistoryActiveCardEl.style.display = "none";
        }
        if (dynamicProcessHistoryInactiveCardEl) {
          dynamicProcessHistoryInactiveCardEl.style.display = "none";
        }
      }

      if (typeof window.APPVERBO_APPLY_SONG_PROCESS_UI_V1 === "function") {
        window.APPVERBO_APPLY_SONG_PROCESS_UI_V1({
          menuKey: cleanMenuKey,
          menuLabel,
          sectionLabel,
          sectionFields,
          processSetting,
          historyProcessMode,
          dynamicProcessEditFormEl,
          dynamicProcessEditGridEl,
          dynamicProcessHistoryActiveCardEl,
          dynamicProcessHistoryInactiveCardEl,
          dynamicProcessHistoryActiveTableEl,
          dynamicProcessHistoryInactiveTableEl
        });
      }

      if (preserveInteractionState && wasEditing) {
        dynamicProcessCardEl.classList.add("editing");
        if (dynamicProcessCreateCardEl && wasCreateCardEditing) {
          dynamicProcessCreateCardEl.classList.add("is-editing");
        }
      }
    }

    window.buildProcessOptionMetaMap = buildProcessOptionMetaMap;
    window.collectCurrentDynamicProcessQuantityValues = collectCurrentDynamicProcessQuantityValues;
    window.syncDynamicProcessQuantityHiddenInputs = syncDynamicProcessQuantityHiddenInputs;
    window.collectCurrentMeuPerfilQuantityValues = collectCurrentMeuPerfilQuantityValues;
    window.syncMeuPerfilQuantityHiddenInputs = syncMeuPerfilQuantityHiddenInputs;
    window.renderMeuPerfilQuantityGroups = renderMeuPerfilQuantityGroups;
    window.renderDynamicProcessQuantityGroups = renderDynamicProcessQuantityGroups;
    window.collectCurrentDynamicProcessValues = collectCurrentDynamicProcessValues;
    window.renderDynamicProcessCard = renderDynamicProcessCard;
  };
})();
// APPVERBO_DYNAMIC_PROCESS_RUNTIME_CORE_V1_MODULE_END
