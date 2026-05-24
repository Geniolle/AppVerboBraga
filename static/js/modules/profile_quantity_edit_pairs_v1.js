// APPVERBO_PROFILE_QUANTITY_EDIT_PAIRS_V4_START
(function () {
  "use strict";

  if (typeof window !== "undefined") {
    window.__APPVERBO_QUANTITY_EDIT_PAIRS_V4_ACTIVE = true;
  }

  //###################################################################################
  // (1) BOOTSTRAP E CONSTANTES
  //###################################################################################

  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};
  const MEU_PERFIL_KEY_V4 = "meu_perfil";
  const LEGACY_DOCUMENTOS_KEY_V4 = "documentos";

  const sidebarMenuSettings = Array.isArray(bootstrap.sidebarMenuSettings)
    ? bootstrap.sidebarMenuSettings
    : [];

  const menuProcessQuantityValuesMap = (
    bootstrap.menuProcessQuantityValuesMap &&
    typeof bootstrap.menuProcessQuantityValuesMap === "object" &&
    !Array.isArray(bootstrap.menuProcessQuantityValuesMap)
  )
    ? bootstrap.menuProcessQuantityValuesMap
    : {};

  const renderStateByRuleKey = new Map();

  //###################################################################################
  // (2) NORMALIZAR
  //###################################################################################

  function normalizeKeyQuantityEditPairs_v4(value) {
    const cleanValue = String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");

    if (cleanValue === LEGACY_DOCUMENTOS_KEY_V4) {
      return MEU_PERFIL_KEY_V4;
    }

    return cleanValue;
  }

  function normalizeTextQuantityEditPairs_v4(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }

  function toSentenceCaseQuantityEditPairs_v4(value) {
    const cleanText = String(value || "").trim().replace(/\s+/g, " ");

    if (!cleanText) {
      return "";
    }

    const loweredText = cleanText.toLocaleLowerCase("pt-PT");
    return loweredText.charAt(0).toLocaleUpperCase("pt-PT") + loweredText.slice(1);
  }

  function normalizeFieldTypeQuantityEditPairs_v4(value) {
    const cleanType = String(value || "text").trim().toLowerCase();
    const allowedTypes = new Set(["text", "number", "email", "phone", "date", "flag", "list"]);

    return allowedTypes.has(cleanType) ? cleanType : "text";
  }

  function convertDisplayDateToInputDateQuantityEditPairs_v4(value) {
    const cleanValue = String(value || "").trim();

    if (/^\d{4}-\d{2}-\d{2}$/.test(cleanValue)) {
      return cleanValue;
    }

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(cleanValue)) {
      const parts = cleanValue.split("/");
      return parts[2] + "-" + parts[1] + "-" + parts[0];
    }

    return cleanValue;
  }

  //###################################################################################
  // (3) CONFIGURAÇÃO DO MEU PERFIL
  //###################################################################################

  function getMeuPerfilSettingQuantityEditPairs_v4() {
    return sidebarMenuSettings.find(function (setting) {
      return normalizeKeyQuantityEditPairs_v4(setting && setting.key) === MEU_PERFIL_KEY_V4;
    }) || null;
  }

  function getFieldMetaMapQuantityEditPairs_v4(setting) {
    const metaMap = new Map();

    const options = Array.isArray(setting && setting.process_field_options)
      ? setting.process_field_options
      : [];

    options.forEach(function (option) {
      const fieldKey = normalizeKeyQuantityEditPairs_v4(option && option.key);

      if (!fieldKey) {
        return;
      }

      metaMap.set(fieldKey, {
        key: fieldKey,
        label: toSentenceCaseQuantityEditPairs_v4(option.label || fieldKey),
        fieldType: normalizeFieldTypeQuantityEditPairs_v4(option.field_type),
        isRequired: Boolean(option.is_required || option.required),
        listOptions: Array.isArray(option.list_options) ? option.list_options : []
      });
    });

    return metaMap;
  }

  function normalizeQuantityRulesQuantityEditPairs_v4(rawRules) {
    if (!Array.isArray(rawRules)) {
      return [];
    }

    return rawRules
      .map(function (rawRule, index) {
        if (!rawRule || typeof rawRule !== "object") {
          return null;
        }

        const key = normalizeKeyQuantityEditPairs_v4(
          rawRule.key ||
          rawRule.rule_key ||
          rawRule.ruleKey ||
          "qty_regra_" + String(index + 1)
        );

        const quantityFieldKey = normalizeKeyQuantityEditPairs_v4(
          rawRule.quantity_field_key ||
          rawRule.quantityFieldKey
        );

        const repeatedRaw = Array.isArray(rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          ? (rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          : [];

        const repeatedFieldKeys = [];
        const seen = new Set();

        repeatedRaw.forEach(function (rawFieldKey) {
          const fieldKey = normalizeKeyQuantityEditPairs_v4(rawFieldKey);

          if (!fieldKey || seen.has(fieldKey)) {
            return;
          }

          seen.add(fieldKey);
          repeatedFieldKeys.push(fieldKey);
        });

        const parsedMax = Number.parseInt(String(rawRule.max_items || rawRule.maxItems || "50"), 10);

        if (!key || !quantityFieldKey || !repeatedFieldKeys.length) {
          return null;
        }

        return {
          key: key,
          label: toSentenceCaseQuantityEditPairs_v4(rawRule.label || rawRule.rule_label || rawRule.name || "Quantidade"),
          quantityFieldKey: quantityFieldKey,
          repeatedFieldKeys: repeatedFieldKeys,
          headerKey: normalizeKeyQuantityEditPairs_v4(rawRule.header_key || rawRule.headerKey),
          itemLabel: toSentenceCaseQuantityEditPairs_v4(rawRule.item_label || rawRule.itemLabel || "Item") || "Item",
          maxItems: Number.isFinite(parsedMax) ? Math.max(1, Math.min(parsedMax, 50)) : 50
        };
      })
      .filter(Boolean);
  }

  function normalizeQuantityItemsQuantityEditPairs_v4(rawItems) {
    if (!Array.isArray(rawItems)) {
      return [];
    }

    return rawItems
      .map(function (rawItem) {
        if (!rawItem || typeof rawItem !== "object") {
          return null;
        }

        const normalized = {};

        Object.keys(rawItem).forEach(function (rawKey) {
          const fieldKey = normalizeKeyQuantityEditPairs_v4(rawKey);

          if (!fieldKey) {
            return;
          }

          normalized[fieldKey] = String(rawItem[rawKey] || "").trim();
        });

        return normalized;
      })
      .filter(Boolean);
  }

  function getQuantityValuesQuantityEditPairs_v4(ruleKey) {
    const valuesByMenu = menuProcessQuantityValuesMap[MEU_PERFIL_KEY_V4];

    if (!valuesByMenu || typeof valuesByMenu !== "object" || Array.isArray(valuesByMenu)) {
      return [];
    }

    return normalizeQuantityItemsQuantityEditPairs_v4(valuesByMenu[normalizeKeyQuantityEditPairs_v4(ruleKey)]);
  }

  //###################################################################################
  // (4) DETETAR ABA ATIVA
  //###################################################################################

  function getCurrentProfileSectionFromActiveTabQuantityEditPairs_v4() {
    const explicitSelectors = [
      "#submenu-items .submenu-item.active[data-profile-section]",
      "#submenu-items .submenu-item[data-profile-section][aria-selected='true']",
      "#submenu-items .submenu-item[data-profile-section][data-active='true']",
      ".submenu-item.active[data-profile-section]",
      ".submenu-item[data-profile-section][aria-selected='true']",
      "[data-profile-section-tab].active[data-profile-section]",
      "[data-profile-section-button].active[data-profile-section]",
      ".profile-section-tab.active[data-profile-section]"
    ];

    for (const selector of explicitSelectors) {
      const activeElement = document.querySelector(selector);

      if (!activeElement) {
        continue;
      }

      const sectionKey = normalizeKeyQuantityEditPairs_v4(
        activeElement.dataset.profileSection ||
        activeElement.dataset.profileSectionKey ||
        activeElement.dataset.profileSectionTab ||
        activeElement.dataset.sectionKey ||
        ""
      );

      if (sectionKey) {
        return sectionKey;
      }
    }

    return "";
  }

  function getCurrentProfileSectionFromInputQuantityEditPairs_v4() {
    const sectionInput = document.querySelector("[data-meu-perfil-section-input]");

    if (!sectionInput) {
      return "";
    }

    return normalizeKeyQuantityEditPairs_v4(sectionInput.value || "");
  }

  function getCurrentProfileSectionFromUrlQuantityEditPairs_v4() {
    try {
      const url = new URL(window.location.href);
      return normalizeKeyQuantityEditPairs_v4(url.searchParams.get("profile_section") || "");
    }
    catch (error) {
      return "";
    }
  }

  function getCurrentProfileSectionQuantityEditPairs_v4() {
    return getCurrentProfileSectionFromActiveTabQuantityEditPairs_v4() ||
      getCurrentProfileSectionFromInputQuantityEditPairs_v4() ||
      getCurrentProfileSectionFromUrlQuantityEditPairs_v4();
  }

  function shouldRenderRuleInCurrentSectionQuantityEditPairs_v4(rule) {
    const ruleSection = normalizeKeyQuantityEditPairs_v4(rule && rule.headerKey);
    const currentSection = getCurrentProfileSectionQuantityEditPairs_v4();

    if (!ruleSection) {
      return true;
    }

    if (!currentSection) {
      return false;
    }

    return currentSection === ruleSection;
  }

  //###################################################################################
  // (5) LOCALIZAR FORMULÁRIO
  //###################################################################################

  function getEditFormQuantityEditPairs_v4() {
    return (
      document.querySelector('form[action="/users/profile/personal"]') ||
      document.querySelector("#perfil-pessoal-card form.profile-edit-form") ||
      document.querySelector("#perfil-pessoal-card form")
    );
  }

  function getEditGridQuantityEditPairs_v4(form) {
    if (!form) {
      return null;
    }

    return form.querySelector(".personal-grid") ||
      form.querySelector(".form-grid") ||
      form;
  }

  function isEditFormVisibleQuantityEditPairs_v4(form) {
    if (!form) {
      return false;
    }

    const style = window.getComputedStyle(form);
    return style.display !== "none" && style.visibility !== "hidden";
  }

  function getFieldLabelQuantityEditPairs_v4(field) {
    const label = field ? field.querySelector("label, .personal-label") : null;
    return normalizeTextQuantityEditPairs_v4(label ? label.textContent : "");
  }

  function findFieldWrapperByFieldKeyQuantityEditPairs_v4(form, fieldKey, fieldMetaMap) {
    const cleanFieldKey = normalizeKeyQuantityEditPairs_v4(fieldKey);

    if (!form || !cleanFieldKey) {
      return null;
    }

    const directSelectors = [
      '[name="custom_field__' + cleanFieldKey + '"]',
      '[name="' + cleanFieldKey + '"]',
      '[data-profile-field-key="' + cleanFieldKey + '"]'
    ];

    for (const selector of directSelectors) {
      const input = form.querySelector(selector);

      if (input) {
        return input.closest(".field") || input.parentElement;
      }
    }

    const meta = fieldMetaMap.get(cleanFieldKey);
    const expectedLabel = normalizeTextQuantityEditPairs_v4(meta ? meta.label : cleanFieldKey);

    return Array.from(form.querySelectorAll(".field")).find(function (field) {
      if (field.closest("[data-appverbo-quantity-edit-generated-v4='1']")) {
        return false;
      }

      return getFieldLabelQuantityEditPairs_v4(field) === expectedLabel;
    }) || null;
  }

  function findInputByFieldKeyQuantityEditPairs_v4(form, fieldKey, fieldMetaMap) {
    const field = findFieldWrapperByFieldKeyQuantityEditPairs_v4(form, fieldKey, fieldMetaMap);

    if (!field) {
      return null;
    }

    return field.querySelector("input, select, textarea");
  }

  //###################################################################################
  // (6) LIMPAR DUPLICADOS E LEGADOS
  //###################################################################################

  function removeAllQuantityPairDomQuantityEditPairs_v4(form, ruleKey) {
    if (!form || !ruleKey) {
      return;
    }

    const escapedRuleKey = String(ruleKey).replace(/"/g, '\\"');

    const selectors = [
      '[data-appverbo-quantity-edit-generated-v1="1"]',
      '[data-appverbo-quantity-edit-generated-v2="1"]',
      '[data-appverbo-quantity-edit-generated-v3="1"]',
      '[data-appverbo-quantity-edit-generated-v4="1"]',
      '.appverbo-quantity-edit-group-v1',
      '.appverbo-quantity-edit-group-v2',
      '.appverbo-quantity-edit-group-v3',
      '.appverbo-quantity-edit-group-v4',
      '.appverbo-quantity-edit-header-v1',
      '.appverbo-quantity-edit-header-v2',
      '.appverbo-quantity-edit-header-v3',
      '.appverbo-quantity-edit-header-v4',
      '.appverbo-quantity-edit-field-v1',
      '.appverbo-quantity-edit-field-v2',
      '.appverbo-quantity-edit-field-v3',
      '.appverbo-quantity-edit-field-v4',
      '[name^="process_quantity_field__' + escapedRuleKey + '__"]',
      '[name="process_quantity_payload__' + escapedRuleKey + '"]'
    ];

    Array.from(form.querySelectorAll(selectors.join(","))).forEach(function (element) {
      const removable = element.closest("[data-appverbo-quantity-edit-generated-v1='1'], [data-appverbo-quantity-edit-generated-v2='1'], [data-appverbo-quantity-edit-generated-v3='1'], [data-appverbo-quantity-edit-generated-v4='1'], .appverbo-quantity-edit-group-v1, .appverbo-quantity-edit-group-v2, .appverbo-quantity-edit-group-v3, .appverbo-quantity-edit-group-v4, .field") || element;

      if (removable && removable.parentElement) {
        removable.remove();
      }
    });

    Array.from(form.querySelectorAll("div, h3, h4, strong")).forEach(function (element) {
      const text = normalizeTextQuantityEditPairs_v4(element.textContent || "");

      if (/^numero de filhos \d+$/.test(text) || /^número de filhos \d+$/.test(String(element.textContent || "").trim().toLowerCase())) {
        if (element.parentElement && !element.closest(".profile-readonly")) {
          element.remove();
        }
      }
    });
  }

  function collectExistingQuantityValuesQuantityEditPairs_v4(form, rule) {
    const payload = [];
    const generatedInputs = Array.from(
      form.querySelectorAll(
        '[name^="process_quantity_field__' + rule.key + '__"], ' +
        '[data-appverbo-quantity-rule-key-v1="' + rule.key + '"] input, ' +
        '[data-appverbo-quantity-rule-key-v1="' + rule.key + '"] select, ' +
        '[data-appverbo-quantity-rule-key-v1="' + rule.key + '"] textarea, ' +
        '[data-appverbo-quantity-rule-key-v2="' + rule.key + '"] input, ' +
        '[data-appverbo-quantity-rule-key-v2="' + rule.key + '"] select, ' +
        '[data-appverbo-quantity-rule-key-v2="' + rule.key + '"] textarea, ' +
        '[data-appverbo-quantity-rule-key-v3="' + rule.key + '"] input, ' +
        '[data-appverbo-quantity-rule-key-v3="' + rule.key + '"] select, ' +
        '[data-appverbo-quantity-rule-key-v3="' + rule.key + '"] textarea, ' +
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] input, ' +
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] select, ' +
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] textarea'
      )
    );

    generatedInputs.forEach(function (input) {
      let index = Number.parseInt(String(input.dataset.appverboQuantityIndexV4 || input.dataset.appverboQuantityIndexV3 || input.dataset.appverboQuantityIndexV2 || input.dataset.appverboQuantityIndexV1 || ""), 10);
      let fieldKey = normalizeKeyQuantityEditPairs_v4(input.dataset.appverboQuantityFieldKeyV4 || input.dataset.appverboQuantityFieldKeyV3 || input.dataset.appverboQuantityFieldKeyV2 || input.dataset.appverboQuantityFieldKeyV1 || "");

      if (!fieldKey) {
        const name = String(input.name || "");
        const prefix = "process_quantity_field__" + rule.key + "__";

        if (name.startsWith(prefix)) {
          const suffix = name.slice(prefix.length);
          const parts = suffix.split("__");
          index = Number.parseInt(parts[0] || "", 10);
          fieldKey = normalizeKeyQuantityEditPairs_v4(parts.slice(1).join("__"));
        }
      }

      if (!Number.isFinite(index) || !fieldKey) {
        return;
      }

      if (!payload[index]) {
        payload[index] = {};
      }

      payload[index][fieldKey] = String(input.value || "").trim();
    });

    return payload.filter(function (item) {
      return item && Object.keys(item).some(function (key) {
        return String(item[key] || "").trim();
      });
    });
  }

  //###################################################################################
  // (7) CRIAR CAMPOS
  //###################################################################################

  function createLabelQuantityEditPairs_v4(text, required) {
    const label = document.createElement("label");
    label.textContent = text || "-";

    if (required) {
      const mark = document.createElement("span");
      mark.textContent = " *";
      label.appendChild(mark);
    }

    return label;
  }

  function createInputQuantityEditPairs_v4(rule, fieldKey, fieldMeta, index, value) {
    const fieldType = normalizeFieldTypeQuantityEditPairs_v4(fieldMeta.fieldType);
    const name = "process_quantity_field__" + rule.key + "__" + String(index) + "__" + fieldKey;
    let input = null;

    if (fieldType === "list" && Array.isArray(fieldMeta.listOptions) && fieldMeta.listOptions.length) {
      input = document.createElement("select");

      fieldMeta.listOptions.forEach(function (optionValue) {
        const option = document.createElement("option");
        option.value = String(optionValue || "").trim();
        option.textContent = String(optionValue || "").trim();
        input.appendChild(option);
      });
    }
    else if (fieldType === "flag") {
      input = document.createElement("select");

      [
        ["", ""],
        ["1", "Sim"],
        ["0", "Não"]
      ].forEach(function (pair) {
        const option = document.createElement("option");
        option.value = pair[0];
        option.textContent = pair[1];
        input.appendChild(option);
      });
    }
    else {
      input = document.createElement("input");

      if (fieldType === "date") {
        input.type = "text";
        input.placeholder = "dd/mm/aaaa";
      }
      else if (fieldType === "number") {
        input.type = "number";
      }
      else if (fieldType === "email") {
        input.type = "email";
      }
      else if (fieldType === "phone") {
        input.type = "tel";
      }
      else {
        input.type = "text";
      }
    }

    input.name = name;
    input.value = String(value || "");
    input.dataset.appverboQuantityFieldKeyV4 = fieldKey;
    input.dataset.appverboQuantityRuleKeyV4 = rule.key;
    input.dataset.appverboQuantityIndexV4 = String(index);

    if (fieldMeta.isRequired) {
      input.required = true;
    }

    return input;
  }

  function createFieldQuantityEditPairs_v4(rule, fieldKey, fieldMeta, index, value) {
    const field = document.createElement("div");

    field.className = "field appverbo-quantity-edit-field-v4";
    field.setAttribute("data-appverbo-quantity-field-v4", "1");
    field.setAttribute("data-profile-field-key", "quantity_" + rule.key + "_" + String(index) + "_" + fieldKey);

    const label = createLabelQuantityEditPairs_v4(fieldMeta.label || fieldKey, fieldMeta.isRequired);
    const input = createInputQuantityEditPairs_v4(rule, fieldKey, fieldMeta, index, value);

    field.appendChild(label);
    field.appendChild(input);

    return field;
  }

  function createGroupQuantityEditPairs_v4(rule, index, itemValues, fieldMetaMap) {
    const group = document.createElement("div");

    group.className = "appverbo-quantity-edit-group-v4";
    group.setAttribute("data-appverbo-quantity-edit-generated-v4", "1");
    group.setAttribute("data-appverbo-quantity-rule-key-v4", rule.key);
    group.setAttribute("data-appverbo-quantity-index-v4", String(index));
    group.setAttribute("data-profile-section-pane", rule.headerKey || "");
    group.style.gridColumn = "1 / -1";
    group.style.order = String(5000 + index);

    const title = document.createElement("div");
    title.className = "appverbo-quantity-edit-title-v4";
    title.textContent = rule.itemLabel + " " + String(index + 1);
    group.appendChild(title);

    const innerGrid = document.createElement("div");
    innerGrid.className = "appverbo-quantity-edit-grid-v4";
    group.appendChild(innerGrid);

    rule.repeatedFieldKeys.forEach(function (fieldKey) {
      const fieldMeta = fieldMetaMap.get(fieldKey) || {
        key: fieldKey,
        label: toSentenceCaseQuantityEditPairs_v4(fieldKey),
        fieldType: "text",
        isRequired: false,
        listOptions: []
      };

      const fieldElement = createFieldQuantityEditPairs_v4(
        rule,
        fieldKey,
        fieldMeta,
        index,
        itemValues ? itemValues[fieldKey] : ""
      );

      innerGrid.appendChild(fieldElement);
    });

    return group;
  }

  //###################################################################################
  // (8) PAYLOAD OCULTO
  //###################################################################################

  function collectRulePayloadQuantityEditPairs_v4(form, rule) {
    const payload = [];
    const generatedInputs = Array.from(
      form.querySelectorAll(
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] input, ' +
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] select, ' +
        '[data-appverbo-quantity-rule-key-v4="' + rule.key + '"] textarea'
      )
    );

    generatedInputs.forEach(function (input) {
      const index = Number.parseInt(String(input.dataset.appverboQuantityIndexV4 || "0"), 10);
      const fieldKey = normalizeKeyQuantityEditPairs_v4(input.dataset.appverboQuantityFieldKeyV4 || "");

      if (!Number.isFinite(index) || !fieldKey) {
        return;
      }

      if (!payload[index]) {
        payload[index] = {};
      }

      payload[index][fieldKey] = String(input.value || "").trim();
    });

    return payload.filter(function (item) {
      return item && Object.keys(item).some(function (key) {
        return String(item[key] || "").trim();
      });
    });
  }

  function syncHiddenPayloadQuantityEditPairs_v4(form, rule) {
    if (!form || !rule) {
      return;
    }

    const payloadName = "process_quantity_payload__" + rule.key;

    Array.from(form.querySelectorAll('[name="' + payloadName + '"]')).forEach(function (input) {
      input.remove();
    });

    if (!shouldRenderRuleInCurrentSectionQuantityEditPairs_v4(rule)) {
      return;
    }

    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = payloadName;
    hiddenInput.value = JSON.stringify(collectRulePayloadQuantityEditPairs_v4(form, rule));

    form.appendChild(hiddenInput);
  }

  function bindPayloadSyncQuantityEditPairs_v4(form, rule) {
    const bindKey = "appverboQuantityPayloadBoundV4_" + rule.key;

    if (form.dataset[bindKey] === "1") {
      return;
    }

    form.dataset[bindKey] = "1";

    form.addEventListener("input", function (event) {
      const target = event.target;

      if (!target || !target.dataset || target.dataset.appverboQuantityRuleKeyV4 !== rule.key) {
        return;
      }

      syncHiddenPayloadQuantityEditPairs_v4(form, rule);
    }, true);

    form.addEventListener("change", function (event) {
      const target = event.target;

      if (!target || !target.dataset || target.dataset.appverboQuantityRuleKeyV4 !== rule.key) {
        return;
      }

      syncHiddenPayloadQuantityEditPairs_v4(form, rule);
    }, true);

    form.addEventListener("submit", function () {
      syncHiddenPayloadQuantityEditPairs_v4(form, rule);
    }, true);
  }

  //###################################################################################
  // (9) RENDERIZAR SEM DUPLICAR
  //###################################################################################

  function getQuantityCountQuantityEditPairs_v4(quantityInput, rule) {
    const parsed = Number.parseInt(String(quantityInput ? quantityInput.value : "").trim(), 10);

    if (!Number.isFinite(parsed) || parsed <= 0) {
      return 0;
    }

    return Math.min(parsed, rule.maxItems || 50);
  }

  function renderRulePairsQuantityEditPairs_v4(form, grid, rule, fieldMetaMap, forceRender) {
    const currentValues = collectExistingQuantityValuesQuantityEditPairs_v4(form, rule);

    if (!shouldRenderRuleInCurrentSectionQuantityEditPairs_v4(rule)) {
      renderStateByRuleKey.delete(rule.key);
      removeAllQuantityPairDomQuantityEditPairs_v4(form, rule.key);
      return;
    }

    const quantityInput = findInputByFieldKeyQuantityEditPairs_v4(form, rule.quantityFieldKey, fieldMetaMap);
    const quantityWrapper = quantityInput ? quantityInput.closest(".field") : null;

    if (!quantityInput || !quantityWrapper || !grid) {
      return;
    }

    const quantityCount = getQuantityCountQuantityEditPairs_v4(quantityInput, rule);
    const savedValues = getQuantityValuesQuantityEditPairs_v4(rule.key);
    const mergedValues = [];

    for (let index = 0; index < quantityCount; index += 1) {
      mergedValues[index] = currentValues[index] || savedValues[index] || {};
    }

    const signature = JSON.stringify({
      ruleKey: rule.key,
      quantityCount: quantityCount,
      repeatedFieldKeys: rule.repeatedFieldKeys,
      mergedValues: mergedValues,
      section: getCurrentProfileSectionQuantityEditPairs_v4()
    });

    const hasExistingV4 = Boolean(
      form.querySelector('[data-appverbo-quantity-edit-generated-v4="1"][data-appverbo-quantity-rule-key-v4="' + rule.key + '"]')
    );

    if (!forceRender && hasExistingV4 && renderStateByRuleKey.get(rule.key) === signature) {
      syncHiddenPayloadQuantityEditPairs_v4(form, rule);
      return;
    }

    renderStateByRuleKey.set(rule.key, signature);
    removeAllQuantityPairDomQuantityEditPairs_v4(form, rule.key);

    let insertionPoint = quantityWrapper;

    for (let index = 0; index < quantityCount; index += 1) {
      const group = createGroupQuantityEditPairs_v4(
        rule,
        index,
        mergedValues[index] || {},
        fieldMetaMap
      );

      insertionPoint.insertAdjacentElement("afterend", group);
      insertionPoint = group;
    }

    syncHiddenPayloadQuantityEditPairs_v4(form, rule);
    bindPayloadSyncQuantityEditPairs_v4(form, rule);
  }

  function renderAllPairsQuantityEditPairs_v4(forceRender) {
    const form = getEditFormQuantityEditPairs_v4();
    const grid = getEditGridQuantityEditPairs_v4(form);
    const setting = getMeuPerfilSettingQuantityEditPairs_v4();

    if (!form || !grid || !setting || !isEditFormVisibleQuantityEditPairs_v4(form)) {
      return;
    }

    const fieldMetaMap = getFieldMetaMapQuantityEditPairs_v4(setting);
    const rules = normalizeQuantityRulesQuantityEditPairs_v4(setting.process_quantity_fields);

    rules.forEach(function (rule) {
      renderRulePairsQuantityEditPairs_v4(form, grid, rule, fieldMetaMap, Boolean(forceRender));
    });
  }

  //###################################################################################
  // (10) BIND
  //###################################################################################

  function bindQuantityInputsQuantityEditPairs_v4() {
    const form = getEditFormQuantityEditPairs_v4();
    const setting = getMeuPerfilSettingQuantityEditPairs_v4();

    if (!form || !setting || form.dataset.appverboQuantityEditPairsBoundV4 === "1") {
      return;
    }

    const fieldMetaMap = getFieldMetaMapQuantityEditPairs_v4(setting);
    const rules = normalizeQuantityRulesQuantityEditPairs_v4(setting.process_quantity_fields);

    rules.forEach(function (rule) {
      const quantityInput = findInputByFieldKeyQuantityEditPairs_v4(form, rule.quantityFieldKey, fieldMetaMap);

      if (!quantityInput) {
        return;
      }

      quantityInput.addEventListener("input", function () {
        renderStateByRuleKey.delete(rule.key);
        window.setTimeout(function () {
          renderAllPairsQuantityEditPairs_v4(true);
        }, 0);
      });

      quantityInput.addEventListener("change", function () {
        renderStateByRuleKey.delete(rule.key);
        window.setTimeout(function () {
          renderAllPairsQuantityEditPairs_v4(true);
        }, 0);
      });
    });

    form.dataset.appverboQuantityEditPairsBoundV4 = "1";
  }

  //###################################################################################
  // (11) ESTILO
  //###################################################################################

  function installStyleQuantityEditPairs_v4() {
    if (document.getElementById("appverbo-profile-quantity-edit-pairs-style-v4")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "appverbo-profile-quantity-edit-pairs-style-v4";
    style.textContent = [
      ".appverbo-quantity-edit-group-v4 { width: 100%; margin-top: 14px; }",
      ".appverbo-quantity-edit-title-v4 { margin: 0 0 10px; font-size: 14px; font-weight: 800; color: #0f172a; }",
      ".appverbo-quantity-edit-grid-v4 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; }",
      ".appverbo-quantity-edit-grid-v4 .field { min-height: 54px; }",
      ".appverbo-quantity-edit-grid-v4 .field input, .appverbo-quantity-edit-grid-v4 .field select, .appverbo-quantity-edit-grid-v4 .field textarea { width: 100%; }",
      "@media (max-width: 900px) { .appverbo-quantity-edit-grid-v4 { grid-template-columns: 1fr; } }"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (12) INICIAR
  //###################################################################################

  function startQuantityEditPairs_v4(forceRender) {
    installStyleQuantityEditPairs_v4();
    bindQuantityInputsQuantityEditPairs_v4();
    renderAllPairsQuantityEditPairs_v4(Boolean(forceRender));
  }

  function shouldReactToSectionChangeQuantityEditPairs_v4(event) {
    const target = event && event.target ? event.target : null;

    if (!target || typeof target.closest !== "function") {
      return false;
    }

    if (target.closest("[data-appverbo-quantity-edit-generated-v4='1']")) {
      return false;
    }

    if (
      target.closest("#submenu-items .submenu-item[data-profile-section]") ||
      target.closest(".submenu-item[data-profile-section]") ||
      target.closest("[data-profile-section-tab]") ||
      target.closest("[data-profile-section-button]") ||
      target.closest(".profile-section-tab")
    ) {
      return true;
    }

    if (target.matches("input[name='profile_section'], [data-meu-perfil-section-input], [data-profile-section-input]")) {
      return true;
    }

    return false;
  }

  document.addEventListener("click", function (event) {
    if (!shouldReactToSectionChangeQuantityEditPairs_v4(event)) {
      return;
    }

    renderStateByRuleKey.clear();

    window.setTimeout(function () {
      startQuantityEditPairs_v4(true);
    }, 80);

    window.setTimeout(function () {
      startQuantityEditPairs_v4(true);
    }, 250);
  }, true);

  document.addEventListener("change", function (event) {
    if (!shouldReactToSectionChangeQuantityEditPairs_v4(event)) {
      return;
    }

    renderStateByRuleKey.clear();

    window.setTimeout(function () {
      startQuantityEditPairs_v4(true);
    }, 0);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      startQuantityEditPairs_v4(false);
    });
  }
  else {
    startQuantityEditPairs_v4(false);
  }

  window.addEventListener("pageshow", function () {
    startQuantityEditPairs_v4(false);
  });
})();
// APPVERBO_PROFILE_QUANTITY_EDIT_PAIRS_V4_END
