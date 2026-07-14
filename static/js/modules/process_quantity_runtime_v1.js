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
  const stateByForm = new WeakMap();

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

  function normalizeProcessFieldType(value) {
    const cleanType = normalizeKey(value);
    return cleanType || "text";
  }

  function isTruthyFlagValue(value) {
    return ["1", "true", "sim", "yes", "on"].includes(normalizeLookupText(value));
  }

  function resolveForm(root) {
    const scope = root && typeof root.querySelector === "function" ? root : document;
    return (
      scope.querySelector('form[action="/users/profile/personal"]') ||
      scope.querySelector("#perfil-pessoal-card form") ||
      scope.querySelector("form[data-process-edit-form='1'], form[data-process-edit-form], form") ||
      null
    );
  }

  function getCurrentSectionFromContext(context) {
    if (context && typeof context.getCurrentSection === "function") {
      return normalizeKey(context.getCurrentSection());
    }
    return "";
  }

  function getSettingFromContext(context) {
    if (context && typeof context.getSetting === "function") {
      return context.getSetting() || null;
    }
    return context && context.setting ? context.setting : null;
  }

  function resolveRulesFromContext(context) {
    const setting = getSettingFromContext(context);
    const rawRules = (context && Array.isArray(context.rules) ? context.rules : null) || (setting && setting.process_quantity_fields) || [];
    return normalizeRules(rawRules);
  }

  function getRuntimeState(context) {
    if (!context || typeof context !== "object") {
      return null;
    }

    if (!context.__appGenesisProcessQuantityRuntimeV1) {
      context.__appGenesisProcessQuantityRuntimeV1 = {
        listeners: [],
        renderedKeys: new Set(),
        destroyed: false
      };
    }

    return context.__appGenesisProcessQuantityRuntimeV1;
  }

  function clearRuntimeListeners(state) {
    if (!state || !Array.isArray(state.listeners)) {
      return;
    }

    state.listeners.forEach((binding) => {
      if (binding && binding.target && binding.type && binding.handler) {
        binding.target.removeEventListener(binding.type, binding.handler, Boolean(binding.capture));
      }
    });

    state.listeners = [];
  }

  function bindListener(state, target, type, handler, capture) {
    if (!state || !target || !type || typeof handler !== "function") {
      return;
    }

    target.addEventListener(type, handler, Boolean(capture));
    state.listeners.push({ target, type, handler, capture: Boolean(capture) });
  }

  function getRuleHostMarkers(ruleKey) {
    return {
      payloadMarkerAttr: "data-process-quantity-payload",
      hostAttr: "data-process-quantity-rule-key",
      ruleKey: normalizeKey(ruleKey)
    };
  }

  function readRuleValues(form, rule, controlPrefix) {
    const values = deserializeItems(
      form && typeof form.querySelector === "function"
        ? (form.querySelector(`input[name="process_quantity_payload__${rule.key}"]`) || {}).value
        : "[]"
    );
    const selector = `[${controlPrefix}-rule-key], [data-process-quantity-rule-key]`;
    const source = form && typeof form.querySelectorAll === "function" ? form.querySelectorAll(selector) : [];

    source.forEach((controlEl) => {
      const ruleKey = normalizeKey(controlEl.getAttribute(`${controlPrefix}-rule-key`) || controlEl.getAttribute("data-process-quantity-rule-key"));
      const fieldKey = normalizeKey(controlEl.getAttribute(`${controlPrefix}-field-key`) || controlEl.getAttribute("data-process-quantity-field-key"));
      const itemIndex = Number.parseInt(String(controlEl.getAttribute(`${controlPrefix}-index`) || controlEl.getAttribute("data-process-quantity-index") || "").trim(), 10);

      if (!ruleKey || !fieldKey || !Number.isFinite(itemIndex) || itemIndex < 0 || ruleKey !== rule.key) {
        return;
      }

      while (values.length <= itemIndex) {
        values.push({});
      }

      if (controlEl.type === "checkbox") {
        values[itemIndex][fieldKey] = controlEl.checked ? "1" : "0";
        return;
      }

      values[itemIndex][fieldKey] = String(controlEl.value || "").trim();
    });

    return values;
  }

  function ensureHiddenPayloadInput(form, ruleKey, markerAttr, value) {
    if (!form || !ruleKey) {
      return null;
    }

    const cleanRuleKey = normalizeKey(ruleKey);
    let hiddenInputEl = form.querySelector(`input[name="process_quantity_payload__${cleanRuleKey}"]`);

    if (!hiddenInputEl) {
      hiddenInputEl = document.createElement("input");
      hiddenInputEl.type = "hidden";
      hiddenInputEl.name = `process_quantity_payload__${cleanRuleKey}`;
      hiddenInputEl.setAttribute(markerAttr, "1");
      form.appendChild(hiddenInputEl);
    }

    hiddenInputEl.value = serializeItems(value || []);
    return hiddenInputEl;
  }

  function removeGeneratedRuleNodes(root, selector) {
    if (!root || typeof root.querySelectorAll !== "function") {
      return;
    }

    root.querySelectorAll(selector).forEach((node) => node.remove());
  }

  function buildFieldControl(rule, itemIndex, fieldMeta, currentValue, ruleKeyAttrPrefix) {
    const fieldType = normalizeProcessFieldType(fieldMeta.fieldType);
    let controlEl = null;

    if (fieldType === "list") {
      controlEl = document.createElement("select");
      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      controlEl.appendChild(emptyOption);

      (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
        const option = document.createElement("option");
        option.value = String(optionValue || "").trim();
        option.textContent = option.value;
        option.selected = option.value === String(currentValue || "").trim();
        controlEl.appendChild(option);
      });
    } else if (fieldType === "flag") {
      controlEl = document.createElement("input");
      controlEl.type = "checkbox";
      controlEl.value = "1";
      controlEl.checked = isTruthyFlagValue(currentValue);
    } else {
      controlEl = document.createElement("input");
      controlEl.type = TEXTUAL_TYPES.has(fieldType) ? fieldType : "text";
      controlEl.value = String(currentValue || "").trim();
    }

    controlEl.name = `process_quantity_field__${rule.key}__${itemIndex}__${fieldMeta.key}`;
    controlEl.dataset.processQuantityRuleKey = rule.key;
    controlEl.dataset.processQuantityItemIndex = String(itemIndex);
    controlEl.dataset.processQuantityFieldKey = fieldMeta.key;
    controlEl.dataset.processQuantityFieldType = fieldType;

    if (ruleKeyAttrPrefix) {
      controlEl.setAttribute(`${ruleKeyAttrPrefix}-rule-key`, rule.key);
      controlEl.setAttribute(`${ruleKeyAttrPrefix}-index`, String(itemIndex));
      controlEl.setAttribute(`${ruleKeyAttrPrefix}-field-key`, fieldMeta.key);
    }

    if (fieldMeta.isRequired && fieldType !== "flag") {
      controlEl.required = true;
    }

    if (fieldMeta.size && TEXTUAL_TYPES.has(fieldType)) {
      controlEl.maxLength = fieldMeta.size;
    }

    return controlEl;
  }

  function resolveQuantityCountFromControl(controlValue, maxItems) {
    const parsedValue = Number.parseInt(toSafeString(controlValue).trim(), 10);
    const parsedMaxItems = Number.parseInt(toSafeString(maxItems || DEFAULT_MAX_ITEMS).trim(), 10);
    const safeMaxItems = Number.isFinite(parsedMaxItems)
      ? Math.min(Math.max(parsedMaxItems, 1), 50)
      : DEFAULT_MAX_ITEMS;

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 0;
    }

    return Math.min(parsedValue, safeMaxItems);
  }

  function renderProfileQuantityRule(context, rule, valuesByRule, fieldMetaMap) {
    const root = context.root || document;
    const formEl = context.formEl || resolveForm(root);
    const readonlyGridEl = context.readonlyGridEl || (root.querySelector("#perfil-pessoal-card .profile-readonly .personal-grid") || null);
    const editGridEl = context.editGridEl || (formEl ? formEl.querySelector(".personal-grid") : null);
    const setting = getSettingFromContext(context);
    const quantityControlName = resolveControlName(rule.quantityFieldKey);
    const quantityControl = formEl ? formEl.querySelector(`[name="${quantityControlName}"]`) : null;
    const quantityWrapper = quantityControl ? (quantityControl.closest(".field") || quantityControl.parentElement) : null;
    const sectionPane = normalizeKey(rule.headerKey || getCurrentSectionFromContext(context) || "");
    const existingItems = resizeItems(valuesByRule[rule.key] || [], resolveQuantityCountFromControl(quantityControl ? quantityControl.value : "", rule.maxItems) || (valuesByRule[rule.key] || []).length);
    const readonlyAnchor = readonlyGridEl ? readonlyGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`) : null;
    const editAnchor = editGridEl ? editGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`) : null;

    if (!readonlyGridEl && !editGridEl) {
      return;
    }

    if (readonlyGridEl) {
      removeGeneratedRuleNodes(readonlyGridEl, `[data-process-quantity-generated='1'][data-process-quantity-rule-key="${rule.key}"]`);
    }
    if (editGridEl) {
      removeGeneratedRuleNodes(editGridEl, `[data-process-quantity-generated='1'][data-process-quantity-rule-key="${rule.key}"]`);
    }

    let host = null;
    if (editGridEl) {
      host = document.createElement("div");
      host.className = "field full profile-quantity-rule-v1";
      host.dataset.processQuantityGenerated = "1";
      host.dataset.processQuantityRuleKey = rule.key;
      host.dataset.profileSectionPane = sectionPane;

      if (quantityWrapper && quantityWrapper.parentElement) {
        quantityWrapper.insertAdjacentElement("afterend", host);
      } else {
        editGridEl.appendChild(host);
      }

      const hiddenInput = ensureHiddenPayloadInput(formEl, rule.key, "data-process-quantity-payload", valuesByRule[rule.key] || []);
      if (hiddenInput) {
        hiddenInput.dataset.processQuantityGenerated = "1";
      }

      existingItems.forEach((itemValues, itemIndex) => {
        const itemBlock = document.createElement("div");
        itemBlock.className = "profile-quantity-item-v1";
        itemBlock.dataset.processQuantityItemIndex = String(itemIndex);

        const itemTitle = document.createElement("h4");
        itemTitle.className = "profile-quantity-item-title-v1";
        itemTitle.textContent = `${rule.itemLabel || "Item"} ${itemIndex + 1}`;
        itemBlock.appendChild(itemTitle);

        const fieldsGrid = document.createElement("div");
        fieldsGrid.className = "personal-grid profile-quantity-item-grid-v1";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey);
          if (!fieldMeta) {
            return;
          }

          const fieldWrapper = document.createElement("div");
          fieldWrapper.className = "field";
          fieldWrapper.dataset.profileSectionPane = sectionPane;
          fieldWrapper.dataset.profileFieldKey = fieldKey;

          const label = document.createElement("label");
          label.textContent = `${fieldMeta.label || fieldKey}${fieldMeta.isRequired ? " *" : ""}`;

          const controlEl = buildFieldControl(rule, itemIndex, fieldMeta, itemValues[fieldKey] || "", "data-process-quantity");
          controlEl.addEventListener("input", () => sync(context));
          controlEl.addEventListener("change", () => sync(context));

          fieldWrapper.appendChild(label);
          fieldWrapper.appendChild(controlEl);
          fieldsGrid.appendChild(fieldWrapper);
        });

        itemBlock.appendChild(fieldsGrid);
        host.appendChild(itemBlock);
      });
    }

    if (readonlyGridEl && existingItems.length) {
      const readonlyHost = document.createElement("div");
      readonlyHost.className = "personal-item profile-quantity-readonly-v1";
      readonlyHost.dataset.processQuantityGenerated = "1";
      readonlyHost.dataset.processQuantityRuleKey = rule.key;
      readonlyHost.dataset.profileSectionPane = sectionPane;
      readonlyHost.style.gridColumn = "1 / -1";

      const mainLabel = document.createElement("span");
      mainLabel.className = "personal-label";
      mainLabel.textContent = rule.label || rule.itemLabel || "Itens";
      readonlyHost.appendChild(mainLabel);

      const listWrapper = document.createElement("div");
      listWrapper.className = "profile-quantity-readonly-list-v1";

      existingItems.forEach((itemValues, itemIndex) => {
        const itemBlock = document.createElement("div");
        itemBlock.className = "profile-quantity-readonly-item-v1";

        const itemTitle = document.createElement("strong");
        itemTitle.className = "personal-value profile-quantity-readonly-title-v1";
        itemTitle.textContent = `${rule.itemLabel || "Item"} ${itemIndex + 1}`;
        itemBlock.appendChild(itemTitle);

        const fieldsList = document.createElement("div");
        fieldsList.className = "profile-quantity-readonly-fields-v1";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey) || { label: fieldKey, fieldType: "text" };
          const row = document.createElement("div");
          row.className = "profile-quantity-readonly-field-v1";

          const label = document.createElement("span");
          label.className = "personal-label";
          label.textContent = fieldMeta.label || fieldKey;

          const value = document.createElement("strong");
          value.className = "personal-value";
          value.textContent = normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
            ? (isTruthyFlagValue(itemValues[fieldKey]) ? "Sim" : "Não")
            : (String(itemValues[fieldKey] || "").trim() || "-");

          row.appendChild(label);
          row.appendChild(value);
          fieldsList.appendChild(row);
        });

        itemBlock.appendChild(fieldsList);
        listWrapper.appendChild(itemBlock);
      });

      readonlyHost.appendChild(listWrapper);
      if (readonlyAnchor && readonlyAnchor.parentElement === readonlyGridEl) {
        readonlyAnchor.insertAdjacentElement("afterend", readonlyHost);
      } else {
        readonlyGridEl.appendChild(readonlyHost);
      }
    }
  }

  function renderDynamicQuantityRule(context, rule, valuesByRule, fieldMetaMap) {
    const root = context.root || document;
    const formEl = context.formEl || resolveForm(root);
    const editGridEl = context.editGridEl || root.querySelector("[data-dynamic-process-quantity-edit-grid]");
    const readonlyGridEl = context.readonlyGridEl || root.querySelector("[data-dynamic-process-quantity-readonly-grid]");
    const quantityAnchor = editGridEl ? editGridEl.querySelector(`[data-profile-field-key="${rule.quantityFieldKey}"]`) : null;
    const ruleValues = Array.isArray(valuesByRule[rule.key]) ? valuesByRule[rule.key] : [];
    const count = resolveQuantityCountFromControl(
      root.querySelector(`[name="${resolveControlName(rule.quantityFieldKey)}"]`)?.value,
      rule.maxItems
    ) || ruleValues.length;
    const selectedValues = resizeItems(ruleValues, count);

    if (editGridEl) {
      removeGeneratedRuleNodes(editGridEl, `[data-process-quantity-generated='1'][data-process-quantity-rule-key="${rule.key}"]`);
    }
    if (readonlyGridEl) {
      removeGeneratedRuleNodes(readonlyGridEl, `[data-process-quantity-generated='1'][data-process-quantity-rule-key="${rule.key}"]`);
    }

    if (editGridEl && selectedValues.length) {
      const host = document.createElement("div");
      host.className = "field full dynamic-process-quantity-editor-block";
      host.dataset.processQuantityGenerated = "1";
      host.dataset.processQuantityRuleKey = rule.key;
      selectedValues.forEach((itemValues, itemIndex) => {
        const itemWrapEl = document.createElement("div");
        itemWrapEl.className = "dynamic-process-quantity-item-edit";

        const itemHeadingEl = document.createElement("h4");
        itemHeadingEl.textContent = `${rule.itemLabel || "Item"} ${itemIndex + 1}`;
        itemWrapEl.appendChild(itemHeadingEl);

        const itemGridEl = document.createElement("div");
        itemGridEl.className = "grid settings-general-grid";

        rule.repeatedFieldKeys.forEach((fieldKey) => {
          const fieldMeta = fieldMetaMap.get(fieldKey);
          if (!fieldMeta) {
            return;
          }

          const fieldContainerEl = document.createElement("div");
          fieldContainerEl.className = "field";

          const inputId = `process_quantity_${rule.key}_${itemIndex}_${fieldKey}`.replace(/[^a-z0-9_]+/gi, "_");
          const labelEl = document.createElement("label");
          labelEl.setAttribute("for", inputId);
          labelEl.textContent = `${fieldMeta.label || fieldKey}${fieldMeta.isRequired ? " *" : ""}`;
          fieldContainerEl.appendChild(labelEl);

          const controlEl = buildFieldControl(rule, itemIndex, fieldMeta, itemValues[fieldKey] || "", "data-process-quantity");
          controlEl.id = inputId;
          controlEl.addEventListener("input", () => sync(context));
          controlEl.addEventListener("change", () => sync(context));
          fieldContainerEl.appendChild(controlEl);
          itemGridEl.appendChild(fieldContainerEl);
        });

        itemWrapEl.appendChild(itemGridEl);
        host.appendChild(itemWrapEl);
      });

      if (quantityAnchor && quantityAnchor.parentElement === editGridEl) {
        quantityAnchor.insertAdjacentElement("afterend", host);
      } else {
        editGridEl.appendChild(host);
      }
    }
  }

  function renderQuantityContext(context) {
    const safeContext = context && typeof context === "object" ? context : {};
    const state = getRuntimeState(safeContext);
    const rules = resolveRulesFromContext(safeContext);
    const setting = getSettingFromContext(safeContext);
    const formEl = safeContext.formEl || resolveForm(safeContext.root);
    const fieldMetaMap = typeof safeContext.resolveFieldMetaMap === "function"
      ? safeContext.resolveFieldMetaMap()
      : buildFieldMetaMap(setting);
    const valuesByRule = typeof safeContext.getValues === "function"
      ? safeContext.getValues()
      : (safeContext.valuesByRule || {});

    if (!state || state.destroyed) {
      return safeContext;
    }

    state.formEl = formEl || state.formEl || null;
    state.setting = setting;
    state.rules = rules;
    state.fieldMetaMap = fieldMetaMap;

    rules.forEach((rule) => {
      if (safeContext.mode === "profile" || safeContext.adapterName === "profile") {
        renderProfileQuantityRule(safeContext, rule, valuesByRule, fieldMetaMap);
        return;
      }

      renderDynamicQuantityRule(safeContext, rule, valuesByRule, fieldMetaMap);
    });

    return safeContext;
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
    const safeContext = context && typeof context === "object" ? context : null;

    if (!safeContext) {
      return null;
    }

    const formEl = safeContext.formEl || resolveForm(safeContext.root);
    if (!formEl) {
      return safeContext;
    }

    const state = getRuntimeState(safeContext);
    if (!state || state.destroyed) {
      return safeContext;
    }

    if (state.formEl === formEl && state.initialized === true) {
      return safeContext;
    }

    destroy(safeContext);
    const nextState = getRuntimeState(safeContext);
    nextState.formEl = formEl;
    nextState.root = safeContext.root || document;
    nextState.initialized = true;
    nextState.destroyed = false;

    const scheduleRender = () => {
      renderQuantityContext(safeContext);
    };
    const scheduleSync = () => {
      sync(safeContext);
    };

    bindListener(nextState, formEl, "input", (event) => {
      const target = event.target;
      if (!target) {
        return;
      }
      if (target.matches && target.matches("[data-process-quantity-field-key], [data-meu-perfil-quantity-field-key]")) {
        scheduleSync();
        return;
      }
      if (target.matches && target.matches("[name^='process_quantity_payload__']")) {
        scheduleSync();
      }
      if (target.matches && target.matches("[name='" + resolveControlName((nextState.rules[0] && nextState.rules[0].quantityFieldKey) || "") + "']")) {
        scheduleRender();
        scheduleSync();
      }
    }, true);

    bindListener(nextState, formEl, "change", (event) => {
      const target = event.target;
      if (!target) {
        return;
      }
      if (target.matches && target.matches("[data-process-quantity-field-key], [data-meu-perfil-quantity-field-key]")) {
        scheduleSync();
        return;
      }
      scheduleRender();
      scheduleSync();
    }, true);

    bindListener(nextState, formEl, "submit", () => {
      sync(safeContext);
    }, true);

    renderQuantityContext(safeContext);
    sync(safeContext);
    return safeContext;
  }

  function render(context) {
    return renderQuantityContext(context);
  }

  function sync(context) {
    const safeContext = context && typeof context === "object" ? context : null;
    if (!safeContext) {
      return null;
    }

    const state = getRuntimeState(safeContext);
    const formEl = safeContext.formEl || (state && state.formEl) || resolveForm(safeContext.root);
    if (!formEl) {
      return safeContext;
    }

    const rules = resolveRulesFromContext(safeContext);
    const valuesByRule = {};

    rules.forEach((rule) => {
      if (typeof safeContext.getValues === "function" && safeContext.getValues !== getValues) {
        const resolved = safeContext.getValues();
        if (resolved && Array.isArray(resolved[rule.key])) {
          valuesByRule[rule.key] = resolved[rule.key];
          return;
        }
      }

      valuesByRule[rule.key] = readRuleValues(formEl, rule, "data-process-quantity");
    });

    rules.forEach((rule) => {
      const nextValues = Array.isArray(valuesByRule[rule.key]) ? valuesByRule[rule.key] : [];
      ensureHiddenPayloadInput(formEl, rule.key, "data-process-quantity-payload", nextValues);
    });

    if (state) {
      state.lastValuesByRule = valuesByRule;
      state.rules = rules;
    }

    if (safeContext.adapter && typeof safeContext.adapter.sync === "function") {
      safeContext.adapter.sync(valuesByRule);
    }

    return valuesByRule;
  }

  function getValues(context) {
    const safeContext = context && typeof context === "object" ? context : null;
    if (!safeContext) {
      return {};
    }

    if (typeof safeContext.getValues === "function" && safeContext.getValues !== getValues) {
      return safeContext.getValues();
    }

    const formEl = safeContext.formEl || resolveForm(safeContext.root);
    if (!formEl) {
      return {};
    }

    const rules = resolveRulesFromContext(safeContext);
    const valuesByRule = {};
    rules.forEach((rule) => {
      valuesByRule[rule.key] = readRuleValues(formEl, rule, "data-process-quantity");
    });
    return valuesByRule;
  }

  function destroy(context) {
    const safeContext = context && typeof context === "object" ? context : null;
    if (!safeContext) {
      return null;
    }

    const state = getRuntimeState(safeContext);
    if (!state || state.destroyed) {
      return safeContext;
    }

    clearRuntimeListeners(state);
    const formEl = state.formEl || safeContext.formEl || null;
    if (formEl) {
      removeGeneratedRuleNodes(formEl, "[data-process-quantity-generated='1']");
      formEl.querySelectorAll("input[data-process-quantity-payload='1']").forEach((inputEl) => {
        if (inputEl.name && inputEl.name.startsWith("process_quantity_payload__")) {
          inputEl.remove();
        }
      });
      delete formEl.dataset.processQuantityRuntimeBoundV1;
    }

    state.destroyed = true;
    state.initialized = false;
    return safeContext;
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
