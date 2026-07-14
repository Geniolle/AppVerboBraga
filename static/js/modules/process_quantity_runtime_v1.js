//###################################################################################
// (1) RUNTIME CANONICO PARA CAMPOS DE QUANTIDADE
//###################################################################################

(function () {
  "use strict";

  const profileRegistryV1 =
    window.AppGenesisProfileFieldRegistryV1 &&
    typeof window.AppGenesisProfileFieldRegistryV1 === "object"
      ? window.AppGenesisProfileFieldRegistryV1
      : null;

  const TEXTUAL_TYPES = new Set(["text", "number", "email", "phone"]);
  const DEFAULT_MAX_ITEMS = 1;

  function toSafeString(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizeKey(value) {
    return toSafeString(value)
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "_")
      .replace(/-+/g, "_")
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function normalizeLookupText(value) {
    return toSafeString(value)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function toSentenceCaseText(value) {
    const clean = toSafeString(value).trim();
    if (!clean) {
      return "";
    }
    return clean.charAt(0).toUpperCase() + clean.slice(1);
  }

  function normalizeItems(rawItems) {
    if (!Array.isArray(rawItems)) {
      return [];
    }

    return rawItems
      .map((rawItem) => {
        if (!rawItem || typeof rawItem !== "object") {
          return null;
        }

        const normalizedItem = {};
        Object.keys(rawItem).forEach((rawKey) => {
          const cleanKey = normalizeKey(rawKey);
          if (!cleanKey) {
            return;
          }
          normalizedItem[cleanKey] = String(rawItem[rawKey] || "").trim();
        });
        return normalizedItem;
      })
      .filter(Boolean);
  }

  function calculateItemCount(value, maxItems) {
    const parsedValue = Number.parseInt(toSafeString(value).trim(), 10);
    const parsedMaxItems = Number.parseInt(toSafeString(maxItems || DEFAULT_MAX_ITEMS).trim(), 10);
    const safeMaxItems = Number.isFinite(parsedMaxItems)
      ? Math.min(Math.max(parsedMaxItems, 1), 50)
      : DEFAULT_MAX_ITEMS;

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 0;
    }

    return Math.min(parsedValue, safeMaxItems);
  }

  function resizeItems(items, desiredCount) {
    const safeItems = Array.isArray(items) ? items : [];
    const safeCount = Number.isFinite(desiredCount) && desiredCount > 0 ? desiredCount : 0;
    const nextItems = [];

    for (let index = 0; index < safeCount; index += 1) {
      nextItems.push(safeItems[index] && typeof safeItems[index] === "object" ? { ...safeItems[index] } : {});
    }

    return nextItems;
  }

  function validateRule(rule) {
    return Boolean(
      rule &&
      typeof rule === "object" &&
      normalizeKey(rule.key) &&
      normalizeKey(rule.quantityFieldKey) &&
      Array.isArray(rule.repeatedFieldKeys) &&
      rule.repeatedFieldKeys.length
    );
  }

  function normalizeRules(rawRules) {
    if (!Array.isArray(rawRules)) {
      return [];
    }

    return rawRules
      .map((rawRule, index) => {
        if (!rawRule || typeof rawRule !== "object") {
          return null;
        }

        const key = normalizeKey(rawRule.key || rawRule.rule_key || rawRule.ruleKey) || `qty_regra_${index + 1}`;
        const label = toSentenceCaseText(rawRule.label || rawRule.rule_label || rawRule.name || "Regra");
        const quantityFieldKey = normalizeKey(rawRule.quantity_field_key || rawRule.quantityFieldKey);
        const headerKey = normalizeKey(rawRule.header_key || rawRule.headerKey);
        const itemLabel = toSentenceCaseText(rawRule.item_label || rawRule.itemLabel || "Item") || "Item";
        const maxItemsRaw = Number.parseInt(String(rawRule.max_items || rawRule.maxItems || "1").trim(), 10);
        const maxItems = Number.isFinite(maxItemsRaw) ? Math.min(Math.max(maxItemsRaw, 1), 50) : DEFAULT_MAX_ITEMS;
        const repeatedFieldKeys = Array.isArray(rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          ? (rawRule.repeated_field_keys || rawRule.repeatedFieldKeys)
          : [];
        const cleanRepeatedFieldKeys = [];
        const seenRepeatedFieldKeys = new Set();

        repeatedFieldKeys.forEach((rawFieldKey) => {
          const cleanFieldKey = normalizeKey(rawFieldKey);
          if (!cleanFieldKey || seenRepeatedFieldKeys.has(cleanFieldKey)) {
            return;
          }
          seenRepeatedFieldKeys.add(cleanFieldKey);
          cleanRepeatedFieldKeys.push(cleanFieldKey);
        });

        const normalizedRule = {
          key,
          label,
          quantityFieldKey,
          repeatedFieldKeys: cleanRepeatedFieldKeys,
          headerKey,
          maxItems,
          itemLabel
        };

        return validateRule(normalizedRule) ? normalizedRule : null;
      })
      .filter(Boolean);
  }

  function serializeItems(items) {
    return JSON.stringify(normalizeItems(items));
  }

  function deserializeItems(value) {
    if (Array.isArray(value)) {
      return normalizeItems(value);
    }

    try {
      const parsed = JSON.parse(String(value || "[]"));
      return normalizeItems(parsed);
    } catch (error) {
      return [];
    }
  }

  function buildFieldMetaMap(setting) {
    const metaMap = new Map();

    (Array.isArray(setting && setting.process_field_options) ? setting.process_field_options : []).forEach((option) => {
      const key = normalizeKey(option && option.key);
      if (!key) {
        return;
      }

      metaMap.set(key, {
        key,
        label: toSafeString(option.label || key).trim(),
        lookupLabel: normalizeLookupText(option.label || key),
        fieldType: normalizeKey(option.field_type)
      });
    });

    return metaMap;
  }

  function buildFieldMetaByKey(setting) {
    return buildFieldMetaMap(setting);
  }

  function getProfileForm(root) {
    const scope = root && typeof root.querySelector === "function" ? root : document;

    return (
      scope.querySelector('form[action="/users/profile/personal"]') ||
      scope.querySelector("#perfil-pessoal-card form") ||
      null
    );
  }

  function getCurrentProfileSection(root) {
    if (profileRegistryV1 && typeof profileRegistryV1.getCurrentProfileSection === "function") {
      return profileRegistryV1.getCurrentProfileSection(root);
    }

    return "";
  }

  function resolveControlName(fieldKey) {
    if (profileRegistryV1 && typeof profileRegistryV1.resolveControlName === "function") {
      return profileRegistryV1.resolveControlName(fieldKey);
    }

    const cleanKey = normalizeKey(fieldKey);
    if (!cleanKey) {
      return "";
    }

    if (cleanKey.startsWith("custom_")) {
      return "custom_field__" + cleanKey;
    }

    const builtinNames = {
      nome: "full_name",
      telefone: "primary_phone",
      email: "login_email",
      pais: "country",
      data_nascimento: "birth_date",
      autorizacao_whatsapp: "whatsapp_notice_opt_in"
    };

    return builtinNames[cleanKey] || cleanKey;
  }

  function collectValuesFromForm(form) {
    if (!form || typeof form.querySelectorAll !== "function") {
      return {};
    }

    if (profileRegistryV1 && typeof profileRegistryV1.collectProfileValues === "function") {
      return profileRegistryV1.collectProfileValues(form);
    }

    const valuesByField = {};

    form.querySelectorAll("[name]").forEach((control) => {
      const fieldKey = normalizeKey(String(control.getAttribute("name") || "").replace(/^custom_field__/, ""));
      if (!fieldKey) {
        return;
      }
      if (control.type === "checkbox") {
        valuesByField[fieldKey] = control.checked ? "1" : "0";
        return;
      }
      valuesByField[fieldKey] = String(control.value || "").trim();
    });

    return valuesByField;
  }

  function getFormQuantityPayloadInputs(form) {
    if (!form || typeof form.querySelectorAll !== "function") {
      return [];
    }

    return Array.from(form.querySelectorAll("[name^='process_quantity_payload__']"));
  }

  function collectQuantityValuesFromForm(form, attrPrefix) {
    const valuesByRule = {};
    if (!form) {
      return valuesByRule;
    }

    getFormQuantityPayloadInputs(form).forEach((inputEl) => {
      const ruleKey = normalizeKey(String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, ""));
      if (!ruleKey) {
        return;
      }
      valuesByRule[ruleKey] = deserializeItems(inputEl.value);
    });

    const selector = `[${attrPrefix}-field-key], [data-process-quantity-field-key]`;
    form.querySelectorAll(selector).forEach((controlEl) => {
      const ruleKey = normalizeKey(controlEl.getAttribute(`${attrPrefix}-rule-key`) || controlEl.getAttribute("data-process-quantity-rule-key"));
      const fieldKey = normalizeKey(controlEl.getAttribute(`${attrPrefix}-field-key`) || controlEl.getAttribute("data-process-quantity-field-key"));
      const itemIndex = Number.parseInt(String(controlEl.getAttribute(`${attrPrefix}-index`) || controlEl.getAttribute("data-process-quantity-index") || "").trim(), 10);
      if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0) {
        return;
      }
      if (!Array.isArray(valuesByRule[ruleKey])) {
        valuesByRule[ruleKey] = [];
      }
      while (valuesByRule[ruleKey].length <= itemIndex) {
        valuesByRule[ruleKey].push({});
      }
      if (controlEl.type === "checkbox") {
        valuesByRule[ruleKey][itemIndex][fieldKey] = controlEl.checked ? "1" : "0";
        return;
      }
      valuesByRule[ruleKey][itemIndex][fieldKey] = String(controlEl.value || "").trim();
    });

    return valuesByRule;
  }

  function syncHiddenPayloads(form, valuesByRule, payloadMarkerAttr, inputNamePrefix) {
    if (!form) {
      return;
    }

    form.querySelectorAll(`[${payloadMarkerAttr}='1']`).forEach((node) => node.remove());

    Object.keys(valuesByRule || {}).forEach((rawRuleKey) => {
      const ruleKey = normalizeKey(rawRuleKey);
      if (!ruleKey) {
        return;
      }

      const hiddenInputEl = document.createElement("input");
      hiddenInputEl.type = "hidden";
      hiddenInputEl.name = `${inputNamePrefix || "process_quantity_payload__"}${ruleKey}`;
      hiddenInputEl.value = serializeItems(valuesByRule[ruleKey]);
      hiddenInputEl.setAttribute(payloadMarkerAttr, "1");
      form.appendChild(hiddenInputEl);
    });
  }

  function createMeuPerfilQuantityAdapterV1(options = {}) {
    const root = options.root || document;
    const personalCardEl = root.getElementById ? root.getElementById("perfil-pessoal-card") : document.getElementById("perfil-pessoal-card");
    const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
    const readonlyGridEl = personalCardEl ? personalCardEl.querySelector(".profile-readonly .personal-grid") : null;
    const editGridEl = formEl ? formEl.querySelector(".personal-grid") : null;
    const setting = typeof options.getSetting === "function" ? options.getSetting() : null;
    const rules = normalizeRules(setting && setting.process_quantity_fields);

    return {
      root,
      personalCardEl,
      formEl,
      readonlyGridEl,
      editGridEl,
      setting,
      rules,
      getValues() {
        return collectQuantityValuesFromForm(formEl, "data-meu-perfil-quantity");
      },
      sync(valuesByRule) {
        syncHiddenPayloads(formEl, valuesByRule, "data-meu-perfil-quantity-payload", "process_quantity_payload__");
      },
      resolveFieldMetaMap() {
        return buildFieldMetaMap(setting);
      },
      getCurrentSection() {
        return getCurrentProfileSection(root);
      }
    };
  }

  function createDynamicProcessQuantityAdapterV1(options = {}) {
    const root = options.root || document;
    const formEl = options.formEl || root.querySelector("form[data-process-edit-form='1'], form[data-process-edit-form], form");
    const readonlyGridEl = options.readonlyGridEl || root.querySelector("[data-dynamic-process-quantity-readonly-grid]");
    const editGridEl = options.editGridEl || root.querySelector("[data-dynamic-process-quantity-edit-grid]");
    const setting = typeof options.getSetting === "function" ? options.getSetting() : null;
    const rules = normalizeRules(setting && setting.process_quantity_fields);

    return {
      root,
      formEl,
      readonlyGridEl,
      editGridEl,
      setting,
      rules,
      getValues() {
        return collectQuantityValuesFromForm(formEl, "data-process-quantity");
      },
      sync(valuesByRule) {
        syncHiddenPayloads(formEl, valuesByRule, "data-process-quantity-payload", "process_quantity_payload__");
      },
      resolveFieldMetaMap() {
        return buildFieldMetaMap(setting);
      },
      getCurrentSection() {
        return String(
          (typeof options.getCurrentSection === "function" ? options.getCurrentSection() : "")
        ).trim();
      }
    };
  }

  function initialize(context) {
    if (!context || typeof context !== "object") {
      return null;
    }

    return context;
  }

  function render(context) {
    return context || null;
  }

  function sync(context) {
    return context || null;
  }

  function getValues(context) {
    return context && typeof context.getValues === "function" ? context.getValues() : {};
  }

  function destroy(context) {
    return context || null;
  }

  window.AppGenesisProcessQuantityRuntimeV1 = {
    initialize,
    render,
    sync,
    getValues,
    destroy,
    normalizeRules,
    normalizeItems,
    calculateItemCount,
    resizeItems,
    buildFieldMetaMap,
    buildFieldMetaByKey,
    serializeItems,
    deserializeItems,
    validateRule,
    createMeuPerfilQuantityAdapterV1,
    createDynamicProcessQuantityAdapterV1,
    collectValuesFromForm,
    resolveControlName,
    getProfileForm,
    getCurrentProfileSection
  };
})();
