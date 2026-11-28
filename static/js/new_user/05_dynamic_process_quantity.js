// new_user/05_dynamic_process_quantity.js: Processo dinamico e Meu Perfil: grupos de quantidade.
// Scripts classicos com escopo global partilhado; carregar pela ordem de templates/new_user.html.

function buildProcessOptionMetaMap(setting) {
  const metaByKey = new Map();
  const processListsByKey = new Map();
  const processLists = Array.isArray(setting && setting.process_lists) ? setting.process_lists : [];
  processLists.forEach((processList) => {
    const listKey = normalizeMenuKey(processList && processList.key);
    if (!listKey) {
      return;
    }
    processListsByKey.set(
      listKey,
      Array.isArray(processList.items)
        ? processList.items.map((item) => String(item || "").trim()).filter(Boolean)
        : []
    );
  });

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
      listOptions: processListsByKey.get(listKey) || [],
      isRequired: normalizeProcessFieldRequired(optionRequiredRaw)
    });
  });

  return metaByKey;
}

function collectCurrentDynamicProcessQuantityValues(menuKey) {
  const cleanMenuKey = normalizeMenuKey(menuKey);
  const baseValues = (
    menuProcessQuantityValuesMap &&
    menuProcessQuantityValuesMap[cleanMenuKey] &&
    typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
  )
    ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
    : {};
  if (!dynamicProcessEditFormEl) {
    return baseValues;
  }

  const payloadInputs = dynamicProcessEditFormEl.querySelectorAll("[name^='process_quantity_payload__']");
  payloadInputs.forEach((inputEl) => {
    const ruleKey = normalizeMenuKey(String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, ""));
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

  const fieldInputs = dynamicProcessEditFormEl.querySelectorAll("[data-process-quantity-field-key]");
  fieldInputs.forEach((controlEl) => {
    const ruleKey = normalizeMenuKey(controlEl.getAttribute("data-process-quantity-rule-key"));
    const itemIndex = Number.parseInt(String(controlEl.getAttribute("data-process-quantity-index") || "").trim(), 10);
    const fieldKey = normalizeMenuKey(controlEl.getAttribute("data-process-quantity-field-key"));
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
    hiddenInputEl.value = JSON.stringify(normalizeProcessQuantityItems(quantityValuesByRule[ruleKey]));
    hiddenInputEl.setAttribute("data-process-quantity-payload", "1");
    hiddenInputEl.setAttribute("data-process-quantity-menu-key", cleanMenuKey);
    hiddenInputEl.setAttribute("data-process-quantity-rule-key", ruleKey);
    dynamicProcessEditFormEl.appendChild(hiddenInputEl);
  });
}

function collectCurrentMeuPerfilQuantityValues() {
  const cleanMenuKey = MEU_PERFIL_MENU_KEY;
  const baseValues = (
    menuProcessQuantityValuesMap &&
    menuProcessQuantityValuesMap[cleanMenuKey] &&
    typeof menuProcessQuantityValuesMap[cleanMenuKey] === "object"
  )
    ? JSON.parse(JSON.stringify(menuProcessQuantityValuesMap[cleanMenuKey]))
    : {};
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  if (!formEl) {
    return baseValues;
  }

  formEl.querySelectorAll("[data-meu-perfil-quantity-payload='1']").forEach((inputEl) => {
    const ruleKey = normalizeMenuKey(String(inputEl.getAttribute("name") || "").replace(/^process_quantity_payload__/, ""));
    if (!ruleKey) {
      return;
    }
    try {
      baseValues[ruleKey] = normalizeProcessQuantityItems(JSON.parse(String(inputEl.value || "[]")));
    } catch (error) {
      baseValues[ruleKey] = [];
    }
  });

  formEl.querySelectorAll("[data-meu-perfil-quantity-field-key]").forEach((controlEl) => {
    const ruleKey = normalizeMenuKey(controlEl.getAttribute("data-meu-perfil-quantity-rule-key"));
    const fieldKey = normalizeMenuKey(controlEl.getAttribute("data-meu-perfil-quantity-field-key"));
    const itemIndex = Number.parseInt(String(controlEl.getAttribute("data-meu-perfil-quantity-index") || "").trim(), 10);
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

  formEl.querySelectorAll("[data-meu-perfil-quantity-payload='1']").forEach((inputEl) => inputEl.remove());

  // O renderizador V1 (setupMeuPerfilQuantityRulesV1) ja envia o payload dos itens; este nao pode duplica-lo.
  if (formEl.dataset.meuPerfilQuantityRendererBoundV1 === "1") {
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
    hiddenInputEl.value = JSON.stringify(normalizeProcessQuantityItems(quantityValuesByRule[ruleKey]));
    hiddenInputEl.setAttribute("data-meu-perfil-quantity-payload", "1");
    formEl.appendChild(hiddenInputEl);
  });
}

function renderMeuPerfilQuantityGroups() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const readonlyGridEl = personalCardEl ? personalCardEl.querySelector(".profile-readonly .personal-grid") : null;
  const formEl = personalCardEl ? personalCardEl.querySelector(".profile-edit-form") : null;
  const editGridEl = formEl ? formEl.querySelector(".personal-grid") : null;
  const setting = getSidebarMenuSetting(MEU_PERFIL_MENU_KEY);
  const normalizedRules = normalizeProcessQuantityRules(setting && setting.process_quantity_fields);
  if (!readonlyGridEl && !editGridEl) {
    return;
  }

  if (readonlyGridEl) {
    readonlyGridEl.querySelectorAll("[data-meu-perfil-quantity-generated='1']").forEach((node) => node.remove());
  }
  if (editGridEl) {
    editGridEl.querySelectorAll("[data-meu-perfil-quantity-generated='1']").forEach((node) => node.remove());
  }

  if (!setting || !normalizedRules.length) {
    syncMeuPerfilQuantityHiddenInputs({});
    return;
  }

  const processValuesByField = collectCurrentMeuPerfilProcessValues();
  const quantityValuesByRule = collectCurrentMeuPerfilQuantityValues();
  const nextQuantityValuesByRule = { ...quantityValuesByRule };
  const optionMetaByKey = buildProcessOptionMetaMap(setting);
  const activeSectionKey = normalizeMenuKey(meuPerfilSelectedProfileSection || (profilePersonalSections[0] && profilePersonalSections[0].key) || "");

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

    const sourceValueRaw = Number.parseInt(String(processValuesByField[rule.quantityFieldKey] || "").trim(), 10);
    const desiredCount = Number.isFinite(sourceValueRaw)
      ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
      : 0;
    // Ordem do campo origem: a que ja tem no formulario (a variavel profilePersonalVisibleFields nao existe neste escopo).
    const originAnchorEl = editAnchorEl || readOnlyAnchorEl;
    const baseOrder = (originAnchorEl && Number.parseInt(getComputedStyle(originAnchorEl).order, 10)) || 0;
    if (readOnlyAnchorEl) {
      readOnlyAnchorEl.style.order = String(baseOrder);
    }
    if (editAnchorEl) {
      editAnchorEl.style.order = String(baseOrder);
    }
    const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
    const nextItems = [];
    for (let index = 0; index < desiredCount; index += 1) {
      nextItems.push(existingItems[index] && typeof existingItems[index] === "object"
        ? { ...existingItems[index] }
        : {});
    }
    nextQuantityValuesByRule[rule.key] = nextItems;

    // Leitura: o bloco por colunas (renderReadonlyRuleQuantityReadonlyV1) substitui este bloco empilhado; nao gerar duplicado.
    if (false && readonlyGridEl && nextItems.length) {
      const groupEl = document.createElement("div");
      groupEl.className = "personal-item";
      groupEl.style.gridColumn = "1 / -1";
      // Grupo repetido no fim da aba (depois dos campos fixos, ordem 190/200), por pedido.
      groupEl.style.order = "300";
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
          valueTextEl.textContent = normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
            ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
            : (rawValue || "-");

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

    if (false && editGridEl && nextItems.length) {
      const blockEl = document.createElement("div");
      blockEl.className = "field full dynamic-process-quantity-editor-block";
      blockEl.style.order = "300";
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

          const inputId = `meu_perfil_quantity_${rule.key}_${index}_${fieldKey}`.replace(/[^a-z0-9_]+/gi, "_");
          const currentValue = String(itemValues[fieldKey] || "").trim();
          const labelEl = document.createElement("label");
          labelEl.setAttribute("for", inputId);
          labelEl.textContent = fieldMeta.isRequired ? `${fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey} *` : (fieldMeta.label || profilePersonalFieldLabels[fieldKey] || fieldKey);
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
            (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
              const optionEl = document.createElement("option");
              optionEl.value = String(optionValue || "").trim();
              optionEl.textContent = String(optionValue || "").trim();
              optionEl.selected = optionEl.value === currentValue;
              controlEl.appendChild(optionEl);
            });
            fieldContainerEl.appendChild(controlEl);
          } else {
            controlEl = document.createElement("input");
            controlEl.type = getDynamicProcessInputType(fieldType);
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

  syncMeuPerfilQuantityHiddenInputs(nextQuantityValuesByRule);
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
  const normalizedRules = normalizeProcessQuantityRules(setting && setting.process_quantity_fields);
  if (!normalizedRules.length) {
    syncDynamicProcessQuantityHiddenInputs(cleanMenuKey, {});
    return;
  }

  const selectedSectionKey = normalizeMenuKey(selectedSection && selectedSection.key) || "__geral__";
  const optionMetaByKey = buildProcessOptionMetaMap(setting);
  const currentSectionFieldKeys = new Set(
    Array.isArray(sectionFields)
      ? sectionFields
        .map((field) => normalizeMenuKey(field && field.key))
        .filter(Boolean)
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
    const sourceValueRaw = Number.parseInt(String(processValuesByField[rule.quantityFieldKey] || "").trim(), 10);
    const desiredCount = Number.isFinite(sourceValueRaw)
      ? Math.min(Math.max(sourceValueRaw, 0), rule.maxItems)
      : 0;
    const existingItems = normalizeProcessQuantityItems(nextQuantityValuesByRule[rule.key]);
    const nextItems = [];

    for (let index = 0; index < desiredCount; index += 1) {
      nextItems.push(existingItems[index] && typeof existingItems[index] === "object"
        ? { ...existingItems[index] }
        : {});
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
            valueTextEl.textContent = normalizeProcessFieldType(fieldMeta.fieldType) === "flag"
              ? (isTruthyFlagValue(rawValue) ? "Sim" : "Não")
              : (rawValue || "-");

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

            const inputId = `dynamic_quantity_${cleanMenuKey}_${rule.key}_${index}_${fieldKey}`
              .replace(/[^a-z0-9_]+/gi, "_");
            const currentValue = String(itemValues[fieldKey] || "").trim();

            const labelEl = document.createElement("label");
            labelEl.setAttribute("for", inputId);
            labelEl.textContent = fieldMeta.isRequired ? `${fieldMeta.label || fieldKey} *` : (fieldMeta.label || fieldKey);
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

              (Array.isArray(fieldMeta.listOptions) ? fieldMeta.listOptions : []).forEach((optionValue) => {
                const optionEl = document.createElement("option");
                optionEl.value = String(optionValue || "");
                optionEl.textContent = String(optionValue || "");
                if (String(optionValue || "") === currentValue) {
                  optionEl.selected = true;
                }
                selectEl.appendChild(optionEl);
              });

              fieldContainerEl.appendChild(selectEl);
            } else {
              const inputEl = document.createElement("input");
              const normalizedValue = fieldType === "date"
                ? normalizeDateInputValue(currentValue)
                : currentValue;
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
  const baseValues = (
    menuProcessValuesMap &&
    menuProcessValuesMap[cleanMenuKey] &&
    typeof menuProcessValuesMap[cleanMenuKey] === "object"
  )
    ? { ...menuProcessValuesMap[cleanMenuKey] }
    : {};
  if (!dynamicProcessEditFormEl) {
    return baseValues;
  }

  const controls = dynamicProcessEditFormEl.querySelectorAll("[name^='process_field__']");
  controls.forEach((controlEl) => {
    const fieldKey = normalizeMenuKey(String(controlEl.getAttribute("name") || "").replace(/^process_field__/, ""));
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
